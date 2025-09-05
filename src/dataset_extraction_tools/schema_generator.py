"""
Simple schema generator for dataset extraction tools.
Generates Pydantic models from JSON field definitions.
"""

import json
from pathlib import Path
from typing import Type
from pydantic import BaseModel, Field, create_model
from src.dataset_extraction_tools.with_evidence import StringWithEvidence


def generate_schema_from_json(json_path: str, schema_name = None) -> Type[BaseModel]:
    """
    Generate Pydantic model from simple JSON field definitions.
    
    Args:
        json_path: Path to JSON file with field_name: description format
        schema_name: Name for the generated schema class
        
    Returns:
        Dynamically created Pydantic model class
        
    Example JSON format:
        {
          "project_id": "Applicant ID in format 'ORD2000111'. Location: top right",
          "funding_requested": "Total funding amount requested. Location: budget section"
        }
    """
    json_file = Path(json_path)
    
    if not json_file.exists():
        raise FileNotFoundError(f"Schema JSON file not found: {json_path}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        fields_config = json.load(f)
    
    if not isinstance(fields_config, dict):
        raise ValueError("JSON must be a dictionary with field_name: description format")
    
    # Create field definitions - all StringWithEvidence, all required
    field_definitions = {}
    for field_name, description in fields_config.items():
        field_definitions[field_name] = (
            StringWithEvidence, 
            Field(description=description)
        )

    if schema_name is None:
        schema_name = json_file.stem
    
    # Dynamically create the model class
    GeneratedModel = create_model(
        schema_name,
        **field_definitions
    )
    
    # Add config as class attribute
    GeneratedModel.__config__ = type('Config', (), {
        'use_enum_values': True
    })
    
    return GeneratedModel