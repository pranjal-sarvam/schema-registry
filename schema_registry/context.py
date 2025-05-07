from typing import Dict, Any, Type, List, Optional
from datetime import datetime
from pydantic import BaseModel, ValidationError
from sarvam_app_stream import (
    GenericStateMachine, 
    StateContext, 
    InteractionEventListener, 
    InteractionEvent
)
from ..custom_logging import logger

class SchemaValidationEvent(InteractionEvent):
    """Event fired when schema validation occurs"""
    def __init__(
        self, 
        schema_name: str, 
        success: bool, 
        errors: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        self.event_type = "schema_validation"
        self.schema_name = schema_name
        self.success = success
        self.errors = errors or []
        self.timestamp = datetime.now()
        self.context = context or {}
        
class SchemaContext(StateContext):
    """Context for schema validation using sarvam_app_stream state management"""
    
    def __init__(self, schema_registry, context_id: str = "schema_validation"):
        self._state_machine = GenericStateMachine()
        super().__init__(state_machine=self._state_machine, context_id=context_id)
        self.schema_registry = schema_registry
        self.validation_results: Dict[str, List[SchemaValidationEvent]] = {}
        self._listeners: List[InteractionEventListener] = []
        
    def add_listener(self, listener: InteractionEventListener):
        """Add a listener to receive schema validation events"""
        self._listeners.append(listener)
        
    def validate(self, schema_name: str, data: Dict[str, Any], context: Dict[str, Any] = None) -> Any:
        """Validate data against a schema and emit events"""
        try:
            schema_class = self.schema_registry.get(schema_name)
            validated = schema_class(**data)
            
            # Create success event
            event = SchemaValidationEvent(
                schema_name=schema_name,
                success=True,
                context=context
            )
            
            # Track the event
            if schema_name not in self.validation_results:
                self.validation_results[schema_name] = []
            self.validation_results[schema_name].append(event)
            
            # Emit the event
            self.notify_event(event)
            
            return validated
            
        except ValidationError as e:
            errors = [str(err) for err in e.errors()]
            
            # Create failure event
            event = SchemaValidationEvent(
                schema_name=schema_name,
                success=False,
                errors=errors,
                context=context
            )
            
            # Track the event
            if schema_name not in self.validation_results:
                self.validation_results[schema_name] = []
            self.validation_results[schema_name].append(event)
            
            # Emit the event
            self.notify_event(event)
            
            # Re-raise with useful information
            raise ValidationError(f"Schema '{schema_name}' validation failed: {errors}", e.raw_errors)
            
    def notify_event(self, event: InteractionEvent):
        """Notify all listeners of an event"""
        for listener in self._listeners:
            try:
                listener.on_event(event)
            except Exception as e:
                logger.error(f"Error in event listener: {str(e)}")
                
    def get_validation_history(self, schema_name: Optional[str] = None) -> Dict[str, List[SchemaValidationEvent]]:
        """Get validation history for all schemas or a specific schema"""
        if schema_name:
            return {schema_name: self.validation_results.get(schema_name, [])}
        return self.validation_results