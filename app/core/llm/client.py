# app/core/llm/client.py
#
# =========================================================
# LLM CLIENT — STRUCTURED JSON OUTPUT
# =========================================================
# AI returns STRICT JSON matching Pydantic schemas.
# No OpenUI code generation from model.
# No regex cleanup needed.
# No hallucinated components.
# =========================================================

import json

from anthropic import AsyncAnthropic

from app.config.settings import settings
from app.core.llm.prompt_loader import load_system_prompt
from app.core.observability import llm_span
from app.config.logging import get_logger


logger = get_logger("llm-client")


# =========================================================
# BASE SYSTEM PROMPT
# =========================================================
BASE_SYSTEM_PROMPT = (
    load_system_prompt()
)


# =========================================================
# STRUCTURED JSON SYSTEM RULES
# =========================================================
JSON_SYSTEM_PROMPT = """
You are a structured data generator for marketing analytics.

You MUST return ONLY valid JSON. No explanations. No markdown. No code.

OUTPUT SCHEMAS (return ONE of these based on user request):

1. ACCOUNTS SUMMARY:
{
  "type": "accounts_summary",
  "title": "Running Ads Summary",
  "accounts": [
    {"name": "LMD02_24", "active_campaigns": 0}
  ]
}

2. ANALYTICS SUMMARY:
{
  "type": "analytics_summary",
  "title": "Campaign Performance",
  "summary": "Text summary here",
  "campaigns": [
    {"campaign_name": "Q1 Campaign", "spend": 1000, "revenue": 2500, "roi": 1.5, "status": "active"}
  ],
  "chart_data": {
    "labels": ["Jan", "Feb"],
    "datasets": [{"label": "Spend", "data": [100, 200]}]
  }
}

3. CAMPAIGN SUMMARY:
{
  "type": "campaign_summary",
  "title": "Campaign Details",
  "campaign_name": "Q1 Campaign",
  "status": "active",
  "metrics": {"spend": 1000, "impressions": 50000, "clicks": 1200, "conversions": 50}
}

4. AUTOMATION STATUS:
{
  "type": "automation_status",
  "title": "Active Automations",
  "automations": [
    {"name": "Auto-optimize", "status": "running", "last_run": "2024-01-15"}
  ]
}

5. REJECTED ADS:
{
  "type": "rejected_ads",
  "title": "Rejected Ad Copies",
  "ads": [
    {"name": "Ad 1", "reason": "Policy violation", "date": "2024-01-10"}
  ]
}

6. REPORT:
{
  "type": "report",
  "title": "Monthly Report",
  "sections": [
    {"heading": "Summary", "content": "Text content...", "chart_data": null}
  ]
}

7. SIMPLE TEXT:
{
  "type": "text",
  "content": "Your message here"
}

8. TABLE:
{
  "type": "table",
  "columns": ["Col1", "Col2"],
  "rows": [["val1", "val2"]]
}

9. CHART:
{
  "type": "chart",
  "chart_type": "line",
  "title": "Chart Title",
  "labels": ["Jan", "Feb"],
  "datasets": [{"label": "Series", "data": [10, 20]}]
}

10. ALERT:
{
  "type": "alert",
  "title": "Warning",
  "description": "Something happened",
  "variant": "warning"
}

11. ERROR:
{
  "type": "error",
  "title": "Error Title",
  "message": "Error description"
}

STRICT RULES:
- Return ONLY JSON — NO markdown, NO code fences, NO explanations, NO conversation
- Use ONLY data provided in tool results — NEVER hallucinate metrics
- Choose the MOST specific schema type for the context
- For complex dashboards with campaigns + charts → use "analytics_summary"
- For simple tables → use "table"
- For simple messages → use "text"
- Type field MUST be one of: accounts_summary, analytics_summary, campaign_summary, automation_status, rejected_ads, report, text, table, chart, alert, error
"""


# =========================================================
# FINAL SYSTEM PROMPT
# =========================================================
SYSTEM_PROMPT = f"""
{BASE_SYSTEM_PROMPT}

{JSON_SYSTEM_PROMPT}
"""


# =========================================================
# ANTHROPIC CLIENT
# =========================================================
anthropic_client = AsyncAnthropic(
    api_key=settings.ANTHROPIC_API_KEY
)


# =========================================================
# FALLBACK JSON
# =========================================================
def build_fallback_json(
    text: str,
) -> dict:
    """Build fallback JSON when AI fails."""
    return {
        "type": "text",
        "content": str(text),
    }


# =========================================================
# GENERATE COMPLETION — STRUCTURED JSON
# =========================================================
async def generate_completion(
    messages: list,
    system: str = "",
):
    """
    Generate a structured JSON response from the LLM.

    Returns:
        dict with keys:
        - success: bool
        - response: str (JSON string from AI)
        - tokens_used: int
        - raw_response: str
    """
    try:

        logger.info(
            "Generating structured JSON completion"
        )

        # =============================================
        # ADD JSON INSTRUCTION TO USER MESSAGE
        # =============================================
        json_instruction = (
            "\n\nIMPORTANT: Return ONLY valid JSON. "
            "No markdown. No code fences. No explanations. "
            "Use the schemas provided in the system prompt."
        )

        if messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "user":
                messages[-1] = {
                    "role": "user",
                    "content": last_msg["content"] + json_instruction,
                }

        # =============================================
        # FINAL SYSTEM PROMPT
        # =============================================
        final_system_prompt = f"""
{SYSTEM_PROMPT}

{system}
"""

        # =============================================
        # GENERATE RESPONSE
        # =============================================
        async with llm_span(model=settings.AI_MODEL, agent="llm-client") as span:
            response = (
                await anthropic_client.messages.create(
                    model=settings.AI_MODEL,
                    max_tokens=settings.AI_MAX_TOKENS,
                    temperature=0.1,
                    system=final_system_prompt,
                    messages=messages,
                )
            )
            span["tokens_used"] = getattr(response.usage, "output_tokens", 0)

        final_text = ""

        # =============================================
        # EXTRACT TEXT BLOCKS
        # =============================================
        for block in response.content:
            if hasattr(block, "type") and block.type == "text":
                final_text += block.text

        tokens_out = getattr(response.usage, "output_tokens", 0)

        # =============================================
        # CLEAN RESPONSE — strip markdown fences if any
        # =============================================
        cleaned_text = final_text.strip()

        # Remove markdown code fences if present
        if cleaned_text.startswith("```"):
            first_brace = cleaned_text.find("{")
            last_brace = cleaned_text.rfind("}")
            if first_brace != -1 and last_brace != -1:
                cleaned_text = cleaned_text[first_brace:last_brace + 1]

        cleaned_text = cleaned_text.replace("```json", "").replace("```", "").strip()

        # =============================================
        # VALIDATE JSON
        # =============================================
        try:
            json.loads(cleaned_text)
        except json.JSONDecodeError:
            logger.warning("AI response is not valid JSON — wrapping in fallback")
            cleaned_text = json.dumps(build_fallback_json(cleaned_text))

        logger.info("JSON completion generated", preview=cleaned_text[:300])

        return {
            "success": True,
            "response": cleaned_text,
            "tokens_used": tokens_out,
            "raw_response": final_text,
        }

    except Exception as e:

        logger.error(
            "LLM completion failed",
            error=str(e),
        )

        fallback_response = json.dumps(
            build_fallback_json(
                f"AI generation failed: {str(e)}"
            )
        )

        return {
            "success": False,
            "response": fallback_response,
            "tokens_used": 0,
            "raw_response": str(e),
        }