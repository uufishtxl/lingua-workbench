import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample_project.settings')
django.setup()

from pomodoro.models import PomodoroTag

tags = [
    ('沉浸美剧', 1),
    ('全栈知识', 2),
    ('氛围编程', 3),
    ('心流编程', 4),
    ('外刊阅读', 5),
    ('哲学思辨', 6)
]

for name, order in tags:
    obj, created = PomodoroTag.objects.get_or_create(name=name, defaults={'order': order})
    if created:
        print(f"Created: {name}")
    else:
        print(f"Already exists: {name}")
