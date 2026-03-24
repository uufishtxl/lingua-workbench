import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sample_project.settings')
django.setup()

from english_corner.models import Scenario

def seed_scenarios():
    scenarios = [
        {
            "title": "Starbucks Ordering",
            "description": "A busy Starbucks in downtown Seattle. Smells of roasted beans and steam.",
            "icon": "☕",
            "vibe": "Busy, Urban, Friendly",
            "is_preset": True,
            "system_prompt": "You are a friendly but busy Starbucks barista. Your name is Alex. You speak natural, conversational English. Sometimes the espresso machine makes noise in the background. Keep your responses short and emphasize efficiency."
        },
        {
            "title": "Job Interview (UI Designer)",
            "description": "A sleek, high-tech office in Silicon Valley. Glass walls and minimalist furniture.",
            "icon": "🎨",
            "vibe": "Professional, Intellectual, Serious",
            "is_preset": True,
            "system_prompt": "You are Sarah, a Lead Product Designer at a top tech company. You are interviewing the user for a Senior UI Designer role. You ask insightful questions about design systems, user empathy, and tool proficiency. You are polite but rigorous."
        },
        {
            "title": "Hiking in the Swiss Alps",
            "description": "A sunny trail near Zermatt. Breathtaking views of the Matterhorn.",
            "icon": "🏔️",
            "vibe": "Adventurous, Relaxed, Nature-loving",
            "is_preset": True,
            "system_prompt": "You are a fellow hiker named Thomas. You met the user on the trail. You are enthusiastic about nature and enjoy sharing tips about the best viewing spots. You speak with a slight European flair but perfect English."
        }
    ]

    for data in scenarios:
        Scenario.objects.update_or_create(
            title=data['title'],
            defaults=data
        )
        print(f"Seeded scenario: {data['title']}")

if __name__ == '__main__':
    seed_scenarios()
