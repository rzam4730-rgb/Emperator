"""Canonical order status transitions shared by POS, KDS and inventory."""
STATUSES = ["جدید", "در حال آماده‌سازی", "آماده", "تحویل‌شده", "لغوشده"]
TRANSITIONS = {
    "جدید": {"در حال آماده‌سازی", "لغوشده"},
    "در حال آماده‌سازی": {"آماده", "لغوشده"},
    "آماده": {"تحویل‌شده"},
    "تحویل‌شده": set(),
    "لغوشده": set(),
}

def is_allowed(old: str, new: str) -> bool:
    return new == old or new in TRANSITIONS.get(old, set())
