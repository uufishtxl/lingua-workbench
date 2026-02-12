from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Author, Book
from .serializers import AuthorSerializer # 假设你已经有了这个

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