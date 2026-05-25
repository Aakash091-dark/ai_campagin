
(function(){
'use strict';

var messagesEl = document.getElementById('messages');
var inputEl    = document.getElementById('userInput');
var sendBtn    = document.getElementById('sendBtn');
var conversationId = null;
var isSending = false;

/* ----------------------------------------------------------
   HELPERS
---------------------------------------------------------- */
function esc(t){
  var d = document.createElement('div');
  d.textContent = String(t == null ? '' : t);
  return d.innerHTML;
}

function el(tag, css, html){
  var e = document.createElement(tag);
  if(css)  e.style.cssText = css;
  if(html) e.innerHTML = html;
  return e;
}

/* ----------------------------------------------------------
   OPENUI COMPONENTS
---------------------------------------------------------- */
function TextContent(text){
  var d = el('div','line-height:1.65;font-size:14px');
  d.innerHTML = esc(text)
    .replace(/[*][*]([^*]+)[*][*]/g,'<strong>$1</strong>')
    .replace(/\\n/g,'<br>');
  return d;
}

function Card(children){
  var d = el('div','display:flex;flex-direction:column;gap:10px');
  (children||[]).forEach(function(c){ if(c) d.appendChild(c); });
  return d;
}

function Alert(title, message, variant){
  var bg  = variant==='destructive'?'#3d1f1f':variant==='warning'?'#3d2f00':variant==='success'?'#1a4731':'#1f3d6e';
  var bdr = variant==='destructive'?'#f85149':variant==='warning'?'#d29922':variant==='success'?'#3fb950':'#388bfd';
  var d = el('div','padding:12px 16px;border-radius:10px;background:'+bg+';border:1px solid '+bdr+';margin:2px 0');
  d.innerHTML = '<strong style="display:block;margin-bottom:4px">'+esc(title||'')+'</strong>'
              + '<div style="font-size:13px;opacity:.9">'+esc(message||'')+'</div>';
  return d;
}

function Badge(label, variant){
  var bg = {default:'#30363d',success:'#1a4731',warning:'#3d2f00',destructive:'#3d1f1f',info:'#1f3d6e'};
  return el('span','display:inline-block;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;background:'+(bg[variant]||bg.default)+';color:#e6edf3', esc(label));
}

function Table(columns, rows){
  columns = columns||[]; rows = rows||[];
  var wrap = el('div','overflow-x:auto;margin:2px 0');
  var t = el('table','width:100%;border-collapse:collapse;font-size:13px');
  if(columns.length){
    var thead = document.createElement('thead');
    var hr = document.createElement('tr');
    columns.forEach(function(c){
      var th = el('th','padding:8px 12px;text-align:left;border-bottom:1px solid #30363d;color:#8b949e;font-weight:600;white-space:nowrap', esc(c));
      hr.appendChild(th);
    });
    thead.appendChild(hr); t.appendChild(thead);
  }
  var tbody = document.createElement('tbody');
  rows.forEach(function(row, ri){
    var tr = document.createElement('tr');
    tr.style.background = ri%2===0?'transparent':'rgba(255,255,255,0.025)';
    (row||[]).forEach(function(cell){
      var td = el('td','padding:8px 12px;border-bottom:1px solid #21262d;color:#e6edf3', esc(cell==null?'-':cell));
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  t.appendChild(tbody); wrap.appendChild(t);
  return wrap;
}

function Chart(type, data){
  data = data||{};
  var labels   = data.labels||[];
  var datasets = data.datasets||[];
  var wrap = el('div','background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:16px;margin:2px 0');
  if(!labels.length){ wrap.textContent='No chart data'; return wrap; }
  var ds = datasets[0]||{};
  var values = ds.data||[];
  var max = 1;
  values.forEach(function(v){ if(typeof v==='number' && v>max) max=v; });
  var lbl = el('div','font-size:12px;color:#8b949e;margin-bottom:12px', esc(ds.label||(type+' chart')));
  wrap.appendChild(lbl);
  var rows = el('div','display:flex;flex-direction:column;gap:6px');
  labels.forEach(function(label, i){
    var val = values[i]||0;
    var pct = max>0?Math.round((val/max)*100):0;
    var row = el('div','display:flex;align-items:center;gap:10px;font-size:12px');
    row.appendChild(el('span','width:130px;color:#8b949e;text-align:right;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap', esc(label)));
    var bw = el('div','flex:1;background:#21262d;border-radius:4px;height:16px;overflow:hidden');
    var bar = el('div','width:'+pct+'%;height:100%;background:#1f6feb;border-radius:4px');
    bw.appendChild(bar); row.appendChild(bw);
    row.appendChild(el('span','width:56px;color:#e6edf3;font-size:11px', esc(typeof val==='number'?val.toLocaleString():val)));
    rows.appendChild(row);
  });
  wrap.appendChild(rows);
  return wrap;
}

function Metric(label, value, sub){
  var d = el('div','background:#0d1117;border:1px solid #30363d;border-radius:10px;padding:14px 18px;display:flex;flex-direction:column;gap:4px');
  d.appendChild(el('div','font-size:12px;color:#8b949e', esc(label)));
  d.appendChild(el('div','font-size:22px;font-weight:700;color:#e6edf3', esc(value)));
  if(sub) d.appendChild(el('div','font-size:11px;color:#8b949e', esc(sub)));
  return d;
}

function MetricGrid(metrics){
  var g = el('div','display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px;margin:2px 0');
  (metrics||[]).forEach(function(m){ if(m) g.appendChild(m); });
  return g;
}

function Section(title, children){
  var d = el('div','display:flex;flex-direction:column;gap:8px');
  if(title) d.appendChild(el('div','font-size:12px;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:.05em', esc(title)));
  (children||[]).forEach(function(c){ if(c) d.appendChild(c); });
  return d;
}

function FollowUpItem(text){
  var btn = el('button','');
  btn.className = 'follow-btn';
  btn.textContent = text;
  btn.onclick = function(){ inputEl.value = text; sendMessage(); };
  return btn;
}

function FollowUpBlock(items){
  var d = el('div','');
  d.className = 'follow-ups';
  (items||[]).forEach(function(item){ if(item) d.appendChild(item); });
  return d;
}

/* ----------------------------------------------------------
   OPENUI PARSER
   Uses new Function with all components injected as args.
   Avoids template literals for wrapping so backticks in the
   response code never break the outer string.
---------------------------------------------------------- */
function isOpenUI(code){
  return typeof code === 'string' && code.indexOf('root =') !== -1;
}

function parseOpenUI(code){
  try{
    var fn = new Function(
      'TextContent','Card','Alert','Badge',
      'Table','Chart','Metric','MetricGrid','Section',
      'FollowUpItem','FollowUpBlock',
      code + '\nreturn root;'
    );
    return fn(
      TextContent, Card, Alert, Badge,
      Table, Chart, Metric, MetricGrid, Section,
      FollowUpItem, FollowUpBlock
    );
  }catch(err){
    console.error('OpenUI parse error:', err.message, '\\n', code);
    return null;
  }
}

/* ----------------------------------------------------------
   MESSAGE RENDERER
---------------------------------------------------------- */
function addMessage(role, content, meta){
  var wrap = el('div','');
  wrap.className = 'message ' + (role === 'error' ? 'error-msg' : role);

  if(role === 'assistant' && isOpenUI(content)){
    var rendered = parseOpenUI(content);
    if(rendered){
      wrap.appendChild(rendered);
    } else {
      // parse failed — show raw text so user sees something
      wrap.appendChild(el('div','white-space:pre-wrap;font-size:13px;color:#8b949e', esc(content)));
    }
  } else {
    wrap.textContent = content;
  }

  if(meta){
    var metaEl = el('div','');
    metaEl.className = 'meta';
    Object.keys(meta).forEach(function(k){
      metaEl.appendChild(el('span','', '<strong>'+esc(k)+':</strong> '+esc(meta[k])));
    });
    wrap.appendChild(metaEl);
  }

  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

/* ----------------------------------------------------------
   SEND
---------------------------------------------------------- */
function sendMessage(){
  var text = inputEl.value.trim();
  if(!text || isSending) return;

  isSending = true;
  sendBtn.disabled = true;
  inputEl.value = '';
  inputEl.style.height = 'auto';

  addMessage('user', text);

  fetch('/api/v1/ai/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer lemonmaxx-dev-token'
    },
    body: JSON.stringify({
      workspace_id: 1,
      message: text,
      conversation_id: conversationId
    })
  })
  .then(function(res){ return res.json(); })
  .then(function(data){
    conversationId = data.conversation_id;
    addMessage('assistant', data.openui_response, {
      Agent: data.agent_used,
      Time:  data.execution_time + 's',
      Tokens: data.tokens_used
    });
  })
  .catch(function(err){
    addMessage('error', 'Request failed: ' + err.message);
  })
  .finally(function(){
    isSending = false;
    sendBtn.disabled = false;
    inputEl.focus();
  });
}

/* ----------------------------------------------------------
   EVENTS
---------------------------------------------------------- */
sendBtn.addEventListener('click', sendMessage);

inputEl.addEventListener('keydown', function(e){
  if(e.key === 'Enter' && !e.shiftKey){
    e.preventDefault();
    sendMessage();
  }
});

inputEl.addEventListener('input', function(){
  this.style.height = 'auto';
  this.style.height = Math.min(this.scrollHeight, 140) + 'px';
});

inputEl.focus();

})();
