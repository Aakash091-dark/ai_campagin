import uuid
from typing import Dict, Any, Callable
from app.config.logging import get_logger

logger = get_logger("approval-system")

class ApprovalManager:
    def __init__(self):
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}

    def request_approval(self, action_name: str, payload: dict, callback: Callable) -> str:
        """Create a pending approval request for a dangerous action."""
        approval_id = str(uuid.uuid4())
        self.pending_approvals[approval_id] = {
            "action_name": action_name,
            "payload": payload,
            "callback": callback,
            "status": "pending"
        }
        logger.info(f"Approval requested for {action_name} [ID: {approval_id}]")
        return approval_id

    async def approve(self, approval_id: str) -> Any:
        """Approve and execute a pending action."""
        if approval_id not in self.pending_approvals:
            raise ValueError("Approval ID not found or already processed")
        
        request = self.pending_approvals[approval_id]
        if request["status"] != "pending":
            raise ValueError(f"Approval is in status {request['status']}")
            
        logger.info(f"Executing approved action: {request['action_name']}")
        request["status"] = "approved"
        
        callback = request["callback"]
        # Execute the callback
        import asyncio
        if asyncio.iscoroutinefunction(callback):
            result = await callback(**request["payload"])
        else:
            result = callback(**request["payload"])
            
        del self.pending_approvals[approval_id]
        return result

    def reject(self, approval_id: str):
        """Reject a pending action."""
        if approval_id in self.pending_approvals:
            request = self.pending_approvals[approval_id]
            logger.info(f"Rejected action: {request['action_name']}")
            del self.pending_approvals[approval_id]

approval_manager = ApprovalManager()
