pending_edit: dict[int, bool] = {}
pending_write: dict[int, bool] = {}
pending_trends: dict[int, str] = {}   # user_id -> "niche" | "topic"
post_cache: dict[str, str] = {}
trends_cache: dict[str, list[str]] = {}  # uuid8 -> [trend1, trend2, trend3]
