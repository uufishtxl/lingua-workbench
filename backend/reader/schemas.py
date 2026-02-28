from pydantic import BaseModel, Field

from typing import List

class OutlineItem(BaseModel):
    title: str = Field(description="Title of the outline segment")
    start_index: int = Field(description="The starting paragraph index for this segment")
    end_index: int = Field(description="The ending paragraph index for this segment")

class ArticleMetaResponse(BaseModel):
    domain: str = Field(description="The primary domain or industry of the article (e.g., 'Finance', 'Tech', 'History', 'General')")
    summary: str = Field(description="A concise 2-sentence summary of the article's core argument or topic")
    difficulty: str = Field(description="Estimated reading difficulty: 'Beginner', 'Intermediate', or 'Advanced'")
    outline: List[OutlineItem] = Field(description="A mandatory 3-8 point chronological outline of the article's structure", default_factory=list)

class CopilotResponse(BaseModel):
    content: str = Field(description="HTML formatted response containing the explanation and examples.")

class AnnotationContext(BaseModel):
    domain: str = "General"
    paragraph: str
    selected_text: str
    annotation_type: str
    user_note: str = ""
