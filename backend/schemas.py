from pydantic import BaseModel
from typing import List, Optional

class Slide(BaseModel):
    page_title: str
    content: List[str]
    layout_type: str = "bullet_points" # e.g., title_only, bullet_points, two_columns, centered
    image_description: Optional[str] = None

class PPTContent(BaseModel):
    title: str
    theme_color: str = "#E88E2E" # Main brand color
    accent_color: str = "#FFD700" # Complementary color
    slides: List[Slide]

class PPTRequest(BaseModel):
    topic: str
    provider: str = "openai"  # openai, doubao, qwen, gemini
    api_key: Optional[str] = None # Optional override
