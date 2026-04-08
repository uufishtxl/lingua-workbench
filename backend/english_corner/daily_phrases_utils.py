"""
Shared utilities for Daily Phrases feature.
DRY encapsulation of bonus word selection logic,
reused by /init/ and /refresh-bonus/ endpoints.
"""
from .models import WordNode


def get_random_bonus_words(user, exclude_ids: list, count: int = 3) -> list[dict]:
    """
    Randomly fetch `count` words from user's box_level=1 pool,
    excluding all IDs in `exclude_ids` (session word IDs).

    Returns: [{"id": int, "word": str}, ...]
    """
    nodes = (
        WordNode.objects
        .filter(user=user, box_level=1)
        .exclude(id__in=exclude_ids)
        .order_by('?')[:count]
        .values('id', 'label')
    )
    return [{"id": n['id'], "word": n['label']} for n in nodes]
