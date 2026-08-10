from pathlib import Path

from django.shortcuts import get_object_or_404
from rest_framework import parsers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CorpusTask, Textbook
from .llm import fix_module_with_llm, regenerate_kp_with_llm
from .serializers import CorpusTaskSerializer, TextbookSerializer
from .services import sync_tts_to_audio_slicer
from .tasks import extract_unit_task, generate_tts_task, llm_bucket_task


class TextbookViewSet(viewsets.ModelViewSet):
    """
    教材管理：上传 PDF、列表、详情。

    设计共识 §1.1：Textbook 全局共享，不做用户隔离（个人项目）。
    """
    queryset = Textbook.objects.all()
    serializer_class = TextbookSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]

    def create(self, request, *args, **kwargs):
        """上传教材：name 缺省时从文件名推导（去 .pdf 后缀）。"""
        data = request.data.copy()
        if not data.get('name'):
            pdf = data.get('pdf_file')
            if pdf is not None:
                data['name'] = Path(pdf.name).stem
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class CorpusTaskViewSet(viewsets.ModelViewSet):
    """
    语料加工任务：创建（textbook + unit → 触发 extract_unit 任务）、列表、详情（轮询状态）。
    """
    queryset = CorpusTask.objects.all()
    serializer_class = CorpusTaskSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save()
        # 直接调用 = 入队（huey immediate=False 时 __call__ 入队，worker 异步执行）
        extract_unit_task(task.id)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """保存（#28）：编辑已完成任务 → 自动退回 proofreading。"""
        task = self.get_object()
        if task.status == CorpusTask.Status.COMPLETED:
            task.status = CorpusTask.Status.PROOFREADING
            task.save(update_fields=['status', 'updated_at'])
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """仪表盘统计（#25）：总任务/已完成/进行中/覆盖单元数。"""
        tasks = CorpusTask.objects.all()
        total = tasks.count()
        completed = tasks.filter(status=CorpusTask.Status.COMPLETED).count()
        units = tasks.values('textbook_id', 'unit').distinct().count()
        return Response({
            'total': total,
            'completed': completed,
            'in_progress': total - completed,
            'units_covered': units,
        })

    @action(detail=True, methods=['get'], url_path='modules')
    def modules(self, request, pk=None):
        """Stage 2 脏预览数据（#26）：6 模块粗分桶全文。"""
        task = self.get_object()
        return Response(task.cleaned_modules or {})

    @action(detail=True, methods=['post'], url_path='bucket')
    def bucket(self, request, pk=None):
        """进入校准（#27）：触发 DeepSeek 归整 6 模块（幂等，重复触发=重新归整）。"""
        task = self.get_object()
        llm_bucket_task(task.id)
        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'], url_path='tts-data')
    def tts_data(self, request, pk=None):
        """学习页跟读数据（#34）：音频 URL + 按模块组织的句子时间戳。"""
        task = self.get_object()
        if task.tts_status != CorpusTask.TaskStatus.DONE or not task.tts_audio_url:
            return Response({"error": "该任务还没有学习音频（需完成校订后生成 TTS）"},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({
            "tts_audio_url": task.tts_audio_url,
            "tts_timestamps": task.tts_timestamps or {},
        })

    @action(detail=True, methods=['post'], url_path='tts-sync-slicer')
    def tts_sync_slicer(self, request, pk=None):
        """手动把学习音频 + 句子切片同步到 audio_slicer（English Book S1E{unit}）。"""
        task = self.get_object()
        ok = sync_tts_to_audio_slicer(task)
        if not ok:
            return Response({"error": "同步失败：任务缺少音频/时间戳，或音频文件不存在"},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({"ok": True, "detail": f"已同步到 English Book (Grade 5) S1E{task.unit}"})

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """完成校订（#28）：status → completed（终态标记，之后编辑自动退回 proofreading）。"""
        task = self.get_object()
        task.status = CorpusTask.Status.COMPLETED
        task.save(update_fields=['status', 'updated_at'])
        # completed 后自动触发学习音频生成（#33，TTS 只依赖 cleaned_modules）
        generate_tts_task(task.id)
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    # ---- S7 AI 修复 / 重新生成（#29）：生成预览（不落盘）→ 前端 diff 确认 → 应用写库 ----

    @action(detail=True, methods=['post'], url_path='fix-module')
    def fix_module(self, request, pk=None):
        """左栏模块级 AI 修复：生成新模块预览（不落盘）。"""
        from .tasks import _module_to_text

        task = self.get_object()
        module_key = request.data.get('module_key')
        instruction = request.data.get('instruction', '')
        mods = task.cleaned_modules or {}
        if module_key not in mods:
            return Response({"error": f"未知模块: {module_key}"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            module_text = (_module_to_text(mods.get(module_key)) or "")[:12000]
            new_content = fix_module_with_llm(module_key, module_text, instruction, task.unit)
        except Exception as exc:  # noqa: BLE001
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"module_key": module_key, "old_content": mods.get(module_key), "new_content": new_content})

    @action(detail=True, methods=['post'], url_path='apply-module')
    def apply_module(self, request, pk=None):
        """应用确认后的模块修复（写回 cleaned_modules 对应槽位，不连锁重算 KP）。"""
        task = self.get_object()
        module_key = request.data.get('module_key')
        content = request.data.get('content')
        mods = dict(task.cleaned_modules or {})
        if module_key not in mods:
            return Response({"error": f"未知模块: {module_key}"}, status=status.HTTP_400_BAD_REQUEST)
        mods[module_key] = content
        task.cleaned_modules = mods
        task.save(update_fields=['cleaned_modules', 'updated_at'])
        return Response(self.get_serializer(task).data)

    @action(detail=True, methods=['post'], url_path='regenerate-kp')
    def regenerate_kp(self, request, pk=None):
        """右栏 KP 级 AI 重新生成：生成新板块预览（不落盘）。"""
        task = self.get_object()
        kp_key = request.data.get('kp_key')
        instruction = request.data.get('instruction', '')
        kp = task.knowledge_points or {}
        if kp_key not in kp:
            return Response({"error": f"未知知识点: {kp_key}"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            new_content = regenerate_kp_with_llm(kp_key, kp.get(kp_key, ''), instruction, task.cleaned_modules or {})
        except Exception as exc:  # noqa: BLE001
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"kp_key": kp_key, "old_content": kp.get(kp_key, ''), "new_content": new_content})

    @action(detail=True, methods=['post'], url_path='apply-kp')
    def apply_kp(self, request, pk=None):
        """应用确认后的 KP 重新生成（写回 knowledge_points 对应板块）。"""
        task = self.get_object()
        kp_key = request.data.get('kp_key')
        content = request.data.get('content', '')
        kp = dict(task.knowledge_points or {})
        if kp_key not in kp:
            return Response({"error": f"未知知识点: {kp_key}"}, status=status.HTTP_400_BAD_REQUEST)
        kp[kp_key] = content
        task.knowledge_points = kp
        task.save(update_fields=['knowledge_points', 'updated_at'])
        return Response(self.get_serializer(task).data)

    def destroy(self, request, *args, **kwargs):
        """删除任务（#25）：后续切片在此级联清理媒体产物（TTS/PDF）。"""
        return super().destroy(request, *args, **kwargs)


class TtsSlicesUpdateView(APIView):
    """音频切片表保存：接收编辑后的 tts_timestamps（整个音频一个 chunk，句子为 slices）。"""

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        task = get_object_or_404(CorpusTask, id=pk)
        data = request.data.get("tts_timestamps")
        if not isinstance(data, dict):
            return Response({"error": "tts_timestamps 必须为对象（模块 → 句子列表）"}, status=400)
        cleaned = {}
        for mod, sents in data.items():
            if not isinstance(sents, list):
                return Response({"error": f"「{mod}」必须为列表"}, status=400)
            rows = []
            for it in sents:
                if not isinstance(it, dict):
                    return Response({"error": f"「{mod}」行必须为对象"}, status=400)
                start, end = it.get("start"), it.get("end")
                for name, val in (("start", start), ("end", end)):
                    if val is not None and not isinstance(val, (int, float)):
                        return Response({"error": f"「{mod}」{name} 必须为数字"}, status=400)
                rows.append({
                    "text": str(it.get("text", "")),
                    "start": round(float(start), 2) if start is not None else None,
                    "end": round(float(end), 2) if end is not None else None,
                })
            cleaned[mod] = rows
        task.tts_timestamps = cleaned
        task.save(update_fields=["tts_timestamps"])
        return Response({"ok": True, "tts_timestamps": cleaned})
