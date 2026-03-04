from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import PomodoroTag, Pomodoro
from .serializers import PomodoroTagSerializer, PomodoroSerializer

class PomodoroTagViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PomodoroTagSerializer
    queryset = PomodoroTag.objects.all()
    pagination_class = None

class PomodoroViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PomodoroSerializer
    pagination_class = None

    def get_queryset(self):
        return Pomodoro.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        existing = Pomodoro.objects.filter(
            user=self.request.user,
            status=Pomodoro.Status.STARTED
        ).first()
        if existing:
            existing.status = Pomodoro.Status.INTERRUPTED
            existing.save()

        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        instance = self.get_object()
        new_status = serializer.validated_data.get('status')

        if (new_status == Pomodoro.Status.COMPLETED 
                and not instance.completed_at):
            serializer.save(completed_at=timezone.now())
        else:
            serializer.save()

    @action(detail=False, methods=['get'])
    def ongoing(self, request):
        """GET /api/pomodoros/ongoing/ — 检查进行中的会话"""
        session = Pomodoro.objects.filter(
            user=request.user,
            status=Pomodoro.Status.STARTED
        ).first()

        if session:
            serializer = self.get_serializer(session)
            return Response(serializer.data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def earliest(self, request):
        """GET /api/pomodoros/earliest/ — 返回最早记录的日期（日历边界）"""
        first = Pomodoro.objects.filter(user=request.user).order_by('created_at').first()
        if first:
            return Response({'date': first.created_at.strftime('%Y-%m-%d')})
        return Response({'date': None})

    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        GET /api/pomodoros/history/?date=2026-02-27
        返回某天的专注记录，按 created_at 升序排列
        """
        date_str = request.query_params.get('date')
        if not date_str:
            return Response({'error': 'date parameter is required'}, status=400)

        records = self.get_queryset().filter(
            created_at__date=date_str,
            status=Pomodoro.Status.COMPLETED
        ).order_by('created_at')

        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)
