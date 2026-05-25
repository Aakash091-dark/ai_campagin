# Lemonmaxx AI Campaign Backend - API Documentation

## Overview

**Lemonmaxx AI** is a sophisticated Python FastAPI backend service that leverages Claude AI to intelligently manage advertising campaigns across Facebook, Instagram, Google, and TikTok platforms. It provides a unified API interface that frontend applications can integrate to enable natural language-based campaign management with AI-powered recommendations.

### Key Features
- 🤖 **AI-Powered Recommendations**: Uses Claude AI to analyze campaigns and suggest optimal actions
- 📊 **Campaign Management**: Launch, pause, resume, update budgets, and manage campaigns
- 💰 **Budget & Bid Management**: Intelligently adjust budgets and bids based on performance
- 📈 **Analytics & Forecasting**: Predict campaign performance and identify optimization opportunities
- 🎯 **Multi-Platform Support**: Unified interface for Facebook, Google, TikTok ad accounts
- 🔄 **Workspace Management**: Multi-tenant support for managing multiple workspaces
- 💾 **Conversation Memory**: Maintains context across conversation turns using embeddings and semantic search
- ⚡ **Real-time Updates**: WebSocket support for streaming AI responses
- 🔐 **Secure Authentication**: Token-based authentication with workspace isolation

---

## Architecture

### Tech Stack
- **Framework**: FastAPI (Python 3.9+)
- **AI/LLM**: Claude (Anthropic) with function calling
- **Database**: PostgreSQL (async with SQLAlchemy)
- **Cache**: Redis (conversation context, rate limiting)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Orchestration**: LangGraph for agentic workflows
- **API Client**: httpx with retry logic

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Application                 │
│              (Chat UI, Campaign Dashboard)              │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/WebSocket
                       │
┌──────────────────────▼──────────────────────────────────┐
│              FastAPI Application Server                 │
│                  (Lemonmaxx AI Backend)                 │
├──────────────────────────────────────────────────────────┤
│                    API Routes                           │
│  ├─ POST /api/v1/ai/chat (AI chat endpoint)            │
│  ├─ POST /api/v1/ai/execute (Execute actions)          │
│  ├─ GET  /api/v1/ai/workspace/{id}/recommendations     │
│  ├─ GET  /api/v1/memory/* (Conversation memory)        │
│  ├─ GET  /api/v1/conversations/* (Chat history)        │
│  └─ GET  /health/* (Health checks)                     │
├──────────────────────────────────────────────────────────┤
│              AI Orchestration Layer (LangGraph)         │
│  ├─ Router Node (Agent selection)                       │
│  ├─ Analytics Agent                                     │
│  ├─ Campaign Agent                                      │
│  ├─ Automations Agent                                   │
│  ├─ Reporting Agent                                     │
│  ├─ Rejected Ads Agent                                  │
│  └─ General Agent                                       │
├──────────────────────────────────────────────────────────┤
│         Claude AI with Tool Functions                   │
│  ├─ Campaign tools (pause, resume, create, delete)     │
│  ├─ Budget tools (update budgets, bid management)      │
│  ├─ Analytics tools (fetch insights, forecasts)        │
│  ├─ Account management tools                           │
│  └─ Workspace tools                                    │
└──────────────────────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
    PostgreSQL      Redis        Campaign Backend API
    (Sessions,    (Cache,      (Lemonmaxx Platform)
     Memory)     Concurrency)    (External Service)
```

---

## API Endpoints

### Authentication

All endpoints (except `/`, `/health/*`, `/api/v1/test/*`) require:

```
Header: Authorization: Bearer <token>
```

**Development Token**: `lemonmaxx-dev-token`

---

### Core AI Chat Endpoint

#### **POST** `/api/v1/ai/chat`
Send a natural language message to the AI and receive an OpenUI-formatted response.

**Request Body**:
```json
{
  "workspace_id": 123,
  "conversation_id": "conv-uuid-optional",
  "message": "List all my ad accounts and their current spend"
}
```

**Response**:
```json
{
  "success": true,
  "conversation_id": "conv-uuid",
  "openui_response": "root = Card([...]) // Valid OpenUI code",
  "execution_time": 2.45,
  "agent_used": "analytics",
  "tokens_used": 1250
}
```

**Example Usage**:
```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer lemonmaxx-dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": 1,
    "message": "Show me all active campaigns with spend over $100"
  }'
```

---

### Recommendations & Analysis

#### **GET** `/api/v1/ai/workspace/{workspace_id}/recommendations`
Get AI-generated recommendations for a workspace.

**Query Parameters**:
- `limit` (int, default: 10): Number of recommendations
- `priority` (enum: high, medium, low): Filter by priority

**Response**:
```json
{
  "workspace_id": 123,
  "recommendations": [
    {
      "id": "rec-1",
      "type": "campaign_optimization",
      "title": "Pause low-performing campaign",
      "description": "Campaign XYZ has 0.5% CTR, 10% below benchmark",
      "priority": "high",
      "estimated_impact": "5-8% improvement in ROAS",
      "action": {
        "type": "pause_campaign",
        "campaign_id": "cam-456"
      }
    }
  ]
}
```

---

### Memory & Context Management

#### **GET** `/api/v1/memory/search`
Search conversation memory using semantic similarity.

**Query Parameters**:
- `workspace_id` (int, required)
- `query` (str, required): Search query
- `limit` (int, default: 5): Number of results

**Response**:
```json
{
  "results": [
    {
      "type": "preference",
      "content": "User prefers budget allocation of 40% to Facebook campaigns",
      "similarity_score": 0.92
    }
  ]
}
```

---

#### **POST** `/api/v1/memory/save`
Save user preferences to memory.

**Request Body**:
```json
{
  "workspace_id": 123,
  "memory_type": "preference",
  "content": "Always allocate 60% budget to Facebook, 40% to Google"
}
```

---

### Conversation History

#### **GET** `/api/v1/conversations/{conversation_id}`
Retrieve conversation history.

**Query Parameters**:
- `workspace_id` (int, required)
- `limit` (int, default: 50): Number of messages
- `offset` (int, default: 0): Pagination offset

**Response**:
```json
{
  "conversation_id": "conv-uuid",
  "workspace_id": 123,
  "created_at": "2026-05-22T16:00:00Z",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "Launch a campaign for product X",
      "created_at": "2026-05-22T16:00:05Z"
    },
    {
      "id": "msg-2",
      "role": "assistant",
      "content": "root = Card([...]) // OpenUI response",
      "tools_used": ["list_accounts", "launch_campaign"],
      "created_at": "2026-05-22T16:00:10Z"
    }
  ]
}
```

---

#### **GET** `/api/v1/conversations`
List all conversations for a workspace.

**Query Parameters**:
- `workspace_id` (int, required)
- `limit` (int, default: 20)
- `offset` (int, default: 0)

---

### Health & Monitoring

#### **GET** `/health/`
Basic health check.

**Response**:
```json
{
  "success": true,
  "service": "Lemonmaxx AI",
  "status": "healthy"
}
```

---

#### **GET** `/health/detailed`
Detailed health check including dependencies.

**Response**:
```json
{
  "success": true,
  "environment": "development",
  "database": true,
  "redis": true,
  "ai_model": "claude-sonnet-4-20250514"
}
```

---

### WebSocket (Streaming)

#### **WS** `/ws/chat/{workspace_id}/{conversation_id}`
Real-time AI response streaming via WebSocket.

**Connection**:
```javascript
const ws = new WebSocket(
  'ws://localhost:8000/ws/chat/123/conv-uuid',
  ['Authorization', 'Bearer lemonmaxx-dev-token']
);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data); // Streaming response chunks
};
```

---

## AI Agent Types

The system automatically routes user messages to the appropriate AI agent:

### 1. **Analytics Agent**
Handles queries about campaign performance, insights, and reporting.

**Triggered by**:
- "Show me spending analytics"
- "What's the ROAS for campaign X?"
- "Generate a performance report"

**Available Tools**:
- `get_campaign_insights()`
- `get_historical_insights()`
- `export_analytics_report()`

---

### 2. **Campaign Agent**
Manages campaign lifecycle: creation, updates, status changes, budgets.

**Triggered by**:
- "Launch a new campaign"
- "Pause all campaigns"
- "Update budget to $500"

**Available Tools**:
- `list_campaigns()`
- `launch_campaign()`
- `pause_campaigns()`
- `resume_campaigns()`
- `update_budget()`
- `delete_campaigns()`

---

### 3. **Automation Agent**
Handles automation rules and scheduling.

**Triggered by**:
- "Set up auto-pause for low performers"
- "Create a rule to pause if CTR < 1%"

**Available Tools**:
- `create_automation()`
- `list_automations()`
- `update_automation()`

---

### 4. **Reporting Agent**
Manages reporting templates and submissions.

**Triggered by**:
- "Submit a report"
- "Show reporting templates"

**Available Tools**:
- `get_reporting_template()`
- `submit_report()`

---

### 5. **Rejected Ads Agent**
Handles rejected ads, appeals, and replacements.

**Triggered by**:
- "Show rejected ads"
- "Appeal this ad rejection"

**Available Tools**:
- `get_rejected_ads()`
- `appeal_rejected_ad()`
- `update_ad_image()`

---

### 6. **General Agent**
Fallback for general queries, greetings, and out-of-scope requests.

---

## Campaign Tool Functions

### Campaign Management

#### `list_campaigns(workspace_id: int, limit: int = 100)`
List all campaigns in a workspace.

```python
# Called by AI when user asks: "Show all campaigns"
response = await list_campaigns(workspace_id=123)
# Returns: [{id, name, status, budget, spend, ...}, ...]
```

---

#### `launch_campaign(workspace_id: int, campaign_config: dict, confirmed: bool = False)`
Launch a new campaign. Requires two-step confirmation.

```python
# Step 1: Preview (confirmed=False)
response = await launch_campaign(
    workspace_id=123,
    campaign_config={
        "name": "Summer Sale Campaign",
        "platform": "facebook",
        "budget": 1000,
        "start_date": "2026-05-30",
        "targeting": {...}
    },
    confirmed=False
)

# Step 2: Confirm & Execute (confirmed=True)
response = await launch_campaign(
    workspace_id=123,
    campaign_config={...},
    confirmed=True
)
```

---

#### `pause_campaigns(workspace_id: int, campaign_ids: list)`
Pause one or more campaigns.

```python
response = await pause_campaigns(
    workspace_id=123,
    campaign_ids=["cam-1", "cam-2", "cam-3"]
)
```

---

#### `resume_campaigns(workspace_id: int, campaign_ids: list)`
Resume paused campaigns.

```python
response = await resume_campaigns(
    workspace_id=123,
    campaign_ids=["cam-1", "cam-2"]
)
```

---

#### `update_campaign_budget(workspace_id: int, campaign_id: str, new_budget: float)`
Update campaign budget.

```python
response = await update_campaign_budget(
    workspace_id=123,
    campaign_id="cam-1",
    new_budget=2500
)
```

---

#### `delete_campaigns(workspace_id: int, campaign_ids: list)`
Delete campaigns (destructive).

```python
response = await delete_campaigns(
    workspace_id=123,
    campaign_ids=["cam-1"]
)
```

---

## Analytics Tool Functions

#### `get_campaign_insights(workspace_id: int, campaign_id: str)`
Fetch live campaign metrics.

```python
response = await get_campaign_insights(
    workspace_id=123,
    campaign_id="cam-1"
)
# Returns: {spend, impressions, clicks, conversions, roas, cpc, ctr, ...}
```

---

#### `get_historical_insights(workspace_id: int, date_range: dict)`
Fetch historical performance data.

```python
response = await get_historical_insights(
    workspace_id=123,
    date_range={
        "start_date": "2026-05-01",
        "end_date": "2026-05-22"
    }
)
```

---

## Error Handling

### Common Error Responses

**401 Unauthorized**:
```json
{
  "detail": "Authorization header missing"
}
```

**429 Rate Limited**:
```json
{
  "detail": "Too many requests. Max 2 concurrent requests per user."
}
```

**500 Server Error**:
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

The system enforces per-user concurrency limits:

- **Global Limit**: 10 concurrent AI requests
- **Per-User Limit**: 2 concurrent AI requests
- **Duration**: 5 minutes

---

## OpenUI Response Format

All AI responses are valid **OpenUI** code (a declarative UI language):

```
root = Card([
  CardHeader("Campaign Analysis"),
  Table([
    TableRow(["Campaign Name", "Status", "Spend", "ROAS"]),
    TableRow(["Summer Sale", "Active", "$1,250", "3.2x"]),
    TableRow(["Fall Promo", "Paused", "$800", "2.8x"]),
  ]),
  FollowUpBlock([
    FollowUpItem("Pause low performers"),
    FollowUpItem("Increase budget for top campaign"),
    FollowUpItem("Show detailed analytics")
  ])
])
```

---

## Example Workflows

### Workflow 1: Launch a Campaign

```bash
# Step 1: Send message
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer lemonmaxx-dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": 1,
    "message": "Launch a campaign for product X with $1000 budget"
  }'

# Response: AI shows preview in OpenUI format with confirmation button

# Step 2: User clicks "Confirm" which sends:
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Authorization: Bearer lemonmaxx-dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": 1,
    "conversation_id": "same-conversation-id",
    "message": "Confirm and launch"
  }'

# Response: Campaign launched successfully
```

---

### Workflow 2: Get AI Recommendations

```bash
# Get recommendations
curl -X GET http://localhost:8000/api/v1/ai/workspace/1/recommendations \
  -H "Authorization: Bearer lemonmaxx-dev-token" \
  -H "Content-Type: application/json"

# Response:
# [
#   {
#     "type": "campaign_optimization",
#     "title": "Pause campaign with 0.5% CTR",
#     "priority": "high",
#     "action": {"type": "pause_campaign", "campaign_id": "cam-1"}
#   }
# ]
```

---

### Workflow 3: Search Memory

```bash
# Search for user preferences
curl -X GET "http://localhost:8000/api/v1/memory/search?workspace_id=1&query=budget%20preference" \
  -H "Authorization: Bearer lemonmaxx-dev-token"

# Response:
# {
#   "results": [
#     {
#       "type": "preference",
#       "content": "User prefers 60% Facebook, 40% Google allocation",
#       "similarity_score": 0.89
#     }
#   ]
# }
```

---

## Configuration

### Environment Variables (`.env`)

```env
# App
APP_NAME=Lemonmaxx AI
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# AI
AI_MODEL=claude-sonnet-4-20250514
AI_MAX_TOKENS=4096
AI_TEMPERATURE=0.1
ANTHROPIC_API_KEY=sk-ant-api03-...

# Database
POSTGRES_DIRECT_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=admin
POSTGRES_DB=lemonmaxx_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Embeddings
AI_EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMS=384
SIMILARITY_THRESHOLD=0.70

# Backend API (External Campaign Management Service)
BACKEND_BASE_URL=http://localhost:8001
BACKEND_API_KEY=your-backend-api-key

# Concurrency
AI_MAX_CONCURRENT=10
AI_MAX_PER_USER=2
```

---

## Deployment

### Docker

```bash
# Build image
docker build -t lemonmaxx-ai:latest .

# Run container
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e POSTGRES_DIRECT_HOST=postgres-host \
  -e REDIS_HOST=redis-host \
  lemonmaxx-ai:latest
```

### Production Setup

1. Use PostgreSQL with SSL
2. Enable Redis persistence
3. Configure proper authentication (JWT tokens)
4. Set up monitoring and logging (ELK stack)
5. Use async worker: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`

---

## Support & Testing

### Test Endpoint

```bash
curl -X GET http://localhost:8000/api/v1/test/echo?message=hello
```

### Interactive API Docs

Visit: `http://localhost:8000/docs` (Swagger UI)
Visit: `http://localhost:8000/redoc` (ReDoc)

---

## Performance Metrics

- **Average Response Time**: 2-5 seconds (depending on AI processing)
- **Throughput**: ~100 requests/second (at 10 concurrent limit)
- **Database Queries**: 1-3 per request (optimized with caching)
- **Token Usage**: 500-2000 tokens per AI request (depending on complexity)

---

## Troubleshooting

### Issue: "Redis connection failed"
- Ensure Redis is running: `redis-cli ping`
- Check `REDIS_HOST` and `REDIS_PORT` in `.env`

### Issue: "Database connection failed"
- Ensure PostgreSQL is running: `psql -U postgres`
- Verify `POSTGRES_DIRECT_HOST` and credentials
- Check database exists: `psql -l | grep lemonmaxx_db`

### Issue: "Unauthorized" on AI endpoints
- Include correct header: `Authorization: Bearer lemonmaxx-dev-token`
- Check token in auth middleware (for development only)

---

## Future Enhancements

- [ ] JWT token authentication with workspace isolation
- [ ] Advanced analytics forecasting models
- [ ] Campaign A/B testing recommendations
- [ ] Multi-language support
- [ ] Advanced audit logging
- [ ] Custom AI model fine-tuning
- [ ] API rate limiting per workspace
- [ ] Webhook notifications for campaign events
