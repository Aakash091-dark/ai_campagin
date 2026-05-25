# app/core/orchestrator/post_processor.py
#
# =========================================================
# POST PROCESSOR — JSON → OpenUI
# =========================================================
# Takes ui_json from LLM, validates it, renders to OpenUI.
# No regex cleanup. No hallucinated components.
# =========================================================

import json

from app.core.openui.json_renderer import (
    render_ui_json,
)

from app.config.logging import (
    get_logger,
)


logger = get_logger("post-processor")


# =========================================================
# SAFE STRING FOR ERROR UI
# =========================================================
def _safe_str(value: str) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


# =========================================================
# FALLBACK ERROR UI
# =========================================================
def _error_ui(
    title: str,
    message: str,
) -> str:
    return (
        f'error_alert = Alert("{_safe_str(title)}", '
        f'"{_safe_str(message)}", "destructive")\n'
        'retry_item = FollowUpItem("Try again")\n'
        'follow_ups = FollowUpBlock([retry_item])\n'
        'root = Card([error_alert, follow_ups])'
    )


# =========================================================
# PROCESS FINAL RESPONSE
# =========================================================
def process_final_response(
    state,
):
    """
    Takes ui_json from agent state, renders to OpenUI.

    Pipeline:
    1. Read ui_json (JSON string) from state
    2. Parse JSON
    3. Render via json_renderer → deterministic OpenUI
    4. Store in state["openui_response"]
    """
    try:

        ui_json_string = state.get(
            "ui_json",
            "",
        )

        if not ui_json_string:

            logger.warning(
                "Empty ui_json in state — "
                "checking openui_response fallback"
            )

            # Check if we have a direct openui_response fallback
            direct_response = state.get(
                "openui_response",
                "",
            )

            if direct_response:
                return state

            state["openui_response"] = (
                _error_ui(
                    "Empty Response",
                    "AI returned empty output",
                )
            )

            return state

        # =============================================
        # PARSE JSON
        # =============================================
        if isinstance(ui_json_string, str):
            try:
                ui_json = json.loads(ui_json_string)
            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to parse ui_json",
                    error=str(e),
                )
                state["openui_response"] = (
                    _error_ui(
                        "Invalid JSON",
                        f"AI returned invalid JSON: {str(e)}",
                    )
                )
                return state
        else:
            # Already a dict
            ui_json = ui_json_string

        # =============================================
        # RENDER TO OPENUI
        # =============================================
        rendered = render_ui_json(ui_json)

        state["openui_response"] = rendered

        logger.info(
            "Post processor — JSON rendered to OpenUI",
            schema_type=ui_json.get("type", "unknown"),
        )

        return state

    except Exception as e:

        logger.error(
            "Post processor failed",
            error=str(e),
        )

        state["openui_response"] = (
            _error_ui(
                "Rendering Failure",
                str(e),
            )
        )

        return state