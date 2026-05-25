import csv
from io import StringIO
from typing import Dict, Any, List

class ReportingService:
    def __init__(self):
        pass

    def generate_csv_report(self, data: List[Dict[str, Any]]) -> str:
        if not data:
            return ""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    def generate_ai_summary(self, campaign_data: Dict[str, Any]) -> str:
        # Placeholder for AI summary generation
        return "AI Summary: The campaign is performing as expected. Consider scaling budget by 10%."

reporting_service = ReportingService()
