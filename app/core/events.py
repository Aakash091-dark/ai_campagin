import asyncio
from typing import Callable, Dict, List, Any
from app.config.logging import get_logger

logger = get_logger("event-bus")

class EventBus:
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
        logger.debug(f"Subscribed to {event_type}")

    async def emit(self, event_type: str, payload: Any):
        logger.info(f"Event emitted: {event_type}")
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(payload)
                    else:
                        callback(payload)
                except Exception as e:
                    logger.error(f"Error in event listener for {event_type}: {str(e)}")

event_bus = EventBus()

# Event Constants
EVENT_CAMPAIGN_PAUSED = "campaign_paused"
EVENT_BUDGET_SCALED = "budget_scaled"
EVENT_REPORT_GENERATED = "report_generated"
