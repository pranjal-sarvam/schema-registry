from sarvam_app_stream import InteractionEventListener
from sarvam_datatypes import get_ist_datetime
from ..custom_logging import logger

class LoggingListener(InteractionEventListener):
    """Listener that logs schema validation events"""
    
    def on_event(self, event):
        if event.event_type == "schema_validation":
            if event.success:
                logger.info(f"Schema '{event.schema_name}' validated successfully at {get_ist_datetime()}")
            else:
                logger.error(
                    f"Schema '{event.schema_name}' validation failed at {get_ist_datetime()}"
                    f" with errors: {', '.join(event.errors)}"
                )

class MetricsListener(InteractionEventListener):
    """Listener that tracks metrics for schema validations"""
    
    def __init__(self):
        self.total_validations = 0
        self.successful_validations = 0
        self.failed_validations = 0
        self.schema_stats = {}
        
    def on_event(self, event):
        if event.event_type == "schema_validation":
            self.total_validations += 1
            
            if event.schema_name not in self.schema_stats:
                self.schema_stats[event.schema_name] = {
                    "total": 0,
                    "success": 0,
                    "failure": 0
                }
                
            self.schema_stats[event.schema_name]["total"] += 1
            
            if event.success:
                self.successful_validations += 1
                self.schema_stats[event.schema_name]["success"] += 1
            else:
                self.failed_validations += 1
                self.schema_stats[event.schema_name]["failure"] += 1
                
    def get_stats(self):
        return {
            "total": self.total_validations,
            "successful": self.successful_validations,
            "failed": self.failed_validations,
            "schemas": self.schema_stats
        }