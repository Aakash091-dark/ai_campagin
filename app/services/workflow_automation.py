from typing import Dict, Any, List
import json

class WorkflowAutomationSystem:
    def __init__(self):
        self.rules = []
    
    def add_rule(self, trigger: str, condition: callable, actions: List[str]):
        """
        Add a new automation rule.
        """
        self.rules.append({
            "trigger": trigger,
            "condition": condition,
            "actions": actions
        })

    def evaluate_event(self, event: Dict[str, Any]):
        """
        Evaluate an incoming event against registered rules.
        """
        triggered_actions = []
        for rule in self.rules:
            if rule["trigger"] == event.get("type"):
                if rule["condition"](event.get("data", {})):
                    triggered_actions.extend(rule["actions"])
                    print(f"Rule triggered! Executing actions: {rule['actions']}")
        
        return self._execute_actions(triggered_actions, event.get("data", {}))

    def _execute_actions(self, actions: List[str], data: Dict[str, Any]):
        """
        Execute the actions sequentially.
        """
        results = []
        for action in actions:
            # Simulated action execution
            print(f"Executing action: {action} with data: {data}")
            if action == "analyze":
                results.append({"action": "analyze", "status": "completed", "details": "Analysis complete."})
            elif action == "pause_campaign":
                results.append({"action": "pause_campaign", "status": "completed", "campaign_id": data.get("campaign_id")})
            elif action == "notify_user":
                results.append({"action": "notify_user", "status": "completed", "message": f"Alert! ROAS dropped for campaign {data.get('campaign_id')}."})
        return results

# Pre-configured rules
def setup_default_workflows() -> WorkflowAutomationSystem:
    system = WorkflowAutomationSystem()
    
    # Rule: ROAS drops -> analyze -> pause campaign -> notify user
    system.add_rule(
        trigger="metric_update",
        condition=lambda data: data.get("metric") == "ROAS" and data.get("value", 0) < data.get("threshold", 1.0),
        actions=["analyze", "pause_campaign", "notify_user"]
    )
    
    return system

automation_system = setup_default_workflows()
