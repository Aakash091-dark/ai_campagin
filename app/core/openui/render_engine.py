# app/core/openui/render_engine.py
#
# =========================================================
# RENDER ENGINE — JSON → OpenUI
# =========================================================
# AI returns strict JSON → Python renders deterministic OpenUI.
# No regex cleanup needed.
# No hallucinated components.
# No new Function() execution.
# =========================================================

import json

from app.core.openui.json_renderer import (
    render_ui_json,
)

from app.config.logging import (
    get_logger,
)


logger = get_logger("render-engine")


# =========================================================
# RENDER OPENUI FROM JSON
# =========================================================
def render_openui_from_json(
    ui_json: dict,
) -> str:
    """
    Render structured JSON into deterministic OpenUI code.

    Args:
        ui_json: Validated JSON dict matching one of the UISchema types.

    Returns:
        Deterministic OpenUI code string.
    """
    try:

        if not ui_json:

            logger.warning(
                "Empty UI JSON — returning fallback error UI"
            )

            return (
                'error_alert = Alert("Empty Response", '
                '"AI returned empty JSON", "destructive")\n'
                'retry_item = FollowUpItem("Try again")\n'
                'follow_ups = FollowUpBlock([retry_item])\n'
                'root = Card([error_alert, follow_ups])'
            )

        result = render_ui_json(ui_json)

        logger.info(
            "OpenUI rendered from JSON successfully",
            schema_type=ui_json.get("type", "unknown"),
        )

        return result

    except Exception as e:

        logger.error(
            "Render engine failed",
            error=str(e),
        )

        return (
            'error_alert = Alert("Render Engine Failure", '
            f'"{_safe_json_str(str(e))}", "destructive")\n'
            'retry_item = FollowUpItem("Try again")\n'
            'follow_ups = FollowUpBlock([retry_item])\n'
            'root = Card([error_alert, follow_ups])'
        )


# =========================================================
# LEGACY — backward compat for old callers
# =========================================================
def render_openui(
    openui_code: str,
) -> str:
    """
    Legacy render function — tries to parse as JSON first,
    falls back to treating as raw OpenUI text for backward compat.

    In the new architecture, this just wraps the JSON renderer.
    Callers should migrate to render_openui_from_json().
    """
    try:
        # Try to parse as JSON
        ui_json = json.loads(openui_code)
        return render_openui_from_json(ui_json)
    except (json.JSONDecodeError, TypeError):
        # If it's already OpenUI code, pass it through
        logger.warning(
            "render_openui received non-JSON — "
            "returning as-is for backward compat"
        )
        return openui_code


def _safe_json_str(value: str) -> str:
    """Escape a string for use inside OpenUI double-quoted strings."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )