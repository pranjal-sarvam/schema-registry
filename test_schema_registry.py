import pytest
from pydantic import BaseModel, ValidationError
from sarvam_app_analytics_service.schema_registry import (
    SchemaRegistry, 
    SchemaContext,
    LoggingListener,
    MetricsListener
)

# Define test schemas
class UserSchema(BaseModel):
    username: str
    email: str
    age: int

class ProductSchema(BaseModel):
    id: str
    name: str
    price: float

# Test suite for SchemaRegistry
class TestSchemaRegistry:
    
    def test_register_and_get_schema(self):
        """Test registering schemas and retrieving them."""
        # Clear registry for test
        SchemaRegistry._schemas = {}
        
        # Register schemas
        SchemaRegistry.register("user", UserSchema)
        SchemaRegistry.register("product", ProductSchema)
        
        # Verify schemas are retrievable
        assert SchemaRegistry.get("user") == UserSchema
        assert SchemaRegistry.get("product") == ProductSchema
        
        # Verify listing schemas
        schemas = SchemaRegistry.list_schemas()
        assert len(schemas) == 2
        assert "user" in schemas
        assert "product" in schemas
        
        # Verify error when getting non-existent schema
        with pytest.raises(ValueError, match="Schema 'nonexistent' not registered"):
            SchemaRegistry.get("nonexistent")
    
    def test_schema_validation_success(self):
        """Test successful schema validation."""
        # Clear registry for test
        SchemaRegistry._schemas = {}
        
        # Register schema
        SchemaRegistry.register("user", UserSchema)
        
        # Create context
        context = SchemaRegistry.create_context()
        
        # Add metrics listener
        metrics = MetricsListener()
        context.add_listener(metrics)
        
        # Valid data
        data = {"username": "testuser", "email": "test@example.com", "age": 30}
        
        # Validate data
        validated = context.validate("user", data)
        
        # Verify validation was successful
        assert validated.username == "testuser"
        assert validated.email == "test@example.com"
        assert validated.age == 30
        
        # Verify metrics were tracked
        stats = metrics.get_stats()
        assert stats["total"] == 1
        assert stats["successful"] == 1
        assert stats["failed"] == 0
        assert "user" in stats["schemas"]
        assert stats["schemas"]["user"]["total"] == 1
        assert stats["schemas"]["user"]["success"] == 1
        
        # Verify validation history
        history = context.get_validation_history()
        assert "user" in history
        assert len(history["user"]) == 1
        assert history["user"][0].success is True
        assert history["user"][0].schema_name == "user"
        
    def test_schema_validation_failure(self):
        """Test failed schema validation."""
        # Clear registry for test
        SchemaRegistry._schemas = {}
        
        # Register schema
        SchemaRegistry.register("user", UserSchema)
        
        # Create context
        context = SchemaRegistry.create_context()
        
        # Add metrics listener
        metrics = MetricsListener()
        context.add_listener(metrics)
        
        # Invalid data (missing required fields, wrong types)
        data = {"username": "testuser"}
        
        # Validate data (should fail)
        with pytest.raises(ValidationError):
            context.validate("user", data)
        
        # Verify metrics were tracked
        stats = metrics.get_stats()
        assert stats["total"] == 1
        assert stats["successful"] == 0
        assert stats["failed"] == 1
        assert "user" in stats["schemas"]
        assert stats["schemas"]["user"]["total"] == 1
        assert stats["schemas"]["user"]["failure"] == 1
        
        # Verify validation history
        history = context.get_validation_history()
        assert "user" in history
        assert len(history["user"]) == 1
        assert history["user"][0].success is False
        assert history["user"][0].schema_name == "user"
        assert len(history["user"][0].errors) > 0