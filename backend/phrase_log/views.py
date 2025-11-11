from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
from rest_framework.generics import ListAPIView
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import pandas as pd
import io

from .services import get_structured_explanations
from .types import LookupRequestData
from .models import PhraseLog, Tag
from .serializers import PhraseLogSerializer, TagSerializer
from rest_framework.decorators import api_view, permission_classes, action
from django.http import HttpResponse


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_phrases_view(request):
    """
    导出用户短语数据为 Excel 文件。
    接收一个包含要导出的 phrase logs 的 ID 列表的 POST 请求。
    如果未提供 ID，则导出该用户的所有短语。
    """
    user = request.user
    log_ids = request.data.get('ids', None)

    if log_ids:
        queryset = PhraseLog.objects.filter(user=user, pk__in=log_ids)
    else:
        queryset = PhraseLog.objects.filter(user=user)

    # 定义要导出的字段
    data = list(queryset.values(
        'expression_text',
        'chinese_meaning',
        'example_sentence',
        'original_context',
        'created_at',
        'remark'
    ))

    if not data:
        return Response({"error": "没有可导出的数据"}, status=status.HTTP_404_NOT_FOUND)

    # 创建 Pandas DataFrame
    df = pd.DataFrame(data)

    # 【修复】将 'created_at' 列转换为无时区，以兼容 Excel
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_localize(None)

    # 重命名字段以获得更友好的列标题
    df.rename(columns={
        'expression_text': '短语',
        'chinese_meaning': '中文含义',
        'example_sentence': '例句',
        'original_context': '原始上下文',
        'created_at': '创建时间',
        'remark': '备注'
    }, inplace=True)

    # 将 DataFrame 写入内存中的 Excel 文件
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Phrases')
    
    buffer.seek(0)

    # 创建 HTTP 响应
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="phrases_export.xlsx"'

    return response


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
                        remark=item.get('remark'),
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




class HistoryAPIView(ListAPIView): # Inherit from ListAPIView
    """
    处理“获取历史记录”的 GET 请求 (V1.01 功能)。
    """

    # --- 【Task 2】 (保护这个 API) ---
    permission_classes = [IsAuthenticated]
    serializer_class = PhraseLogSerializer # Specify the serializer

    def get_queryset(self):
        """
        This view should return a list of all the phrase logs
        for the currently authenticated user, with optional filtering.
        """
        user = self.request.user
        queryset = PhraseLog.objects.filter(user=user)

        # Get filter parameters from the request URL
        tag_ids_str = self.request.query_params.get('tag', None)
        search_query = self.request.query_params.get('search', None)

        # Apply tag filter if a non-empty tag_ids_str is provided
        if tag_ids_str:
            tag_ids = tag_ids_str.split(',')
            queryset = queryset.filter(tags__id__in=tag_ids)

        # Apply search filter if a non-empty search_query is provided
        if search_query:
            queryset = queryset.filter(
                Q(expression_text__icontains=search_query)
                #   |
                # Q(chinese_meaning__icontains=search_query) |
                # Q(example_sentence__icontains=search_query) |
                # Q(original_context__icontains=search_query) |
                # Q(remark__icontains=search_query)
            )

        # Return the filtered and ordered queryset
        return queryset.order_by('-created_at')


class TagAPIView(APIView):
    """
    处理“获取所有标签”的 GET 请求。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # 只获取当前用户的标签
        tags = Tag.objects.filter(user=request.user).order_by('name')
        serializer = TagSerializer(tags, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PhraseLogDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles Retrieve, Update, and Destroy for a single PhraseLog entry.
    - GET: Retrieve a single log.
    - PUT/PATCH: Update a single log.
    - DELETE: Delete a single log.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PhraseLogSerializer

    def get_queryset(self):
        """
        This view should return a queryset of all the phrase logs
        for the currently authenticated user.
        """
        return PhraseLog.objects.filter(user=self.request.user)

