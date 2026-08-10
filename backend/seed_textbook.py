"""
种子脚本：把 backend/english_book_5a.pdf 注册为第一条 Textbook。

用法（Windows venv，backend/ 目录下）：
    python seed_textbook.py
"""
import os
import shutil

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample_project.settings')
django.setup()

from django.conf import settings

from corpus.models import Textbook

SRC_PDF = os.path.join(os.path.dirname(__file__), 'english_book_5a.pdf')


def seed_textbook():
    if not os.path.exists(SRC_PDF):
        print(f"[跳过] 找不到源文件: {SRC_PDF}")
        return

    # 拷贝到 media/textbooks/（保留原文件）；若目标已存在但大小不一致（如被测试伪造文件污染），强制覆盖
    dest_dir = os.path.join(settings.MEDIA_ROOT, 'textbooks')
    os.makedirs(dest_dir, exist_ok=True)
    dest_name = 'english_book_5a.pdf'
    dest_path = os.path.join(dest_dir, dest_name)
    src_size = os.path.getsize(SRC_PDF)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) == src_size:
        print(f"[已存在且大小一致] {dest_path}")
    else:
        shutil.copy(SRC_PDF, dest_path)
        print(f"[拷贝] {SRC_PDF} -> {dest_path}（{src_size} 字节）")

    obj, created = Textbook.objects.get_or_create(
        name='5A新版五上',
        defaults={
            'grade': '五年级',
            'semester': '上册',
            'pdf_file': f'textbooks/{dest_name}',
        },
    )
    if created:
        print(f"[创建] Textbook: {obj}")
    else:
        print(f"[已存在] Textbook: {obj}")


if __name__ == '__main__':
    seed_textbook()
