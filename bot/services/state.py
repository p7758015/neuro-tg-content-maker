# bot/services/state.py

# простое in-memory хранилище: user_id -> style_name
USER_ACTIVE_STYLE: dict[int, str] = {}

def set_user_style(user_id: int, style_name: str) -> None:
    USER_ACTIVE_STYLE[user_id] = style_name

def get_user_style(user_id: int) -> str | None:
    return USER_ACTIVE_STYLE.get(user_id)

# простое in-memory хранилище: user_id -> style_name
USER_ACTIVE_STYLE: dict[int, str] = {}

def set_user_style(user_id: int, style_name: str) -> None:
    USER_ACTIVE_STYLE[user_id] = style_name

def get_user_style(user_id: int) -> str | None:
    return USER_ACTIVE_STYLE.get(user_id)


# кто последний настраивал канал (для /link_channel в канале)
LAST_CONNECT_USER: dict[str, int] = {}  # просто ключ "last" -> telegram_id

def set_last_connect_user(user_id: int) -> None:
    LAST_CONNECT_USER["last"] = user_id

def get_last_connect_user() -> int | None:
    return LAST_CONNECT_USER.get("last")
