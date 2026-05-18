"""Pydantic schemas for validating pipeline YAML configurations."""

from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, Field


class PromptPhaseSchema(BaseModel):
    """Schema for a phase prompt definition in the constitution."""
    role: str
    content: str


class PhaseConfigSchema(BaseModel):
    """Schema for a phase configuration in the constitution."""
    agent_name: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    prompts: List[PromptPhaseSchema] = Field(default_factory=list)


class ConstitutionSchema(BaseModel):
    """Schema for the AutoHarness constitution.yaml file."""
    model_config = ConfigDict(extra="allow")
    
    phases: Optional[Dict[str, PhaseConfigSchema]] = None
    global_rules: Optional[List[str]] = None
    version: Optional[str] = None


class ProjectConfigSchema(BaseModel):
    """Schema for project-specific configurations."""
    model_config = ConfigDict(extra="allow")

    name: str
    description: Optional[str] = None
    dependencies: Optional[List[str]] = Field(default_factory=list)


def get_schema_for_type(schema_type: str) -> Optional[Type[BaseModel]]:
    """Get the Pydantic schema class for a given schema type name."""
    schemas = {
        "constitution": ConstitutionSchema,
        "project": ProjectConfigSchema,
    }
    return schemas.get(schema_type.lower())
