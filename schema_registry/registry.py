from typing import Dict, Type, Any, Optional
from pydantic import BaseModel

from .context import SchemaContext

class SchemaRegistry:
    """Registry for maintaining schema consistency"""
    _schemas: Dict[str, Type[BaseModel]] = {}
    
    @classmethod
    def register(cls, name: str, schema: Type[BaseModel]):
        """Register a schema with the registry"""
        cls._schemas[name] = schema
        
    @classmethod
    def get(cls, name: str) -> Type[BaseModel]:
        """Get a schema by name"""
        if name not in cls._schemas:
            raise ValueError(f"Schema '{name}' not registered")
        return cls._schemas[name]
        
    @classmethod
    def list_schemas(cls) -> Dict[str, Type[BaseModel]]:
        """List all registered schemas"""
        return cls._schemas
        
    @classmethod
    def create_context(cls, context_id: str = "schema_validation") -> SchemaContext:
        """Create a validation context"""
        return SchemaContext(schema_registry=cls, context_id=context_id)