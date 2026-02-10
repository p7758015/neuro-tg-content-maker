# bot/services/state.py

# простое in-memory хранилище: user_id -> style_name
USER_ACTIVE_STYLE: dict[int, str] = {}

def set_user_style(user_id: int, style_name: str) -> None:
    USER_ACTIVE_STYLE[user_id] = style_name

def get_user_style(user_id: int) -> str | None:
    return USER_ACTIVE_STYLE.get(user_id)
