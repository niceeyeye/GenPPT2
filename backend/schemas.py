from pydantic import BaseModel
from typing import List, Optional

class SlideItem(BaseModel):
    title: str
    description: str

class Slide(BaseModel):
    page_title: str
    subtitle: Optional[str] = None
    content: List[SlideItem] # 升级为结构化数据
    layout_type: str = "cards" # e.g., title_only, cards, two_columns, timeline
    image_description: Optional[str] = None

class PPTContent(BaseModel):
    title: str
    subtitle: Optional[str] = None
    theme_color: str = "#4F46E5" # 默认现代紫
    accent_color: str = "#06B6D4" # 默认亮青色
    bg_style: str = "gradient" # gradient, solid, mesh
    slides: List[Slide]

class PPTRequest(BaseModel):
    topic: str
    provider: str = "openai"  # openai, doubao, qwen, gemini
    api_key: Optional[str] = None # Optional override

class ModifyOutlineRequest(BaseModel):
    content: PPTContent
    instruction: str
    provider: str = "openai"
    api_key: Optional[str] = None
