# app/core/openui/json_renderer.py
#
# =========================================================
# STRUCTURED JSON → OPENUI RENDERER
# =========================================================
# Takes validated Pydantic JSON from LLM and converts
# deterministically to OpenUI code. No regex cleanup.
# No hallucinated components. No JS execution.
# =========================================================

import json

from app.schemas.ui_schemas import (
    AccountSummarySchema,
    AnalyticsSummarySchema,
    CampaignSummarySchema,
    ReportSchema,
    AutomationStatusSchema,
    RejectedAdsSchema,
    TextSchema,
    TableSchema,
    ChartSchema,
    AlertSchema,
    BadgeSchema,
    ErrorSchema,
    GenericUISchema,
)

from app.config.logging import (
    get_logger,
)


logger = get_logger("json-renderer")


# =========================================================
# SCHEMA MAP — type string → Pydantic model
# =========================================================
_SCHEMA_MAP = {
    "accounts_summary": AccountSummarySchema,
    "analytics_summary": AnalyticsSummarySchema,
    "campaign_summary": CampaignSummarySchema,
    "report": ReportSchema,
    "automation_status": AutomationStatusSchema,
    "rejected_ads": RejectedAdsSchema,
    "text": TextSchema,
    "table": TableSchema,
    "chart": ChartSchema,
    "alert": AlertSchema,
    "badge": BadgeSchema,
    "error": ErrorSchema,
    "generic": GenericUISchema,
}


# =========================================================
# SAFE STRING
# =========================================================
def _safe_str(value: str) -> str:
    """Escape a string for use inside OpenUI double-quoted strings."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )


# =========================================================
# RENDER TEXT
# =========================================================
def _render_text(
    schema: TextSchema,
    component_index: int,
) -> list[str]:
    lines = []
    var_name = f"text_{component_index}"
    lines.append(f'{var_name} = TextContent("{_safe_str(schema.content)}")')
    return lines, var_name


# =========================================================
# RENDER TABLE
# =========================================================
def _render_table(
    schema: TableSchema,
    component_index: int,
) -> list[str]:
    lines = []
    var_name = f"table_{component_index}"
    columns_json = json.dumps(schema.columns)
    rows_json = json.dumps(schema.rows)
    lines.append(f"{var_name} = Table(columns={columns_json}, rows={rows_json})")
    return lines, var_name


# =========================================================
# RENDER CHART
# =========================================================
def _render_chart(
    schema: ChartSchema,
    component_index: int,
) -> list[str]:
    lines = []
    var_name = f"chart_{component_index}"
    # Build data dict like OpenUI expects
    data = {
        "labels": schema.labels,
        "datasets": schema.datasets,
    }
    data_json = json.dumps(data)
    lines.append(f'{var_name} = Chart(type="{_safe_str(schema.chart_type)}", data={data_json})')
    return lines, var_name


# =========================================================
# RENDER ALERT
# =========================================================
def _render_alert(
    schema: AlertSchema,
    component_index: int,
) -> list[str]:
    lines = []
    var_name = f"alert_{component_index}"
    lines.append(
        f'{var_name} = Alert('
        f'"{_safe_str(schema.title)}", '
        f'"{_safe_str(schema.description)}", '
        f'"{_safe_str(schema.variant)}"'
        f')'
    )
    return lines, var_name


# =========================================================
# RENDER BADGE
# =========================================================
def _render_badge(
    schema: BadgeSchema,
    component_index: int,
) -> list[str]:
    lines = []
    var_name = f"badge_{component_index}"
    lines.append(f'{var_name} = Badge("{_safe_str(schema.label)}", "{_safe_str(schema.variant)}")')
    return lines, var_name


# =========================================================
# RENDER ACCOUNTS SUMMARY
# =========================================================
def _render_accounts_summary(
    schema: AccountSummarySchema,
) -> tuple[list[str], str]:
    """Renders an accounts summary card."""
    lines = []
    idx = 0

    # Title text
    title_var = "summary_title"
    lines.append(f'{title_var} = TextContent("{_safe_str(schema.title)}")')

    # Accounts table
    columns = ["Account", "Active Campaigns"]
    accounts_rows = []
    for acct in schema.accounts:
        accounts_rows.append([
            acct.get("name", "-"),
            acct.get("active_campaigns", 0),
        ])

    table_var = "accounts_table"
    columns_json = json.dumps(columns)
    rows_json = json.dumps(accounts_rows)
    lines.append(f"{table_var} = Table(columns={columns_json}, rows={rows_json})")

    # Card root
    lines.append(f"root = Card([{title_var}, {table_var}])")

    return lines


# =========================================================
# RENDER ANALYTICS SUMMARY
# =========================================================
def _render_analytics_summary(
    schema: AnalyticsSummarySchema,
) -> tuple[list[str], str]:
    """Renders a full analytics dashboard."""
    lines = []
    component_vars = []

    # Title
    title_var = "analytics_title"
    lines.append(f'{title_var} = TextContent("{_safe_str(schema.title)}")')
    component_vars.append(title_var)

    # Summary text
    summary_var = "analytics_summary"
    lines.append(f'{summary_var} = TextContent("{_safe_str(schema.summary)}")')
    component_vars.append(summary_var)

    # Campaigns table
    if schema.campaigns:
        columns = ["Campaign", "Spend", "Revenue", "ROI", "Status"]
        table_rows = []
        for c in schema.campaigns:
            table_rows.append([
                c.get("campaign_name", "-"),
                c.get("spend", 0),
                c.get("revenue", 0),
                c.get("roi", 0),
                c.get("status", "-"),
            ])
        table_var = "analytics_table"
        columns_json = json.dumps(columns)
        rows_json = json.dumps(table_rows)
        lines.append(f"{table_var} = Table(columns={columns_json}, rows={rows_json})")
        component_vars.append(table_var)

    # Chart
    if schema.chart_data:
        chart_var = "analytics_chart"
        data_json = json.dumps(schema.chart_data)
        lines.append(f'{chart_var} = Chart(type="line", data={data_json})')
        component_vars.append(chart_var)

    # Card root
    components_str = ", ".join(component_vars)
    lines.append(f"root = Card([{components_str}])")

    return lines


# =========================================================
# RENDER CAMPAIGN SUMMARY
# =========================================================
def _render_campaign_summary(
    schema: CampaignSummarySchema,
) -> tuple[list[str], str]:
    lines = []
    component_vars = []

    # Title
    title_var = "campaign_title"
    lines.append(f'{title_var} = TextContent("{_safe_str(schema.title)}")')
    component_vars.append(title_var)

    # Campaign name and status as text
    info_var = "campaign_info"
    info_text = f"Campaign: {schema.campaign_name} | Status: {schema.status}"
    lines.append(f'{info_var} = TextContent("{_safe_str(info_text)}")')
    component_vars.append(info_var)

    # Metrics table
    if schema.metrics:
        columns = ["Metric", "Value"]
        metric_rows = []
        for key, value in schema.metrics.items():
            metric_rows.append([key, str(value)])
        table_var = "campaign_metrics"
        columns_json = json.dumps(columns)
        rows_json = json.dumps(metric_rows)
        lines.append(f"{table_var} = Table(columns={columns_json}, rows={rows_json})")
        component_vars.append(table_var)

    components_str = ", ".join(component_vars)
    lines.append(f"root = Card([{components_str}])")

    return lines


# =========================================================
# RENDER AUTOMATION STATUS
# =========================================================
def _render_automation_status(
    schema: AutomationStatusSchema,
) -> tuple[list[str], str]:
    lines = []
    component_vars = []

    # Title
    title_var = "automation_title"
    lines.append(f'{title_var} = TextContent("{_safe_str(schema.title)}")')
    component_vars.append(title_var)

    # Automations table
    if schema.automations:
        columns = ["Name", "Status", "Last Run"]
        auto_rows = []
        for a in schema.automations:
            auto_rows.append([
                a.get("name", "-"),
                a.get("status", "-"),
                a.get("last_run", "-"),
            ])
        table_var = "automation_table"
        columns_json = json.dumps(columns)
        rows_json = json.dumps(auto_rows)
        lines.append(f"{table_var} = Table(columns={columns_json}, rows={rows_json})")
        component_vars.append(table_var)

    components_str = ", ".join(component_vars)
    lines.append(f"root = Card([{components_str}])")

    return lines


# =========================================================
# RENDER REJECTED ADS
# =========================================================
def _render_rejected_ads(
    schema: RejectedAdsSchema,
) -> tuple[list[str], str]:
    lines = []
    component_vars = []

    # Title
    title_var = "rejected_title"
    lines.append(f'{title_var} = TextContent("{_safe_str(schema.title)}")')
    component_vars.append(title_var)

    # Ads table
    if schema.ads:
        columns = ["Ad Name", "Reason", "Date"]
        ads_rows = []
        for ad in schema.ads:
            ads_rows.append([
                ad.get("name", "-"),
                ad.get("reason", "-"),
                ad.get("date", "-"),
            ])
        table_var = "rejected_table"
        columns_json = json.dumps(columns)
        rows_json = json.dumps(ads_rows)
        lines.append(f"{table_var} = Table(columns={columns_json}, rows={rows_json})")
        component_vars.append(table_var)

    components_str = ", ".join(component_vars)
    lines.append(f"root = Card([{components_str}])")

    return lines


# =========================================================
# RENDER REPORT
# =========================================================
def _render_report(
    schema: ReportSchema,
) -> tuple[list[str], str]:
    lines = []
    component_vars = []

    # Title
    title_var = "report_title"
    lines.append(f'{title_var} = TextContent("{_safe_str(schema.title)}")')
    component_vars.append(title_var)

    # Sections
    for i, section in enumerate(schema.sections):
        heading_var = f"report_heading_{i}"
        lines.append(
            f'{heading_var} = TextContent("{_safe_str(section.heading)}")'
        )
        component_vars.append(heading_var)

        content_var = f"report_content_{i}"
        lines.append(
            f'{content_var} = TextContent("{_safe_str(section.content)}")'
        )
        component_vars.append(content_var)

        if section.chart_data:
            chart_var = f"report_chart_{i}"
            data_json = json.dumps(section.chart_data)
            lines.append(f'{chart_var} = Chart(type="line", data={data_json})')
            component_vars.append(chart_var)

    components_str = ", ".join(component_vars)
    lines.append(f"root = Card([{components_str}])")

    return lines


# =========================================================
# RENDER GENERIC
# =========================================================
def _render_generic(
    schema: GenericUISchema,
) -> tuple[list[str], str]:
    """Fallback: builds from raw component list."""
    lines = []
    component_vars = []

    if schema.title:
        title_var = "generic_title"
        lines.append(f'{title_var} = TextContent("{_safe_str(schema.title)}")')
        component_vars.append(title_var)

    for i, comp in enumerate(schema.components):
        comp_type = comp.get("type", "text")
        comp_vars, var_name = _render_raw_component(
            comp_type,
            comp,
            i,
        )
        lines.extend(comp_vars)
        component_vars.append(var_name)

    components_str = ", ".join(component_vars)
    lines.append(f"root = Card([{components_str}])")

    return lines


# =========================================================
# RENDER RAW COMPONENT (for generic fallback)
# =========================================================
def _render_raw_component(
    comp_type: str,
    props: dict,
    index: int,
) -> tuple[list[str], str]:
    """Render a component from a raw props dict."""
    lines = []
    var_name = f"comp_{index}"

    if comp_type == "text":
        content = _safe_str(props.get("content", ""))
        lines.append(f'{var_name} = TextContent("{content}")')
    elif comp_type == "table":
        columns = json.dumps(props.get("columns", []))
        rows = json.dumps(props.get("rows", []))
        lines.append(f"{var_name} = Table(columns={columns}, rows={rows})")
    elif comp_type == "chart":
        chart_type = _safe_str(props.get("chart_type", "line"))
        data = json.dumps(props.get("data", {}))
        lines.append(f'{var_name} = Chart(type="{chart_type}", data={data})')
    elif comp_type == "alert":
        lines.append(
            f'{var_name} = Alert('
            f'"{_safe_str(props.get("title", ""))}", '
            f'"{_safe_str(props.get("description", ""))}", '
            f'"{_safe_str(props.get("variant", "default"))}"'
            f')'
        )
    elif comp_type == "badge":
        lines.append(
            f'{var_name} = Badge('
            f'"{_safe_str(props.get("label", ""))}", '
            f'"{_safe_str(props.get("variant", "default"))}"'
            f')'
        )
    else:
        # Fallback to text
        content = _safe_str(str(props))
        lines.append(f'{var_name} = TextContent("{content}")')

    return lines, var_name


# =========================================================
# RENDER ERROR
# =========================================================
def _render_error(
    schema: ErrorSchema,
) -> tuple[list[str], str]:
    lines = []
    lines.append(
        f'error_alert = Alert('
        f'"{_safe_str(schema.title)}", '
        f'"{_safe_str(schema.message)}", '
        f'"destructive"'
        f')'
    )
    lines.append("retry_item = FollowUpItem(\"Try again\")")
    lines.append("follow_ups = FollowUpBlock([retry_item])")
    lines.append("root = Card([error_alert, follow_ups])")
    return lines


# =========================================================
# RENDER TEXT (top-level — wraps in Card)
# =========================================================
def _render_text_toplevel(
    schema: TextSchema,
) -> list[str]:
    lines = []
    lines.append(f'msg = TextContent("{_safe_str(schema.content)}")')
    lines.append("root = Card([msg])")
    return lines


# =========================================================
# RENDER TABLE (top-level — wraps in Card)
# =========================================================
def _render_table_toplevel(
    schema: TableSchema,
) -> list[str]:
    lines = []
    columns_json = json.dumps(schema.columns)
    rows_json = json.dumps(schema.rows)
    lines.append(f"data_table = Table(columns={columns_json}, rows={rows_json})")
    lines.append("root = Card([data_table])")
    return lines


# =========================================================
# RENDER CHART (top-level — wraps in Card)
# =========================================================
def _render_chart_toplevel(
    schema: ChartSchema,
) -> list[str]:
    lines = []
    data = {"labels": schema.labels, "datasets": schema.datasets}
    data_json = json.dumps(data)
    lines.append(f'data_chart = Chart(type="{_safe_str(schema.chart_type)}", data={data_json})')
    lines.append("root = Card([data_chart])")
    return lines


# =========================================================
# RENDER ALERT (top-level — wraps in Card)
# =========================================================
def _render_alert_toplevel(
    schema: AlertSchema,
) -> list[str]:
    lines = []
    lines.append(
        f'msg_alert = Alert('
        f'"{_safe_str(schema.title)}", '
        f'"{_safe_str(schema.description)}", '
        f'"{_safe_str(schema.variant)}"'
        f')'
    )
    lines.append("root = Card([msg_alert])")
    return lines


# =========================================================
# RENDER BADGE (top-level — wraps in Card)
# =========================================================
def _render_badge_toplevel(
    schema: BadgeSchema,
) -> list[str]:
    lines = []
    lines.append(f'msg_badge = Badge("{_safe_str(schema.label)}", "{_safe_str(schema.variant)}")')
    lines.append("root = Card([msg_badge])")
    return lines


# =========================================================
# ROUTER: JSON SCHEMA → OPENUI
# =========================================================
_JSON_RENDERERS = {
    "accounts_summary": _render_accounts_summary,
    "analytics_summary": _render_analytics_summary,
    "campaign_summary": _render_campaign_summary,
    "report": _render_report,
    "automation_status": _render_automation_status,
    "rejected_ads": _render_rejected_ads,
    "error": _render_error,
    "generic": _render_generic,
    "text": _render_text_toplevel,
    "table": _render_table_toplevel,
    "chart": _render_chart_toplevel,
    "alert": _render_alert_toplevel,
    "badge": _render_badge_toplevel,
}


# =========================================================
# MAIN ENTRY POINT
# =========================================================
def render_ui_json(
    ui_json: dict,
) -> str:
    """
    Renders a structured JSON dict into deterministic OpenUI code.

    Validates the dict into the correct Pydantic model first so
    renderer functions receive typed objects, not raw dicts.

    Args:
        ui_json: A dict matching one of the UISchema types.

    Returns:
        Deterministic OpenUI code string. No regex cleaning needed.
    """
    try:
        schema_type = ui_json.get("type", "generic")

        logger.info(
            "Rendering UI JSON",
            schema_type=schema_type,
        )

        # =============================================
        # VALIDATE DICT → PYDANTIC MODEL
        # =============================================
        schema_class = _SCHEMA_MAP.get(
            schema_type,
            GenericUISchema,
        )

        try:
            validated = schema_class(**ui_json)
        except Exception as ve:
            logger.warning(
                "Schema validation failed — falling back to generic",
                error=str(ve),
                schema_type=schema_type,
            )
            validated = GenericUISchema(
                type="generic",
                title=ui_json.get("title"),
                components=[],
            )
            schema_type = "generic"

        renderer = _JSON_RENDERERS.get(
            schema_type,
            _render_generic,
        )

        lines = renderer(validated)

        result = "\n".join(lines)

        # Ensure result has a root
        if "root =" not in result:
            result += "\nroot = Card([])"

        logger.info(
            "UI JSON rendered successfully",
            schema_type=schema_type,
            line_count=len(lines),
        )

        return result

    except Exception as e:

        logger.error(
            "UI JSON renderer failed",
            error=str(e),
        )

        return (
            'error_alert = Alert("Render Error", '
            f'"{_safe_str(str(e))}", "destructive")\n'
            'retry_item = FollowUpItem("Try again")\n'
            'follow_ups = FollowUpBlock([retry_item])\n'
            'root = Card([error_alert, follow_ups])'
        )