import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any

# Use absolute path relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

def _load_history() -> List[Dict[str, Any]]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def _save_history(history: List[Dict[str, Any]]):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_history_item(title: str, content: Any, pptx_filename: str = None, html_filename: str = None):
    history = _load_history()
    new_item = {
        "id": str(uuid.uuid4()),
        "title": title,
        "content": content if isinstance(content, dict) else content.dict(),
        "pptx_filename": pptx_filename,
        "html_filename": html_filename,
        "timestamp": datetime.now().isoformat()
    }
    history.insert(0, new_item) # Newest first
    # Keep only last 50 items
    history = history[:50]
    _save_history(history)
    return new_item

def get_all_history() -> List[Dict[str, Any]]:
    return _load_history()

def delete_history_item(item_id: str):
    history = _load_history()
    new_history = [item for item in history if item["id"] != item_id]
    _save_history(new_history)
    return True
