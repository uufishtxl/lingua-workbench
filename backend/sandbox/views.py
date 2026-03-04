from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from .models import Author, Book, PSandbox, PTagSandbox
from .serializers import AuthorSerializer, PSandboxSerializer, PTagSandboxSerializer
from rest_framework import permissions, status
from django.utils import timezone

# --- 手感保持练习：重写 Pomodoro 练习 START ----

class PTagSandboxViewSet(ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PTagSandboxSerializer
    queryset = PTagSandbox.objects.all()
    pagination_class = None # 禁用分页（Tag 一般数据少，不需要分页）


class PSandboxViewSet(ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PSandboxSerializer
    pagination_class = None

    # 任务 1 - 覆写 queryset：A) 筛选用户 B) 提供日期时，删除日期
    def get_queryset(self):
        return PSandbox.objects.filter(user=self.request.user).order_by('-created_at')

    # 任务 4 - 重写 perform_create，检查是否有STARTED 的任务，如果有，修改成 INTERRUPTED
    def perform_create(self, serializer):
        existing = PSandbox.objects.filter(user=self.request.user, status=PSandbox.Status.STARTED).first()
        if existing:
            existing.status = PSandbox.Status.INTERRUPTED
            existing.save()
        serializer.save(user=self.request.user)
    
    # 任务 5 - 重写 perform_update，提交 completed_at
    def perform_update(self, serializer): # 这里有了 serializer 这个参数，是什么？
        instance = self.get_object()
        new_status = serializer.validated_data.get('status')

        if (new_status == PSandbox.Status.COMPLETED 
            and not instance.completed_at):
            serializer.save(completed_at = timezone.now())
        else:
            serializer.save()



    # 任务 2 - @action 检查 ongoing 有没有正在进行的专注任务
    @action(detail=False, methods=['get'])
    def ongoing(self, request):
        session = PSandbox.objects.filter(user=request.user, status=PSandbox.Status.STARTED).first()
        if session:
            serializer = self.get_serializer(session)
            return Response(serializer.data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    # 任务 6 - @action，返回最早的日期
    @action(detail=False, methods=['get'])
    def earliest(self, request):
        # 找到最早日期的记录，不使用 get_queryset() 防止受 ?date= 参数污染
        earliest = PSandbox.objects.filter(user=request.user).order_by('created_at').first()
        if earliest:
            return Response({'date': earliest.created_at.strftime('%Y-%m-%d')})
        return Response({'date': None})

    # 任务 3 - @action 按日期获取专注记录
    @action(detail=False, methods=['get'])
    def history(self, request):
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'date not provided'})
        
        records = self.get_queryset().filter(
            created_at__date=date_str, 
            status=PSandbox.Status.COMPLETED
        ).order_by('created_at')
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)




# --- END ---
class AuthorViewSet(ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    # 场景 1: detail=True (必须指定是哪个作者)
    # 目的: "给我列出【这个】作者写的所有书名"
    # URL 范例: POST /api/authors/1/quick_publish/
    @action(detail=True, methods=['post'])
    def quick_publish(self, request, pk=None):
        # 核心区别：因为 detail=True，所以我可以调用 get_object() 拿到 id=1 的作者实例
        author = self.get_object()
        
        # 业务逻辑：给这个作者快速发一本新书
        new_book = Book.objects.create(
            author=author, 
            title=f"{author.name}'s New Book", 
        )
        return Response({'status': f'Book "{new_book.title}" created for {author.name}'})

    # 场景 2: detail=False (不需要 ID，针对整体)
    # 目的: "给我把【所有】作者的年龄清零" (或者获取统计信息)
    # URL 范例: POST /api/authors/reset_all_ages/
    @action(detail=False, methods=['post'])
    def reset_all_ages(self, request):
        # 核心区别：因为 detail=False，我拿不到单个对象，我操作的是 get_queryset()
        count = self.get_queryset().update(age=0)
        
        return Response({'status': f'Reset age for {count} authors'})