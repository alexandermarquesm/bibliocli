
from typing import List, Optional
from pydantic import BaseModel

class Chapter(BaseModel):
    title: str
    paragraphs: List[str]
    is_narrative: bool = True
    index: Optional[int] = None
    
class FormattedBook(BaseModel):
    title: str
    author: str
    chapters: List[Chapter]
    suggested_start: Optional[dict] = None
    source_url: Optional[str] = None
    updated_at: Optional[str] = None
