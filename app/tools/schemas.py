# app/tools/schemas.py
#
# Strict Pydantic schemas for every write operation.
# The AI must collect all required fields from the user
# before calling the corresponding tool.

from __future__ import annotations

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# =========================================================
# SHARED / PRIMITIVES
# =========================================================

class AlertCondition(BaseModel):
    metric: str = Field(..., description="e.g. Spend, CPC, ROAS")
    condition: str = Field(..., description="e.g. '>', '<', 'Increases By %'")
    value: str = Field(..., description="Numeric threshold as string")
    unit: Optional[str] = Field(None, description="e.g. '$'")
    period: Optional[str] = Field(None, description="e.g. 'Last 30 Minutes,Last 1 Hour'")
    logical_operator: Optional[str] = Field(None, description="AND | OR")


class AutomationCondition(BaseModel):
    metric: str = Field(..., description="e.g. spend, CPM, ROAS")
    operator: str = Field(..., description="e.g. '>', '<', '>='")
    value: float = Field(..., description="Numeric threshold")
    unit: Optional[str] = Field(None, description="e.g. '$'")
    conjunction: Optional[Literal["AND", "OR"]] = None


# =========================================================
# DASHBOARD
# =========================================================

class DashboardSummaryParams(BaseModel):
    from_date: str = Field(..., description="Start date YYYY-MM-DD")
    to_date: str = Field(..., description="End date YYYY-MM-DD")


class DashboardTimeseriesParams(BaseModel):
    granularity: Literal["day", "hour", "week"] = Field(..., description="day | hour | week")
    from_date: str = Field(..., description="Start date YYYY-MM-DD")
    to_date: str = Field(..., description="End date YYYY-MM-DD")


class DashboardUserTrendsParams(BaseModel):
    user_id: int = Field(..., description="User ID")
    granularity: Literal["day", "hour", "week"] = Field(..., description="day | hour | week")
    from_date: str = Field(..., description="Start date YYYY-MM-DD")
    to_date: str = Field(..., description="End date YYYY-MM-DD")


class DashboardAccountDrilldownParams(BaseModel):
    platform: Literal["facebook", "google", "tiktok"] = Field(..., description="Ad platform")
    account_id: str = Field(..., description="Ad account ID")
    start_date: str = Field(..., description="Start date YYYY-MM-DD")
    end_date: str = Field(..., description="End date YYYY-MM-DD")


# =========================================================
# WORKSPACE
# =========================================================

class CreateWorkspaceSchema(BaseModel):
    name: str = Field(..., description="Workspace name")
    default_timezone: str = Field(..., description="e.g. Asia/Kolkata")
    media_buyer_code_wise: bool = Field(False, description="Group by media buyer code?")


class UpdateWorkspaceSchema(BaseModel):
    name: Optional[str] = None
    default_timezone: Optional[str] = None
    media_buyer_code_wise: Optional[bool] = None
    is_favorite: Optional[bool] = None


class DeleteWorkspacesSchema(BaseModel):
    workspace_ids: list[int] = Field(..., description="List of workspace IDs to delete")


# =========================================================
# ACCOUNTS
# =========================================================

class BackfillSchema(BaseModel):
    platform: Literal["facebook", "google", "tiktok"] = Field(..., description="Ad platform")
    start_date: str = Field(..., description="Start date YYYY-MM-DD")
    end_date: str = Field(..., description="End date YYYY-MM-DD")


# =========================================================
# ACCOUNT LINKING
# =========================================================

class PlatformAdAccountSelection(BaseModel):
    account_id: str
    account_name: str
    timezone: str
    currency: str
    parent_manager_id: Optional[str] = None


class LinkPlatformAdAccountsSchema(BaseModel):
    workspace_id: int = Field(..., description="Workspace ID")
    platform: Literal["facebook", "google", "tiktok"] = Field(..., description="Ad platform")
    session: str = Field(..., description="Base64 session string from OAuth callback")
    selections: list[PlatformAdAccountSelection] = Field(..., description="Ad accounts to link")


class ManualIntegrationItem(BaseModel):
    workspace_id: int
    name: str
    account_id: str
    platform: str
    token: str
    timezone: str
    currency: str
    profile_name: str
    profile_id: str


# =========================================================
# ACCOUNT ASSIGNMENT
# =========================================================

class AccountAssignSchema(BaseModel):
    workspace_id: int = Field(..., description="Workspace ID")
    account_ids: list[int] = Field(..., description="List of account IDs")
    user_id: int = Field(..., description="User ID to assign to")


class AccountUnassignSchema(BaseModel):
    workspace_id: int = Field(..., description="Workspace ID")
    account_ids: list[int] = Field(..., description="List of account IDs")
    user_id: int = Field(..., description="User ID to unassign from")


class AccountSelfAssignSchema(BaseModel):
    account_ids: list[int] = Field(..., description="List of account IDs to self-assign")


class AccountAssignUnassignSchema(BaseModel):
    workspace_id: int = Field(..., description="Workspace ID")
    user_id: int = Field(..., description="User ID")
    assign: list[int] = Field(default_factory=list, description="Account IDs to assign")
    un_assign: list[int] = Field(default_factory=list, description="Account IDs to unassign")


# =========================================================
# CAMPAIGN STATUS / BUDGET / BID
# =========================================================

class CampaignStatusItem(BaseModel):
    account_id: str
    campaign_id: str
    status: Literal["ACTIVE", "PAUSED", "DELETED"]
    platform: Literal["facebook", "google", "tiktok"]


class CampaignBudgetItem(BaseModel):
    account_id: str
    campaign_id: str
    budget: float
    budget_type: Literal["DAILY", "LIFETIME"]
    status: Literal["ACTIVE", "PAUSED"]


class AdsetBudgetItem(BaseModel):
    account_id: str
    campaign_id: str
    adset_id: str
    budget: float
    budget_type: Literal["DAILY", "LIFETIME"]
    status: Literal["ACTIVE", "PAUSED"]


class AdsetBidItem(BaseModel):
    account_id: str
    campaign_id: str
    adset_id: str
    bid_amount: float


class GoogleAdsetBidItem(BaseModel):
    account_id: str
    campaign_id: str
    adset_id: str
    cpc_bid_amount: float


class AdsetStatusItem(BaseModel):
    account_id: str
    campaign_id: str
    adset_id: str
    status: Literal["ACTIVE", "PAUSED", "DELETED"]
    platform: Literal["facebook", "google", "tiktok"]


class AdStatusItem(BaseModel):
    account_id: str
    campaign_id: str
    adset_id: str
    ad_id: str
    material_id: str
    status: Literal["ACTIVE", "PAUSED", "DELETED"]
    platform: Literal["facebook", "google", "tiktok"]


class AdDeleteItem(BaseModel):
    account_id: str
    campaign_id: str
    adset_id: str
    ad_id: str
    platform: Literal["facebook", "google", "tiktok"]


class CampaignDeleteItem(BaseModel):
    account_id: str
    campaign_id: str
    platform: Literal["facebook", "google", "tiktok"]


class AdsetDeleteItem(BaseModel):
    account_id: str
    campaign_id: str
    adset_id: str
    platform: Literal["facebook", "google", "tiktok"]


class AdMaterialStatusItem(BaseModel):
    account_id: str
    ad_id: str
    adset_id: str
    material_id: str
    status: Literal["ENABLE", "DISABLE"]


class GoogleEnhancedCpcItem(BaseModel):
    account_id: str
    campaign_id: str
    enhanced_cpc_enabled: bool
    bidding_strategy: str
    bid_value: float


# =========================================================
# CAMPAIGN LAUNCHER
# =========================================================

class CreateCampaignSchema(BaseModel):
    account_id: str = Field(..., description="Ad account ID")
    name: str = Field(..., description="Campaign name")
    objective: str = Field(..., description="e.g. OUTCOME_SALES, OUTCOME_TRAFFIC")
    status: Literal["ACTIVE", "PAUSED"] = Field(..., description="Initial status")
    bid_strategy: Optional[str] = Field(None, description="e.g. LOWEST_COST_WITHOUT_CAP")


class CreateAdsetSchema(BaseModel):
    campaign_id: str = Field(..., description="Parent campaign ID")
    account_id: str = Field(..., description="Ad account ID")
    name: str = Field(..., description="Ad set name")
    status: Literal["ACTIVE", "PAUSED"] = Field(..., description="Initial status")
    optimization_goal: str = Field(..., description="e.g. OFFSITE_CONVERSIONS")
    daily_budget: str = Field(..., description="Daily budget as string (in account currency)")
    targeting: dict[str, Any] = Field(..., description="Targeting spec (geo, age, etc.)")


class CreateAdSchema(BaseModel):
    adset_id: str = Field(..., description="Parent ad set ID")
    account_id: str = Field(..., description="Ad account ID")
    name: str = Field(..., description="Ad name")
    status: Literal["ACTIVE", "PAUSED"] = Field(..., description="Initial status")
    page_id: str = Field(..., description="Facebook Page ID")
    creative: dict[str, Any] = Field(..., description="Creative spec (link_data, video_data, etc.)")


class LaunchCampaignSchema(BaseModel):
    account_id: str = Field(..., description="Ad account ID")
    campaign_name: str = Field(..., description="Campaign name")
    objective: str = Field(..., description="e.g. OUTCOME_SALES")
    campaign_status: Literal["ACTIVE", "PAUSED"] = Field(..., description="Initial status")


class CampaignTemplateSchema(BaseModel):
    template_name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    data: dict[str, Any] = Field(default_factory=dict, description="Template data payload")


# =========================================================
# SMART ALERTS
# =========================================================

class CreateSmartAlertSchema(BaseModel):
    alert_name: str = Field(..., description="Alert name")
    scope: str = Field(..., description="e.g. Campaign Level, Ad Set Level")
    target: str = Field(..., description="e.g. platform, specific")
    platform: Literal["facebook", "google", "tiktok"] = Field(..., description="Ad platform")
    entity_target: Literal["all", "specific"] = Field(..., description="all or specific entities")
    entity_ids: Optional[list[str]] = Field(None, description="Specific entity IDs if entity_target=specific")
    entity_names: Optional[list[str]] = Field(None, description="Corresponding entity names")
    conditions: list[AlertCondition] = Field(..., description="Alert trigger conditions")
    timezone: str = Field(..., description="e.g. America/New_York")
    notify_in_app: bool = Field(True, description="Send in-app notification")
    notify_email: bool = Field(False, description="Send email notification")
    notify_telegram: bool = Field(False, description="Send Telegram notification")


class UpdateSmartAlertSchema(BaseModel):
    alert_name: Optional[str] = None
    notify_email: Optional[bool] = None
    notify_in_app: Optional[bool] = None
    notify_telegram: Optional[bool] = None
    conditions: Optional[list[AlertCondition]] = None


# =========================================================
# AUTOMATIONS
# =========================================================

class CreateAutomationSchema(BaseModel):
    name: str = Field(..., description="Automation rule name")
    action_type: Literal["pause", "resume", "increase_budget", "decrease_budget"] = Field(
        ..., description="Action to take when triggered"
    )
    platform: Literal["facebook", "google", "tiktok"] = Field(..., description="Ad platform")
    entity_level: Literal["campaign", "adset", "ad"] = Field(..., description="Level to act on")
    entity_ids: list[str] = Field(..., description="Entity IDs to monitor")
    trigger_type: Literal["interval", "schedule"] = Field(..., description="interval or schedule")
    frequency_minutes: Optional[int] = Field(None, description="Check interval in minutes (for interval trigger)")
    notify_in_app: bool = Field(True, description="Send in-app notification")
    notify_email: bool = Field(False, description="Send email notification")
    conditions: list[AutomationCondition] = Field(..., description="Trigger conditions")


class UpdateAutomationSchema(BaseModel):
    frequency_minutes: Optional[int] = None
    notify_in_app: Optional[bool] = None
    notify_email: Optional[bool] = None
    conditions: Optional[list[AutomationCondition]] = None


# =========================================================
# TASKS
# =========================================================

class CreateTaskCategorySchema(BaseModel):
    name: str = Field(..., description="Category name")


class CreateTaskTagSchema(BaseModel):
    name: str = Field(..., description="Tag name")


class CreateTaskSchema(BaseModel):
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    remark: Optional[str] = Field(None, description="Additional remark")
    category_id: Optional[int] = Field(None, description="Category ID")
    priority: Literal["low", "medium", "high"] = Field(..., description="Task priority")
    assigned_to: list[int] = Field(default_factory=list, description="User IDs to assign")
    due_at: Optional[str] = Field(None, description="Due datetime ISO 8601")
    tag_ids: list[int] = Field(default_factory=list, description="Tag IDs")
    watcher_ids: list[int] = Field(default_factory=list, description="Watcher user IDs")
    is_repeat: bool = Field(False, description="Is this a repeating task?")
    repeat_type: Optional[Literal["daily", "weekly", "monthly"]] = None
    repeat_start_at: Optional[str] = None
    repeat_time: Optional[str] = None
    repeat_due_days: Optional[int] = None
    repeat_on_days: Optional[list[int]] = None
    repeat_on_dates: Optional[list[int]] = None


class UpdateTaskSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    tag_ids: Optional[list[int]] = None
    watcher_ids: Optional[list[int]] = None
    due_at: Optional[str] = None


class UpdateTaskStatusSchema(BaseModel):
    status: Literal["pending", "in_progress", "completed", "cancelled"] = Field(
        ..., description="New task status"
    )


class AddTaskCommentSchema(BaseModel):
    content: str = Field(..., description="Comment text")


# =========================================================
# GOALS
# =========================================================

class CreateGoalSchema(BaseModel):
    user_id: int = Field(..., description="User ID")
    target_period: str = Field(..., description="Month in YYYY-MM format e.g. 2026-05")
    target_profit: float = Field(..., description="Target profit amount")


class UpdateGoalSchema(BaseModel):
    target_profit: float = Field(..., description="Updated target profit amount")


# =========================================================
# NOTES
# =========================================================

class CreateNoteSchema(BaseModel):
    title: str = Field(..., description="Note title")
    html: str = Field(..., description="Note content as HTML")
    preview: str = Field(..., description="Plain text preview")
    settings: Optional[dict[str, Any]] = Field(
        default_factory=lambda: {
            "fontFamily": "-apple-system, BlinkMacSystemFont, sans-serif",
            "fontSize": 15,
            "textAlign": "left",
        }
    )
    wordCount: Optional[int] = None
    charCount: Optional[int] = None


class UpdateNoteSchema(BaseModel):
    title: Optional[str] = None
    html: Optional[str] = None
    preview: Optional[str] = None
    settings: Optional[dict[str, Any]] = None
    wordCount: Optional[int] = None
    charCount: Optional[int] = None


# =========================================================
# REPORTING CONFIG
# =========================================================

class ReportingSlotsConfig(BaseModel):
    s1: Optional[str] = Field(None, description="Slot 1 time HH:MM")
    s2: Optional[str] = Field(None, description="Slot 2 time HH:MM")
    s3: Optional[str] = Field(None, description="Slot 3 time HH:MM")


class CreateReportingConfigSchema(BaseModel):
    slots_config: ReportingSlotsConfig = Field(..., description="Time slots configuration")
    timezone: str = Field(..., description="e.g. Asia/Kolkata")
    buffer_before_min: int = Field(..., description="Buffer minutes before slot")
    buffer_after_min: int = Field(..., description="Buffer minutes after slot")
    is_active: bool = Field(True, description="Enable this config?")


class SubmitReportSchema(BaseModel):
    slot_id: str = Field(..., description="Slot ID e.g. s1, s2, s3")
    data: dict[str, Any] = Field(..., description="Platform-keyed spend/revenue/leads data")
    date: str = Field(..., description="Report date YYYY-MM-DD")


# =========================================================
# PERMISSIONS
# =========================================================

class TabPermission(BaseModel):
    enabled: bool
    editable: bool


class UpdateUserTabPermissionsSchema(BaseModel):
    tabs: dict[str, TabPermission] = Field(
        ..., description="Tab name → {enabled, editable} mapping"
    )


# =========================================================
# TRACKERS
# =========================================================

class CreateTrackerItem(BaseModel):
    name: str
    tracker_name: str = Field(..., description="e.g. Binom, RedTrack")
    platform: Literal["facebook", "google", "tiktok"]
    traffic_channel_id: str
    traffic_channel_name: str
    campaign_sub: str
    adset_sub: str
    ad_sub: str
    placement_sub: str
    media_buyer_code: str
    timezone: str
    tracker_id: int
    token: str
    client_id: str
    is_enterprise_level: bool = False


class UpdateTrackerSchema(BaseModel):
    name: Optional[str] = None
    tracker_name: Optional[str] = None
    traffic_channel_id: Optional[str] = None
    traffic_channel_name: Optional[str] = None
    campaign_sub: Optional[str] = None
    adset_sub: Optional[str] = None
    ad_sub: Optional[str] = None
    placement_sub: Optional[str] = None
    media_buyer_code: Optional[str] = None
    timezone: Optional[str] = None
    token: Optional[str] = None
    client_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_enterprise_level: Optional[bool] = None


# =========================================================
# USER MANAGEMENT
# =========================================================

class CreateAdminSchema(BaseModel):
    workspace_id: int = Field(..., description="Workspace ID")
    email: str = Field(..., description="Admin email")
    name: str = Field(..., description="Full name")
    number: str = Field(..., description="Phone number")
    password: str = Field(..., description="Password (min 8 chars)")


class CreateTLSchema(BaseModel):
    workspace_id: int = Field(..., description="Workspace ID")
    email: str = Field(..., description="Team Lead email")
    name: str = Field(..., description="Full name")
    number: str = Field(..., description="Phone number")
    password: str = Field(..., description="Password (min 8 chars)")


class CreateUserSchema(BaseModel):
    workspace_id: int = Field(..., description="Workspace ID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="Full name")
    number: str = Field(..., description="Phone number")
    password: str = Field(..., description="Password (min 8 chars)")
    tl_id: Optional[int] = Field(None, description="Team Lead user ID")


class AssignTLSchema(BaseModel):
    workspace_id: int = Field(..., description="Workspace ID")
    user_id: int = Field(..., description="User ID")
    tl_id: int = Field(..., description="Team Lead user ID")


# =========================================================
# USER PROFILE
# =========================================================

class UpdateUserProfileSchema(BaseModel):
    name: Optional[str] = None
    number: Optional[str] = None
    social_id: Optional[str] = None
    profile_pic: Optional[str] = None
    media_buyer_code: Optional[str] = None


class AddUserTagsSchema(BaseModel):
    workspace_id: int = Field(..., description="Workspace ID")
    platform: Literal["facebook", "google", "tiktok"] = Field(..., description="Ad platform")
    category: str = Field(..., description="e.g. campaign, adset, ad")
    entity_id: str = Field(..., description="Entity ID to tag")
    tags: list[str] = Field(..., description="List of tag strings")


# =========================================================
# TIMEZONE
# =========================================================

class SetWorkspaceTimezoneSchema(BaseModel):
    timezone: str = Field(..., description="Timezone string e.g. America/New_York")


# =========================================================
# REJECTED ADS
# =========================================================

class RejectedAdItem(BaseModel):
    ad_id: str
    account_id: str


class AppealRejectedAdsSchema(BaseModel):
    items: list[RejectedAdItem] = Field(..., description="Ads to appeal")


class UpdateRejectedAdSchema(BaseModel):
    items: list[RejectedAdItem] = Field(..., description="Ads to update")
    ad_status: Optional[str] = Field(None, description="e.g. PAUSED")
    image_hash: Optional[str] = None
    primary_text: Optional[str] = None
    headline: Optional[str] = None
    description: Optional[str] = None
    call_to_action: Optional[str] = None
    link: Optional[str] = None
    display_link: Optional[str] = None
