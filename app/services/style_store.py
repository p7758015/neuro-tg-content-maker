# app/services/style_store.py
import json
from pathlib import Path
from typing import Dict, List

STYLES_DIR = Path("styles")
STYLES_DIR.mkdir(exist_ok=True)

def style_path(name: str) -> Path:
    safe_name = name.replace("/", "_").replace("@", "").strip()
    return STYLES_DIR / f"{safe_name}.json"

def save_style(name: str, style: Dict) -> None:
    path = style_path(name)
    with path.open("w", encoding="utf-8") as f:
        json.dump(style, f, ensure_ascii=False, indent=2)

def load_style(name: str) -> Dict | None:
    path = style_path(name)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def list_styles() -> List[str]:
    return [p.stem for p in STYLES_DIR.glob("*.json")]

def delete_style(name: str) -> bool:
    path = style_path(name)
    if not path.exists():
        return False
    path.unlink()
    return True

def rename_style(old_name: str, new_name: str) -> bool:
    old_path = style_path(old_name)
    new_path = style_path(new_name)
    if not old_path.exists():
        return False
    if new_path.exists():
        # не перезаписываем существующий
        return False
    old_path.rename(new_path)
    return True

def suggest_style_name_from_username(username: str) -> str:
    return username.replace("@", "").strip()


