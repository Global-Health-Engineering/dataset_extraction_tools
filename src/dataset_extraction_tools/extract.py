"""
Simplified structured data extraction using Instructor with evidence tracking.
Combines evidence models and extraction logic in a single focused module.
"""

import json
from pathlib import Path
from typing import Union, Optional, TypeVar, Type, List, Any
from datetime import date
from pydantic import BaseModel, Field, create_model
from .utils import timing

try:
    import instructor
    from pydantic import BaseModel, Field
except ImportError:
    raise ImportError("Install dependencies: pip install instructor pydantic")

T = TypeVar('T', bound=BaseModel)


# Evidence tracking models
class WithEvidence(BaseModel):
    """Base model for extracted fields with evidence tracking"""
    value: Any = Field(..., description="The extracted value")
    evidence: str = Field(..., description="Exact quote from document supporting this value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    
    class Config:
        json_encoders = {date: lambda v: v.isoformat()}


class StringWithEvidence(WithEvidence):
    value: Optional[str] = None


class IntWithEvidence(WithEvidence):
    value: Optional[int] = None


class FloatWithEvidence(WithEvidence):
    value: Optional[float] = None


class DateWithEvidence(WithEvidence):
    value: Optional[date] = None


class EnumWithEvidence(WithEvidence):
    value: Optional[str] = None

def create_simple_schema(response_model: Type[T]) -> Type[BaseModel]:
    """
    Create a simplified version of schema without evidence tracking.
    Converts WithEvidence fields to their simple counterparts.
    """
    field_definitions = {}

    for field_name, field_info in response_model.__annotations__.items():
        if hasattr(response_model, '__fields__'):
            field_desc = response_model.__fields__[field_name].field_info.description

            # Convert evidence types to simple types
            if field_info == StringWithEvidence:
                field_definitions[field_name] = (Optional[str], Field(description=field_desc))
            elif field_info == IntWithEvidence:
                field_definitions[field_name] = (Optional[int], Field(description=field_desc))
            elif field_info == FloatWithEvidence:
                field_definitions[field_name] = (Optional[float], Field(description=field_desc))
            elif field_info == DateWithEvidence:
                field_definitions[field_name] = (Optional[date], Field(description=field_desc))
            else:
                # Keep other types as-is
                field_definitions[field_name] = (field_info, Field(description=field_desc))

    # Create simplified model
    SimpleModel = create_model(
        f"{response_model.__name__}_Simple",
        **field_definitions
    )

    return SimpleModel


def generate_extraction_prompt(schema: Type[BaseModel], use_evidence: bool = True) -> str:
    """Generate extraction prompt from schema field descriptions."""
    fields_desc = []
    for field_name, field_info in schema.__annotations__.items():
        if hasattr(schema, '__fields__'):
            field_desc = schema.__fields__[field_name].field_info.description
            fields_desc.append(f"- {field_name}: {field_desc}")

    base_prompt = f"""Extract the following information from this document:

{chr(10).join(fields_desc)}

CRITICAL REQUIREMENTS:
- Extract ONLY text that appears verbatim in the document
- Do not infer, estimate, or add any information not explicitly stated"""

    if use_evidence:
        base_prompt += """
- Provide exact quotes as evidence for each field
- Include confidence score between 0.0 and 1.0
- Use confidence 0.0 if information is not found"""
    else:
        base_prompt += """
- Return null/empty for fields not found in the document"""

    return base_prompt


def schema_from_json(json_path: str, schema_name = None) -> Type[BaseModel]:
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


# Core extraction functions
def extract_from_text(
    text: str,
    response_model: Type[T],
    provider: str = "ollama/llama3.2",
    api_key: Optional[str] = None,
    custom_prompt: Optional[str] = None
) -> T:
    """Extract structured data from text using instructor with evidence tracking."""
    client = instructor.from_provider(provider, **({} if api_key is None else {"api_key": api_key}))

    if custom_prompt:
        prompt = f"{custom_prompt}\n\n{text}"
    else:
        prompt = (
            f"Extract structured data from this document. "
            f"For each field, provide exact quoted evidence and confidence 0-1.\n\n{text}"
        )

    return client.chat.completions.create(
        response_model=response_model,
        messages=[{"role": "user", "content": prompt}],
        max_retries=2
    )


@timing
def extract_from_file(
    file_path: Union[str, Path],
    response_model: Type[T],
    provider: str = "ollama/llama3.2",
    api_key: Optional[str] = None,
    save_json: bool = True,
    custom_prompt: Optional[str] = None
) -> T:
    """Extract structured data from a single markdown file."""
    file_path = Path(file_path)
    text = file_path.read_text(encoding='utf-8')

    result = extract_from_text(text, response_model, provider, api_key, custom_prompt)

    if save_json:
        json_path = file_path.with_suffix('.json')
        _save_result(result, json_path)

    return result


def extract_from_files(
    file_paths: List[Union[str, Path]],
    response_model: Type[T],
    provider: str = "ollama/llama3.2",
    api_key: Optional[str] = None,
    save_json: bool = True
) -> T:
    """Extract structured data from multiple files in a single LLM call."""
    if not file_paths:
        raise ValueError("No files provided")
    
    # Combine all file contents
    combined_content = []
    valid_paths = []
    
    for i, file_path in enumerate(file_paths):
        file_path = Path(file_path)
        if file_path.exists():
            text = file_path.read_text(encoding='utf-8')
            combined_content.append(f"=== DOCUMENT {i+1}: {file_path.name} ===\n{text}")
            valid_paths.append(file_path)
    
    if not combined_content:
        raise FileNotFoundError("No valid files found")
    
    # Single LLM call with combined content
    full_content = "\n\n".join(combined_content)
    result = extract_from_text(full_content, response_model, provider, api_key)
    
    # Save to first file's directory
    if save_json and valid_paths:
        json_path = valid_paths[0].with_suffix('.json')
        _save_result(result, json_path)
    
    return result


def _save_result(result: BaseModel, json_path: Path):
    """Save extraction result to JSON with evidence tracking when available."""
    data = {}

    for field_name, field_value in result.__dict__.items():
        # Handle WithEvidence types (legacy)
        if field_value and hasattr(field_value, 'value') and field_value.value is not None:
            data[field_name] = {
                'value': field_value.value,
                'evidence': field_value.evidence,
                'confidence': field_value.confidence
            }
        # Handle simple types (string, int, float, lists, etc.)
        elif field_value is not None:
            data[field_name] = field_value

    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding='utf-8')