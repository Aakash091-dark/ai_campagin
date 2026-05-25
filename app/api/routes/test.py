# app/api/routes/test.py
# =========================================================
# TEMPORARY TEST ENDPOINT — bypasses auth for local testing
# =========================================================

import time
import uuid

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)

from app.core.orchestrator.graph import (
    run_ai_graph,
)


router = APIRouter()


# =========================================================
# TEST CHAT — no auth required
# =========================================================
@router.post("/chat")
async def test_chat(
    payload: ChatRequest,
):

    start_time = time.time()

    try:

        # =============================================
        # HARDCODED TEST USER
        # =============================================
        user_id = payload.user_id or 1

        conversation_id = (
            payload.conversation_id
            or str(uuid.uuid4())
        )

        # =============================================
        # RUN GRAPH (no memory / no DB for simplicity)
        # =============================================
        result = await run_ai_graph(
            workspace_id=payload.workspace_id,
            message=payload.message,
            conversation_id=conversation_id,
            user_id=user_id,
            memory_context=[],
        )

        execution_time = round(
            time.time() - start_time,
            2
        )

        return ChatResponse(
            success=result["success"],
            conversation_id=conversation_id,
            openui_response=result[
                "openui_response"
            ],
            execution_time=execution_time,
            agent_used=result[
                "selected_agent"
            ],
            tokens_used=result[
                "tokens_used"
            ],
        )

    except Exception as e:

        return {
            "success": False,
            "error": str(e),
            "execution_time": round(
                time.time() - start_time,
                2
            ),
        }


# =========================================================
# TEST UI PAGE
# =========================================================
TEST_UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Lemonmaxx AI — Test Chat</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f13;
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        header {
            padding: 18px 24px;
            background: #1a1a23;
            border-bottom: 1px solid #2a2a35;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        header h1 {
            font-size: 18px;
            font-weight: 600;
            letter-spacing: -0.3px;
        }
        header span {
            font-size: 12px;
            color: #888;
            background: #252533;
            padding: 3px 10px;
            border-radius: 6px;
        }
        .badge {
            margin-left: auto;
            display: flex;
            gap: 12px;
            align-items: center;
            font-size: 12px;
        }
        .badge .status {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: #44cc66;
            display: inline-block;
        }
        .container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        .sidebar {
            width: 280px;
            background: #14141d;
            border-right: 1px solid #2a2a35;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            flex-shrink: 0;
        }
        .sidebar label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #666;
        }
        .sidebar input,
        .sidebar select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #2a2a35;
            border-radius: 8px;
            background: #1a1a23;
            color: #e0e0e0;
            font-size: 13px;
            outline: none;
            transition: border-color .2s;
        }
        .sidebar input:focus,
        .sidebar select:focus {
            border-color: #6c5ce7;
        }
        .sidebar .hint {
            font-size: 11px;
            color: #555;
            line-height: 1.5;
        }
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        #messages {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .msg {
            max-width: 80%;
            padding: 14px 18px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .msg.user {
            background: #2d2d44;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }
        .msg.assistant {
            background: #1a1a2e;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
            border: 1px solid #2a2a44;
        }
        .msg .meta {
            font-size: 11px;
            color: #666;
            margin-top: 8px;
            display: flex;
            gap: 10px;
        }
        .msg .meta .agent {
            color: #6c5ce7;
        }
        .msg.error {
            background: #2e1a1a;
            border-color: #442a2a;
            color: #ff6666;
        }
        .typing {
            align-self: flex-start;
            padding: 14px 18px;
            background: #1a1a2e;
            border-radius: 12px;
            border: 1px solid #2a2a44;
            display: none;
            gap: 4px;
        }
        .typing span {
            width: 8px; height: 8px;
            background: #6c5ce7;
            border-radius: 50%;
            animation: bounce 1.2s infinite;
        }
        .typing span:nth-child(2) { animation-delay: .2s; }
        .typing span:nth-child(3) { animation-delay: .4s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: translateY(0); opacity: .4; }
            40% { transform: translateY(-8px); opacity: 1; }
        }
        .input-area {
            padding: 16px 24px;
            border-top: 1px solid #2a2a35;
            background: #1a1a23;
            display: flex;
            gap: 12px;
        }
        .input-area textarea {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #2a2a35;
            border-radius: 10px;
            background: #14141d;
            color: #e0e0e0;
            font-size: 14px;
            font-family: inherit;
            resize: none;
            outline: none;
            min-height: 48px;
            max-height: 120px;
            transition: border-color .2s;
        }
        .input-area textarea:focus {
            border-color: #6c5ce7;
        }
        .input-area button {
            padding: 12px 24px;
            background: #6c5ce7;
            color: #fff;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background .2s, transform .1s;
            align-self: flex-end;
        }
        .input-area button:hover {
            background: #5a4bd1;
        }
        .input-area button:active {
            transform: scale(.97);
        }
        .input-area button:disabled {
            opacity: .5;
            cursor: not-allowed;
        }
        .stats {
            padding: 8px 24px;
            background: #14141d;
            border-top: 1px solid #2a2a35;
            display: flex;
            gap: 20px;
            font-size: 11px;
            color: #555;
        }
        .stats strong {
            color: #888;
        }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #2a2a35; border-radius: 3px; }
        @media (max-width: 768px) {
            .sidebar { display: none; }
        }
    </style>
</head>
<body>

<header>
    <h1>&#9889; Lemonmaxx AI</h1>
    <span>Test Interface</span>
    <div class="badge">
        <span class="status"></span>
        <span id="statusText">Ready</span>
    </div>
</header>

<div class="container">
    <div class="sidebar">
        <label>Workspace ID</label>
        <input type="number" id="workspaceId" value="1" min="1" />
        <label>User ID</label>
        <input type="number" id="userId" value="1" min="1" />
        <label>Conversation</label>
        <select id="conversationMode">
            <option value="new">New conversation (auto)</option>
            <option value="persist">Persist (same session)</option>
        </select>
        <div class="hint">
            All requests use the dev token & skip auth middleware.<br />
            Memory / DB writes are bypassed in test mode.
        </div>
        <button id="clearBtn" style="margin-top:auto;padding:10px;background:#2a2a35;border:1px solid #3a3a45;border-radius:8px;color:#ccc;cursor:pointer;font-size:13px;">Clear Chat</button>
    </div>

    <div class="main">
        <div id="messages">
            <div class="msg assistant">
                Hello! I'm the Lemonmaxx AI test interface. Send a message to test any agent.<br/>
                <em style="font-size:12px;color:#666;">Try: "show analytics", "pause campaign 5", "automation rules", "rejected ads", "generate report"</em>
            </div>
        </div>

        <div class="typing" id="typing">
            <span></span><span></span><span></span>
        </div>

        <div class="input-area">
            <textarea id="userInput" rows="1" placeholder="Type a message to test the AI..."
                onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendMessage()}"></textarea>
            <button id="sendBtn" onclick="sendMessage()">Send</button>
        </div>

        <div class="stats">
            <span>Agent: <strong id="lastAgent">—</strong></span>
            <span>Tokens: <strong id="lastTokens">—</strong></span>
            <span>Time: <strong id="lastTime">—</strong></span>
            <span>Conversation: <strong id="convId">—</strong></span>
        </div>
    </div>
</div>

<script>
let conversationId = null;
let isSending = false;

function getConfig() {
    return {
        workspace_id: parseInt(document.getElementById('workspaceId').value) || 1,
        user_id: parseInt(document.getElementById('userId').value) || 1,
        persist: document.getElementById('conversationMode').value === 'persist',
    };
}

function setStatus(text, ok) {
    document.getElementById('statusText').textContent = text;
    const dot = document.querySelector('.badge .status');
    dot.style.background = ok !== false ? '#44cc66' : '#ff4444';
}

function addMessage(role, content, meta) {
    const el = document.createElement('div');
    el.className = 'msg ' + role;
    let html = content;
    if (meta) {
        html += '<div class="meta">';
        if (meta.agent) html += '<span class="agent">' + meta.agent + '</span>';
        if (meta.tokens !== undefined) html += '<span>' + meta.tokens + ' tokens</span>';
        if (meta.time !== undefined) html += '<span>' + meta.time + 's</span>';
        html += '</div>';
    }
    el.innerHTML = html;
    document.getElementById('messages').appendChild(el);
    el.scrollIntoView({ behavior: 'smooth' });
}

function showTyping(show) {
    document.getElementById('typing').style.display = show ? 'flex' : 'none';
}

async function sendMessage() {
    if (isSending) return;

    const input = document.getElementById('userInput');
    const message = input.value.trim();
    if (!message) return;

    const config = getConfig();

    // reset conversation ID if new mode
    if (!config.persist) {
        conversationId = null;
    }

    const payload = {
        workspace_id: config.workspace_id,
        message: message,
        conversation_id: conversationId || null,
        user_id: config.user_id,
    };

    // clear input
    input.value = '';
    input.style.height = 'auto';

    addMessage('user', message);
    showTyping(true);
    setStatus('Thinking...', true);
    isSending = true;
    document.getElementById('sendBtn').disabled = true;

    try {
        const res = await fetch('/api/v1/test/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        const data = await res.json();

        if (!data.success) {
            addMessage('assistant', '&#10060; Error: ' + (data.error || 'Unknown error'), { agent: 'error' });
            setStatus('Error', false);
            return;
        }

        // store conversation ID
        conversationId = data.conversation_id;

        addMessage('assistant', data.openui_response, {
            agent: data.agent_used || 'general',
            tokens: data.tokens_used,
            time: data.execution_time,
        });

        document.getElementById('lastAgent').textContent = data.agent_used || 'general';
        document.getElementById('lastTokens').textContent = data.tokens_used ?? '—';
        document.getElementById('lastTime').textContent = data.execution_time ? data.execution_time + 's' : '—';
        document.getElementById('convId').textContent = data.conversation_id
            ? data.conversation_id.substring(0, 12) + '...'
            : '—';

        setStatus('Ready', true);

    } catch (err) {
        addMessage('assistant', '&#10060; Network error: ' + err.message, { agent: 'error' });
        setStatus('Offline', false);
    } finally {
        showTyping(false);
        isSending = false;
        document.getElementById('sendBtn').disabled = false;
    }
}

// auto-resize textarea
document.getElementById('userInput').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// clear chat
document.getElementById('clearBtn').addEventListener('click', function() {
    const msgs = document.getElementById('messages');
    msgs.innerHTML = '<div class="msg assistant">Chat cleared. Start a new test.</div>';
    conversationId = null;
    document.getElementById('lastAgent').textContent = '—';
    document.getElementById('lastTokens').textContent = '—';
    document.getElementById('lastTime').textContent = '—';
    document.getElementById('convId').textContent = '—';
    setStatus('Ready', true);
});
</script>
</body>
</html>
"""


@router.get("/ui", response_class=HTMLResponse)
async def test_ui():
    return TEST_UI_HTML