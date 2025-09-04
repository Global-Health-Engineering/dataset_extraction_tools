"""
Pydantic models for dataset_extraction_tools with evidence tracking.
Defines all data structures for extraction with evidence and confidence scoring.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import date


class WithEvidence(BaseModel):
    """Base model for extracted fields with evidence tracking"""
    value: Any = Field(..., description="The extracted value")
    evidence: str = Field(..., description="Exact quote from document supporting this value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class StringWithEvidence(WithEvidence):
    """String field with evidence"""
    value: Optional[str] = None


class IntWithEvidence(WithEvidence):
    """Integer field with evidence"""
    value: Optional[int] = None


class FloatWithEvidence(WithEvidence):
    """Float field with evidence"""
    value: Optional[float] = None


class DateWithEvidence(WithEvidence):
    """Date field with evidence"""
    value: Optional[date] = None


class EnumWithEvidence(WithEvidence):
    """Enum field with evidence"""
    value: Optional[str] = None