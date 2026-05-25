from typing import Dict, Any, List

class RuleBasedAI:
    def __init__(self):
        self.rules = []

    def evaluate_campaign(self, metrics: Dict[str, Any]) -> List[str]:
        suggestions = []
        ctr = metrics.get("ctr", 0)
        cpm = metrics.get("cpm", 0)
        
        if ctr < 1.0 and cpm > 10.0:
            suggestions.append("Suggest creative refresh: CTR dropped and CPM rose.")
            
        if metrics.get("roas", 0) > 3.0:
            suggestions.append("Consider scaling budget: ROAS is strong.")
            
        return suggestions

rule_based_ai = RuleBasedAI()
