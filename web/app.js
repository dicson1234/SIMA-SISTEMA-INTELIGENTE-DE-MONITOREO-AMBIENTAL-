let bridge = null;
let state = {};
let tempHistory = [];
let humHistory = [];
let lightHistory = [];
let currentExpression = 'NORMAL';
let waitingForAI = false;
let lastHistoryCount = -1;

const $ = (id) => document.getElementById(id);
const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

function safeText(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}

function safeAIHtml(value) {
  const escaped = safeText(value);
  return escaped.replace(/&lt;br\s*\/??&gt;/gi, '<br>').replace(/&lt;b&gt;(.*?)&lt;\/b&gt;/gis, '<b>$1</b>').replace(/&lt;strong&gt;(.*?)&lt;\/strong&gt;/gis, '<strong>$1</strong>');
}

function formatNum(value, digits=1) {
  return value === null || value === undefined ? '—' : Number(value).toFixed(digits);
}

function setStatusColor(el, color) {
  if (!el || !color) return;
  const safe = /^#[0-9a-f]{6}$/i.test(color) ? color : '#a5b98a';
  el.style.color = safe;
}

function updateState(next) {
  state = next || {};
  $('tempValue').textContent = formatNum(state.temperature);
  $('humValue').textContent = formatNum(state.humidity);
  $('comfortValue').textContent = state.comfort == null ? '—' : String(state.comfort);
  $('lightValue').textContent = formatNum(state.light, 0);
  $('tempStatus').textContent = `● ${state.temp_status || 'Sin lectura'}`;
  $('humStatus').textContent = `● ${state.hum_status || 'Sin lectura'}`;
  $('comfortStatus').textContent = `● ${state.comfort_status || 'Sin lectura'}`;
  $('lightStatus').textContent = state.light == null ? '● Sin lectura' : '● Lectura activa';
  setStatusColor($('tempStatus'), state.temp_color); setStatusColor($('humStatus'), state.hum_color); setStatusColor($('comfortStatus'), '#a5b98a'); setStatusColor($('lightStatus'), '#a5b98a');
  $('sampleCount').textContent = `${state.sample_count || 0} muestras`;
  $('portInfo').textContent = `Puerto: ${state.port || '—'} · ${state.baudrate || '—'} baudios`;
  $('footerPort').textContent = `Puerto: ${state.port || '—'} · Baudios: ${state.baudrate || '—'}`;
  const online = !!state.connected || !!state.demo;
  $('connectionText').textContent = state.connected ? 'Conectado' : state.demo ? 'Demo activa' : 'Desconectado';
  $('connectionChip').querySelector('.dot').style.background = online ? '#a5b98a' : '#c45c5c';
  $('readyText').textContent = state.connected ? 'HARDWARE CONECTADO' : state.demo ? 'SIMULACIÓN ACTIVA' : 'MONITOREO LISTO';
  $('footerStatus').textContent = state.paused ? 'SIMA 2.0 · Tiempo pausado' : 'SIMA 2.0 Activo — Monitoreo dinámico en tiempo real.';
  $('userName').textContent = state.user || 'Administrador';

  tempHistory.push(state.temperature == null ? null : Number(state.temperature));
  humHistory.push(state.humidity == null ? null : Number(state.humidity));
  lightHistory.push(state.light == null ? null : Number(state.light));
  if (tempHistory.length > 48) tempHistory.shift(); if (humHistory.length > 48) humHistory.shift(); if (lightHistory.length > 48) lightHistory.shift();
  drawCharts();

  const count = Number(state.sample_count || 0);
  if (count > lastHistoryCount) { if (count > 0) appendHistory(); lastHistoryCount = count; }
}

function appendHistory() {
  if (state.temperature == null && state.humidity == null) return;
  const list = $('historyList');
  const empty = list.querySelector('.empty-state'); if (empty) empty.remove();
  const now = new Date();
  const entry = document.createElement('div'); entry.className = 'history-entry';
  entry.innerHTML = `<div><div class="history-main"><strong>${formatNum(state.temperature)}°C</strong> · ${formatNum(state.humidity)}% RH</div><div class="history-time">${now.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'})}</div></div><div class="history-side"><small>${state.comfort == null ? '—' : state.comfort + ' pts'}</small></div>`;
  list.prepend(entry); while (list.children.length > 8) list.removeChild(list.lastChild);
}

function drawSingleChart(canvas, values, min, max, lineColor) {
  const rect = canvas.getBoundingClientRect(); const dpr = window.devicePixelRatio || 1; const w = Math.max(120, Math.floor(rect.width)); const h = Math.max(72, Math.floor(rect.height));
  canvas.width = Math.floor(w*dpr); canvas.height = Math.floor(h*dpr); const ctx = canvas.getContext('2d'); ctx.scale(dpr, dpr); ctx.clearRect(0,0,w,h);
  ctx.strokeStyle = 'rgba(151,160,144,.08)'; ctx.lineWidth = 1;
  for (let i=1;i<4;i++){const y=(h*i)/4;ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
  const valid=values.filter(v=>v!=null&&Number.isFinite(v)); if(!valid.length)return; const range=Math.max(.1,max-min);
  const pts=values.map((v,i)=>{if(v==null)return null;const x=values.length===1?w/2:(i/(values.length-1))*w;const y=h-((v-min)/range)*h;return[x,clamp(y,2,h-2)];}).filter(Boolean); if(pts.length<2)return;
  const grad=ctx.createLinearGradient(0,0,0,h);grad.addColorStop(0,'rgba(165,185,138,.14)');grad.addColorStop(1,'rgba(0,0,0,0)');ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.lineTo(pts[pts.length-1][0],h);ctx.lineTo(pts[0][0],h);ctx.closePath();ctx.fillStyle=grad;ctx.fill();
  ctx.beginPath();pts.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.strokeStyle=lineColor;ctx.lineWidth=2;ctx.stroke();
}
function drawCharts(){const temp=tempHistory.filter(v=>v!=null);const tMin=temp.length?Math.min(...temp)-1:20;const tMax=temp.length?Math.max(...temp)+1:30;drawSingleChart($('tempChart'),tempHistory,tMin,tMax,'rgba(165,185,138,1)');drawSingleChart($('humChart'),humHistory,0,100,'rgba(130,147,107,1)');}

function pixelMatrixFor(expression){
  const cols=20,rows=12,m=Array.from({length:rows},()=>Array(cols).fill(0));
  const eye=(ox,oy,mode='open')=>{const points={open:[[1,1,1,1],[1,2,2,1],[1,1,1,1]],happy:[[0,1,1,0],[1,0,0,1],[0,0,0,0]],sleepy:[[1,1,1,1],[0,0,0,0]],surprised:[[1,1,1,1],[1,2,2,1],[1,2,2,1],[1,1,1,1]],wink:[[1,1,1,1]],think:[[0,1,1,0],[1,1,1,1],[0,1,1,0]]}[mode]||[[1,1,1,1],[1,2,2,1],[1,1,1,1]];points.forEach((row,ry)=>row.forEach((v,rx)=>{if(m[oy+ry]&&m[oy+ry][ox+rx]!==undefined)m[oy+ry][ox+rx]=v;}));};
  const mode=expression==='HAPPY'||expression==='LOVE'?'happy':expression==='SLEEPY'?'sleepy':expression==='SURPRISED'?'surprised':expression==='WINK'?'wink':expression==='THINKING'?'think':'open';
  eye(4,4,mode);eye(13,4,expression==='WINK'?'wink':mode);
  if(expression==='ALERT'||expression==='WARN'){for(let y=3;y<9;y++){m[y][9]=1;m[y][10]=1}if(expression==='ALERT'){m[8][9]=2;m[8][10]=2}}
  if(expression==='TALKING')[[9,9],[10,9],[8,10],[9,10],[10,10],[11,10]].forEach(([x,y])=>m[y][x]=1);else[[9,9],[10,9],[9,10],[10,10]].forEach(([x,y])=>m[y][x]=1);
  return m;
}
function renderPixelFace(){const face=$('pixelFace');if(!face)return;face.innerHTML='';pixelMatrixFor(currentExpression).flat().forEach(v=>{const cell=document.createElement('span');cell.className=v===2?'pixel white':v===1?'pixel on':'pixel';face.appendChild(cell);});}
function setExpression(expr){currentExpression=String(expr||'NORMAL').toUpperCase();renderPixelFace();}

function addMessage(text,user=false){const wrap=document.createElement('div');wrap.className=`message-row ${user?'user':''}`;const avatar=document.createElement('div');avatar.className='message-avatar';avatar.textContent=user?'●':'⌁';const bubble=document.createElement('div');bubble.className='message-bubble';bubble.innerHTML=`${user?safeText(text):safeAIHtml(text)}<div class="message-meta">${new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</div>`;wrap.appendChild(avatar);wrap.appendChild(bubble);$('chatMessages').appendChild(wrap);$('chatMessages').scrollTop=$('chatMessages').scrollHeight;}
function resetChatUI(){$('chatMessages').innerHTML='';addMessage('Conversación reiniciada. ¿En qué puedo ayudarte hoy?',false);setExpression('NORMAL');}
function sendPrompt(prompt){const text=String(prompt||'').trim();if(!text||!bridge||waitingForAI)return;addMessage(text,true);waitingForAI=true;$('sendBtn').disabled=true;$('chatInput').disabled=true;setExpression('THINKING');bridge.send_message(text);}

function wireActions(){
  document.querySelectorAll('[data-action]').forEach(btn=>btn.addEventListener('click',()=>{if(!bridge)return;const map={connect:'connect_serial',demo:'toggle_demo',pause:'toggle_pause',clear:'clear_data',excel:'export_excel',pdf:'export_pdf',nn:'open_neural_network',fullscreen:'toggle_fullscreen',settings:'open_settings',profile:'open_profile'};const method=map[btn.dataset.action];if(method&&typeof bridge[method]==='function')bridge[method]();}));
  document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));tab.classList.add('active');$(tab.dataset.tab==='monitor'?'monitorPanel':'assistantPanel').classList.add('active');}));
  document.querySelectorAll('.quick-btn').forEach(btn=>btn.addEventListener('click',()=>sendPrompt(btn.dataset.quick)));
  $('sendBtn').addEventListener('click',()=>{sendPrompt($('chatInput').value);$('chatInput').value='';});
  $('chatInput').addEventListener('keydown',e=>{if(e.key==='Enter'){sendPrompt(e.target.value);e.target.value='';}});
  $('resetChat').addEventListener('click',()=>{if(bridge)bridge.reset_chat();resetChatUI();});
  window.addEventListener('resize',drawCharts);
}

new QWebChannel(qt.webChannelTransport,channel=>{
  bridge=channel.objects.bridge;
  bridge.state_changed.connect(payload=>updateState(JSON.parse(payload)));
  bridge.user_changed.connect(payload=>updateState(JSON.parse(payload)));
  bridge.ai_response.connect(payload=>{let response={};try{response=JSON.parse(payload);}catch(e){response={response:'No pude interpretar la respuesta del asistente.',expression_state:'WARN'};}waitingForAI=false;$('sendBtn').disabled=false;$('chatInput').disabled=false;$('chatInput').focus();addMessage(response.response||'Sin respuesta.',false);setExpression('TALKING');setTimeout(()=>setExpression(response.expression_state||'HAPPY'),1200);});
  wireActions();renderPixelFace();addMessage('Hola. Soy SIMA. Puedo analizar tus datos ambientales y ayudarte a interpretarlos.',false);
  bridge.get_snapshot(payload=>updateState(JSON.parse(payload)));
});
