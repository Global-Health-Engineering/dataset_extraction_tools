"""
Pydantic models for ethord project using dataset_extraction_tools.
Defines all data structures for extraction with evidence tracking.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from src.core.with_evidence import StringWithEvidence, IntWithEvidence, FloatWithEvidence, DateWithEvidence, EnumWithEvidence

class Ethord(BaseModel):
    """
    Extraction model for ethord documents.
    Contains required fields using WithEvidence.
    """
    
    # Project identification
    project_id: Optional[StringWithEvidence] = Field(
        None, 
        description="Unique project identifier or reference number"
    )
    
    call_category: Optional[EnumWithEvidence] = Field(
        None,
        description="Category of the funding call (research, innovation, etc.)"
    )
    
    # Applicant information
    applicant_id: Optional[StringWithEvidence] = Field(
        None,
        description="Unique identifier for the main applicant"
    )
    
    main_applicant_institution_name: Optional[StringWithEvidence] = Field(
        None,
        description="Name of the main applicant's institution"
    )
    
    applicant_type: Optional[EnumWithEvidence] = Field(
        None,
        description="Type of applicant (individual, institution, consortium, etc.)"
    )
    
    applicant_title: Optional[StringWithEvidence] = Field(
        None,
        description="Academic or professional title of the applicant (Dr., Prof., etc.)"
    )
    
    applicant_first_name: Optional[StringWithEvidence] = Field(
        None,
        description="First name of the main applicant"
    )
    
    applicant_last_name: Optional[StringWithEvidence] = Field(
        None,
        description="Last name of the main applicant"
    )
    
    applicant_institution: Optional[StringWithEvidence] = Field(
        None,
        description="Institution name where applicant is affiliated"
    )
    
    applicant_department_name: Optional[StringWithEvidence] = Field(
        None,
        description="Department or faculty name within the institution"
    )
    
    applicant_lab_name: Optional[StringWithEvidence] = Field(
        None,
        description="Laboratory or research group name"
    )
    
    applicant_orcid_id: Optional[StringWithEvidence] = Field(
        None,
        description="ORCID identifier of the applicant"
    )
    
    # Project details
    title: Optional[StringWithEvidence] = Field(
        None,
        description="Full title of the research project"
    )
    
    acronym: Optional[StringWithEvidence] = Field(
        None,
        description="Project acronym or short name"
    )
    
    abstract: Optional[StringWithEvidence] = Field(
        None,
        description="Project abstract or summary"
    )
    
    keywords: Optional[StringWithEvidence] = Field(
        None,
        description="Keywords or tags associated with the project"
    )
    
    # Project timeline and funding
    project_duration_months: Optional[IntWithEvidence] = Field(
        None,
        description="Duration of the project in months"
    )
    
    funding_requested: Optional[FloatWithEvidence] = Field(
        None,
        description="Total funding amount requested"
    )
    
    project_start_yyyy_mm_dd: Optional[DateWithEvidence] = Field(
        None,
        description="Project start date in YYYY-MM-DD format"
    )
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }


class ExtractionResult(BaseModel):
    """Container for extraction results with metadata"""
    
    # Quality metrics
    overall_confidence: Optional[float] = Field(None, description="Average confidence across all fields")
    fields_extracted: int = Field(None, description="Number of fields successfully extracted")
    total_fields: int = Field(None, description="Total number of possible fields")
    
    # Validation flags
    needs_review: bool = Field(False, description="True if any field has confidence < 0.8")
    validation_errors: list[str] = Field(default_factory=list, description="List of validation errors")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            date: lambda v: v.isoformat()
        }