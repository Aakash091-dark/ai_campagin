# app/schemas/ui_schemas.py
#
# =========================================================
# PYDANTIC MODELS FOR STRUCTURED UI JSON
# =========================================================
# AI returns STRICT JSON instead of executable OpenUI code.
# Python renderer converts JSON → OpenUI deterministically.
# =========================================================

from pydantic import BaseModel
from pydantic import Field
from typing import Optional
from typing import List
from typing import Any
from typing import Dict
from typing import Union
from enum import Enum


# =========================================================
# UI SCHEMA TYPES
# =========================================================
class UISchemaType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    CHART = "chart"
    ALERT = "alert"
    BADGE = "badge"
    ANALYTICS_SUMMARY = "analytics_summary"
    CAMPAIGN_SUMMARY = "campaign_summary"
    ACCOUNTS_SUMMARY = "accounts_summary"
    AUTOMATION_STATUS = "automation_status"
    REJECTED_ADS = "rejected_ads"
    REPORT = "report"
    ERROR = "error"
    GENERIC = "generic"


# =========================================================
# BASE COMPONENT SCHEMAS
# =========================================================
class TextSchema(BaseModel):
    type: str = "text"
    content: str


class TableSchema(BaseModel):
    type: str = "table"
    columns: List[str]
    rows: List[List[Any]]


class ChartSchema(BaseModel):
    type: str = "chart"
    chart_type: str = Field(
        ...,
        description="line, bar, pie, area, radial, radar, scatter",
    )
    title: Optional[str] = None
    labels: List[str]
    datasets: List[Dict[str, Any]]


class AlertSchema(BaseModel):
    type: str = "alert"
    title: str
    description: str
    variant: str = "default"


class BadgeSchema(BaseModel):
    type: str = "badge"
    label: str
    variant: str = "default"


# =========================================================
# DOMAIN-SPECIFIC SCHEMAS
# =========================================================
class AccountSummarySchema(BaseModel):
    """Accounts summary — from analytics/campaigns agent."""
    type: str = "accounts_summary"
    title: str = Field(
        ...,
        description="Card title",
    )
    accounts: List[Dict[str, Any]] = Field(
        ...,
        description="List of account objects with name, active_campaigns, etc.",
    )


class AnalyticsSummarySchema(BaseModel):
    """Full analytics dashboard — from analytics agent."""
    type: str = "analytics_summary"
    title: str = Field(
        ...,
        description="Dashboard title",
    )
    summary: str = Field(
        ...,
        description="Text summary of analytics",
    )
    campaigns: List[Dict[str, Any]] = Field(
        ...,
        description="Campaign data with spend, revenue, roi, status",
    )
    chart_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional chart data with labels and datasets",
    )


class CampaignSummarySchema(BaseModel):
    """Single campaign details — from campaigns agent."""
    type: str = "campaign_summary"
    title: str = Field(
        ...,
        description="Campaign card title",
    )
    campaign_name: str
    status: str
    metrics: Dict[str, Any] = Field(
        ...,
        description="Key metrics like spend, impressions, clicks, conversions",
    )


class AutomationStatusSchema(BaseModel):
    """Automation statuses — from automations agent."""
    type: str = "automation_status"
    title: str = Field(
        ...,
        description="Automations card title",
    )
    automations: List[Dict[str, Any]] = Field(
        ...,
        description="List of automation objects with name, status, last_run",
    )


class RejectedAdsSchema(BaseModel):
    """Rejected ads list — from rejected_ads agent."""
    type: str = "rejected_ads"
    title: str = Field(
        ...,
        description="Rejected ads card title",
    )
    ads: List[Dict[str, Any]] = Field(
        ...,
        description="List of rejected ad objects with name, reason, date",
    )


class ReportSection(BaseModel):
    """A single section within a report."""
    heading: str
    content: str
    chart_data: Optional[Dict[str, Any]] = None


class ReportSchema(BaseModel):
    """Full report — from reporting agent."""
    type: str = "report"
    title: str
    sections: List[ReportSection]


class ErrorSchema(BaseModel):
    """Error display."""
    type: str = "error"
    title: str = "Error"
    message: str


class GenericUISchema(BaseModel):
    """Fallback generic schema — builds from raw components."""
    type: str = "generic"
    title: Optional[str] = None
    components: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of component dicts with type and props",
    )


# =========================================================
# UNION — ALL VALID UI SCHEMAS
# =========================================================
UISchema = Union[
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
]