from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TaskType(str, Enum):
    dialect_normalization = "dialect_normalization"
    dialect_generation = "dialect_generation"
    translation_en = "translation_en"
    translation_ar = "translation_ar"
    chat = "chat"
    transliteration = "transliteration"
    classification = "classification"


class ReviewStatus(str, Enum):
    raw = "raw"
    needs_review = "needs_review"
    approved = "approved"
    rejected = "rejected"


class TrainingRecordCreate(BaseModel):
    task_type: TaskType
    input_text: str = Field(..., min_length=1, max_length=5000)
    output_text: Optional[str] = Field(None, max_length=5000)
    dialect: str = Field(default="Kannur / North Malabar")
    source_type: str = Field(default="manual")
    script: str = Field(default="unknown")
    sub_region: Optional[str] = None
    tone: Optional[str] = None
    domain: Optional[str] = None
    speaker_age_group: Optional[str] = None
    notes: Optional[str] = None


class TrainingRecord(TrainingRecordCreate):
    id: int
    status: ReviewStatus
    quality_score: float
    validation_errors: list[str]
    duplicate_key: str
    created_at: str
    updated_at: str


class ReviewUpdate(BaseModel):
    status: ReviewStatus
    reviewer: Optional[str] = None
    notes: Optional[str] = None
    corrected_output_text: Optional[str] = None
