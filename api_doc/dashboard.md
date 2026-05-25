# Dashboard API Documentation

## Overview
The dashboard API provides a summary of workspace-level ad account performance,
active campaigns, spend, and key metrics across all connected platforms.

---

## Endpoints

### GET `/api/v1/workspaces/{workspace_id}/dashboard/summary`
Returns the full dashboard summary for a workspace.

**Response**:
```json
{
  "workspace_id": 1,
  "total_spend": 12500.00,
  "total_revenue": 38000.00,
  "total_roas": 3.04,
  "active_campaigns": 8,
  "paused_campaigns": 3,
  "total_campaigns": 11,
  "impressions": 1200000,
  "clicks": 48000,
  "ctr": 4.0,
  "conversions": 960,
  "cpc": 0.26,
  "accounts": [
    {
      "id": "act_001",
      "name": "LMD02_24",
      "platform": "facebook",
      "status": "active",
      "active_campaigns": 3,
      "spend": 4200.00,
      "roas": 3.1
    },
    {
      "id": "act_002",
      "name": "LMD_Google_01",
      "platform": "google",
      "status": "active",
      "active_campaigns": 2,
      "spend": 3800.00,
      "roas": 2.9
    }
  ]
}
```

---

### GET `/api/v1/workspaces/{workspace_id}/dashboard/accounts`
Returns all connected ad accounts with their current status.

**Response**:
```json
{
  "workspace_id": 1,
  "total_accounts": 4,
  "accounts": [
    {
      "id": "act_001",
      "name": "LMD02_24",
      "platform": "facebook",
      "status": "active",
      "currency": "USD",
      "active_campaigns": 3,
      "spend_today": 420.00,
      "spend_this_month": 4200.00
    }
  ]
}
```

---

### GET `/api/v1/workspaces/{workspace_id}/dashboard/metrics`
Returns aggregated performance metrics for the workspace.

**Response**:
```json
{
  "workspace_id": 1,
  "period": "last_30_days",
  "spend": 12500.00,
  "revenue": 38000.00,
  "roas": 3.04,
  "impressions": 1200000,
  "clicks": 48000,
  "ctr": 4.0,
  "cpc": 0.26,
  "conversions": 960,
  "cost_per_conversion": 13.02,
  "top_platform": "facebook",
  "trend": {
    "spend_change": "+12%",
    "roas_change": "+0.3",
    "conversions_change": "+8%"
  }
}
```
