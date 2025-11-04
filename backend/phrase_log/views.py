from django.http import JsonResponse
from rest_framework.views import APIView # 导入 DRF 的 APIView
from rest_framework.response import Response # 导入 DRF 的 Response
from rest_framework.permissions import IsAuthenticated # 导入权限
from rest_framework import status # 导入 HTTP 状态码
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import ExpressionLookupForm
from .services import get_structured_explanations
from .types import LookupRequestData
from .models import PhraseLog, Tag
from .serializers import PhraseLogSerializer


class PhraseLookupAPIView(APIView):
    """
    处理“查询短语”的 POST 请求 (V1 功能)。
    """

    # --- 【Task 2】 ---
    # 这一行代码，就“保护”了这个 API。
    # 只有提供了有效 JWT Token 的请求才能进入。
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        # 'request.user' 现在保证是“已登录用户”
        # 'request.data' 是 DRF 自动解析后的 JSON

        try:
            data = request.data
            lookup_data: LookupRequestData = {
                "original_context": data.get('original_context'),
                "expressions_to_lookup": data.get('expressions_to_lookup', ''),
                "remark": data.get('remark', None),
                "tags": data.get("tags", None)
            }

            results_ai = get_structured_explanations(lookup_data)

            if results_ai:
                # --- 【Task 3】 (创建时关联 user) ---
                for item in results_ai:
                    phrase_log = PhraseLog.objects.create(
                        user=request.user, # <-- 关联当前登录的用户
                        original_context=item.get('original_context'),
                        expression_text=item.get('expression_text'),
                        chinese_meaning=item.get('chinese_meaning'),
                        example_sentence=item.get('example_sentence'),
                        remark=item.get('remark')
                    )
                    # Handle tags
                    if lookup_data.get('tags'):
                        for tag_name in lookup_data['tags']:
                            tag, created = Tag.objects.get_or_create(name=tag_name, user=request.user)
                            phrase_log.tags.add(tag)

                # 返回“创建成功”和数据
                return Response(results_ai, status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "AI service failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HistoryAPIView(APIView):
    """
    处理“获取历史记录”的 GET 请求 (V1.01 功能)。
    """

    # --- 【Task 2】 (保护这个 API) ---
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # --- 【Task 3】 (只获取*自己的*数据) ---
        logs = PhraseLog.objects.filter(user=request.user).order_by('-created_at')

        # 使用“翻译官”把数据转换成 JSON
        serializer = PhraseLogSerializer(logs, many=True)

        # 返回“OK”和数据
        return Response(serializer.data, status=status.HTTP_200_OK)