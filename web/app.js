let bridge = null;
let state = {};
let tempHistory = [];
let humHistory = [];
let lightHistory = [];
let currentExpression = 'NORMAL';
let waitingForAI = false;
let lastHistoryCount = -1;
let aiSafetyTimeout = null;

// Variables de animación fluida del avatar
let animTick = 0;
let isBlinking = false;
let blinkTimer = 0;
let nextBlinkIn = 160;
let gazeOffsetX = 0;
let gazeOffsetY = 0;
let gazeTimer = 0;
let nextGazeIn = 220;

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
  
  // 1. Actualizar Tarjetas y Textos Principales
  if ($('tempValue')) $('tempValue').textContent = formatNum(state.temperature);
  if ($('humValue')) $('humValue').textContent = formatNum(state.humidity);
  if ($('comfortValue')) $('comfortValue').textContent = state.comfort == null ? '—' : String(state.comfort);
  if ($('lightValue')) $('lightValue').textContent = formatNum(state.light, 0);
  
  if ($('tempStatus')) $('tempStatus').textContent = `● ${state.temp_status || 'Sin lectura'}`;
  if ($('humStatus')) $('humStatus').textContent = `● ${state.hum_status || 'Sin lectura'}`;
  if ($('comfortStatus')) $('comfortStatus').textContent = `● ${state.comfort_status || 'Sin lectura'}`;
  if ($('lightStatus')) $('lightStatus').textContent = state.light == null ? '● Sin lectura' : '● Lectura activa';
  
  setStatusColor($('tempStatus'), state.temp_color);
  setStatusColor($('humStatus'), state.hum_color);
  setStatusColor($('comfortStatus'), '#a5b98a');
  setStatusColor($('lightStatus'), '#a5b98a');
  
  if ($('sampleCount')) $('sampleCount').textContent = `${state.sample_count || 0} muestras`;
  if ($('portInfo')) $('portInfo').textContent = `Puerto: ${state.port || '—'} · ${state.baudrate || '—'} baudios`;
  if ($('footerPort')) $('footerPort').textContent = `Puerto: ${state.port || '—'} · Baudios: ${state.baudrate || '—'}`;
  
  const online = !!state.connected || !!state.demo;
  if ($('connectionText')) $('connectionText').textContent = state.connected ? 'Conectado' : state.demo ? 'Demo activa' : 'Desconectado';
  if ($('connectionChip')) $('connectionChip').querySelector('.dot').style.background = online ? '#a5b98a' : '#c45c5c';
  if ($('readyText')) $('readyText').textContent = state.connected ? 'HARDWARE CONECTADO' : state.demo ? 'SIMULACIÓN ACTIVA' : 'MONITOREO LISTO';
  if ($('footerStatus')) $('footerStatus').textContent = state.paused ? 'SIMA 2.0 · Tiempo pausado' : 'SIMA 2.0 Activo — Monitoreo dinámico en tiempo real.';
  if ($('userName')) $('userName').textContent = state.user || 'Administrador';

  // 2. Feedback Visual del Botón Modo Demo y Conexión
  const demoBtn = document.querySelector('[data-action="demo"]');
  if (demoBtn) {
    if (state.demo) {
      demoBtn.textContent = '⏹ Detener Demo';
      demoBtn.classList.add('active-demo');
    } else {
      demoBtn.textContent = 'Modo Demo';
      demoBtn.classList.remove('active-demo');
    }
  }

  const connBtn = document.querySelector('[data-action="connect"]');
  if (connBtn) {
    connBtn.textContent = state.connected ? 'Desconectar' : 'Conectar Serial';
  }

  // 3. Acumulación Histórica para Gráficas
  if (state.temperature != null) {
    tempHistory.push(Number(state.temperature));
    if (tempHistory.length > 50) tempHistory.shift();
  }
  if (state.humidity != null) {
    humHistory.push(Number(state.humidity));
    if (humHistory.length > 50) humHistory.shift();
  }
  if (state.light != null) {
    lightHistory.push(Number(state.light));
    if (lightHistory.length > 50) lightHistory.shift();
  }

  drawCharts();

  const count = Number(state.sample_count || 0);
  if (count > lastHistoryCount) {
    if (count > 0) appendHistory();
    lastHistoryCount = count;
  }
}

function appendHistory() {
  if (state.temperature == null && state.humidity == null) return;
  const list = $('historyList');
  if (!list) return;
  const empty = list.querySelector('.empty-state');
  if (empty) empty.remove();
  const now = new Date();
  const entry = document.createElement('div');
  entry.className = 'history-entry';
  entry.innerHTML = `<div><div class="history-main"><strong>${formatNum(state.temperature)}°C</strong> · ${formatNum(state.humidity)}% RH</div><div class="history-time">${now.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'})}</div></div><div class="history-side"><small>${state.comfort == null ? '—' : state.comfort + ' pts'}</small></div>`;
  list.prepend(entry);
  while (list.children.length > 10) list.removeChild(list.lastChild);
}

// ═════════════════════════════════════════════════════════════════════
//  RENDERIZADO AVANZADO DE GRÁFICAS ENMARCADAS CON EJE Y Y LEYENDAS
// ═════════════════════════════════════════════════════════════════════
function drawSingleChart(canvas, values, minVal, maxVal, lineColor, fillColor) {
  if (!canvas) return;
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const w = Math.max(150, Math.floor(rect.width));
  const h = Math.max(70, Math.floor(rect.height));

  canvas.width = Math.floor(w * dpr);
  canvas.height = Math.floor(h * dpr);

  const ctx = canvas.getContext('2d');
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);

  const paddingLeft = 32;
  const paddingRight = 12;
  const paddingTop = 10;
  const paddingBottom = 16;

  const plotW = w - paddingLeft - paddingRight;
  const plotH = h - paddingTop - paddingBottom;

  ctx.strokeStyle = 'rgba(151,160,144,0.12)';
  ctx.lineWidth = 1;
  ctx.fillStyle = 'rgba(150,152,144,0.7)';
  ctx.font = '9px system-ui, sans-serif';
  ctx.textAlign = 'right';
  ctx.textBaseline = 'middle';

  const steps = 3;
  const range = Math.max(0.5, maxVal - minVal);

  for (let i = 0; i <= steps; i++) {
    const ratio = i / steps;
    const y = paddingTop + plotH * (1 - ratio);
    const val = minVal + ratio * range;

    ctx.beginPath();
    ctx.moveTo(paddingLeft, y);
    ctx.lineTo(w - paddingRight, y);
    ctx.stroke();

    ctx.fillText(val.toFixed(1), paddingLeft - 4, y);
  }

  const valid = values.filter(v => v != null && Number.isFinite(v));
  if (valid.length < 2) return;

  const pts = values.map((v, i) => {
    if (v == null) return null;
    const x = paddingLeft + (i / (values.length - 1)) * plotW;
    const y = paddingTop + plotH - ((v - minVal) / range) * plotH;
    return [x, clamp(y, paddingTop + 2, paddingTop + plotH - 2)];
  }).filter(Boolean);

  if (pts.length < 2) return;

  const grad = ctx.createLinearGradient(0, paddingTop, 0, paddingTop + plotH);
  grad.addColorStop(0, fillColor || 'rgba(165,185,138,0.22)');
  grad.addColorStop(1, 'rgba(0,0,0,0)');

  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) {
    const xc = (pts[i - 1][0] + pts[i][0]) / 2;
    const yc = (pts[i - 1][1] + pts[i][1]) / 2;
    ctx.quadraticCurveTo(pts[i - 1][0], pts[i - 1][1], xc, yc);
  }
  ctx.lineTo(pts[pts.length - 1][0], pts[pts.length - 1][1]);
  ctx.lineTo(pts[pts.length - 1][0], paddingTop + plotH);
  ctx.lineTo(pts[0][0], paddingTop + plotH);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) {
    const xc = (pts[i - 1][0] + pts[i][0]) / 2;
    const yc = (pts[i - 1][1] + pts[i][1]) / 2;
    ctx.quadraticCurveTo(pts[i - 1][0], pts[i - 1][1], xc, yc);
  }
  ctx.lineTo(pts[pts.length - 1][0], pts[pts.length - 1][1]);
  ctx.strokeStyle = lineColor;
  ctx.lineWidth = 2.2;
  ctx.shadowColor = lineColor;
  ctx.shadowBlur = 6;
  ctx.stroke();
  ctx.shadowBlur = 0;

  const lastPt = pts[pts.length - 1];
  ctx.beginPath();
  ctx.arc(lastPt[0], lastPt[1], 4, 0, Math.PI * 2);
  ctx.fillStyle = '#ffffff';
  ctx.fill();
  ctx.strokeStyle = lineColor;
  ctx.lineWidth = 2;
  ctx.stroke();
}

function drawCharts() {
  const tempValid = tempHistory.filter(v => v != null);
  const humValid = humHistory.filter(v => v != null);

  if (tempValid.length) {
    const tMin = Math.min(...tempValid);
    const tMax = Math.max(...tempValid);
    const tAvg = tempValid.reduce((a, b) => a + b, 0) / tempValid.length;
    const tCur = tempValid[tempValid.length - 1];

    if ($('tempMin')) $('tempMin').textContent = tMin.toFixed(1);
    if ($('tempMax')) $('tempMax').textContent = tMax.toFixed(1);
    if ($('tempAvg')) $('tempAvg').textContent = tAvg.toFixed(1);
    if ($('tempLivePill')) $('tempLivePill').textContent = `${tCur.toFixed(1)} °C`;

    const spanMin = Math.floor(tMin - 1);
    const spanMax = Math.ceil(tMax + 1);
    drawSingleChart($('tempChart'), tempHistory, spanMin, spanMax, '#a5b98a', 'rgba(165,185,138,0.25)');
  } else {
    drawSingleChart($('tempChart'), [20, 22, 21, 23], 18, 26, '#a5b98a', 'rgba(165,185,138,0.1)');
  }

  if (humValid.length) {
    const hMin = Math.min(...humValid);
    const hMax = Math.max(...humValid);
    const hAvg = humValid.reduce((a, b) => a + b, 0) / humValid.length;
    const hCur = humValid[humValid.length - 1];

    if ($('humMin')) $('humMin').textContent = hMin.toFixed(1);
    if ($('humMax')) $('humMax').textContent = hMax.toFixed(1);
    if ($('humAvg')) $('humAvg').textContent = hAvg.toFixed(1);
    if ($('humLivePill')) $('humLivePill').textContent = `${hCur.toFixed(1)} %`;

    const spanMin = Math.max(0, Math.floor(hMin - 3));
    const spanMax = Math.min(100, Math.ceil(hMax + 3));
    drawSingleChart($('humChart'), humHistory, spanMin, spanMax, '#82b4d2', 'rgba(130,180,210,0.25)');
  } else {
    drawSingleChart($('humChart'), [45, 48, 50, 47], 35, 65, '#82b4d2', 'rgba(130,180,210,0.1)');
  }
}

// ═════════════════════════════════════════════════════════════════════
//  MATRIZ CIRCULAR 20x20 PARA QUE LA IA LLENE EL ORBE COMPLETO
// ═════════════════════════════════════════════════════════════════════

function create20x20Matrix() {
  const cols = 20, rows = 20;
  return Array.from({ length: rows }, () => Array(cols).fill(0));
}

function computePixelFaceMatrix() {
  const m = create20x20Matrix();
  const expr = currentExpression;

  let eyeMode = 'open';
  if (isBlinking) {
    eyeMode = 'blink';
  } else if (expr === 'HAPPY' || expr === 'LOVE') {
    eyeMode = 'happy';
  } else if (expr === 'SLEEPY') {
    eyeMode = 'sleepy';
  } else if (expr === 'SURPRISED') {
    eyeMode = 'surprised';
  } else if (expr === 'THINKING') {
    eyeMode = 'think';
  } else if (expr === 'ALERT' || expr === 'WARN') {
    eyeMode = 'alert';
  }

  // Ojos centrados proporcionalmente en la matriz 20x20 (filas 6..9)
  const leftEyeX = clamp(4 + gazeOffsetX, 2, 6);
  const rightEyeX = clamp(13 + gazeOffsetX, 11, 15);
  const eyeY = clamp(7 + gazeOffsetY, 5, 9);

  const drawEye = (ox, oy, mode) => {
    let shape = [
      [1, 1, 1, 1],
      [1, 2, 2, 1],
      [1, 2, 2, 1],
      [1, 1, 1, 1]
    ];
    if (mode === 'blink') {
      shape = [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0]
      ];
    } else if (mode === 'happy') {
      shape = [
        [0, 1, 1, 0],
        [1, 0, 0, 1],
        [0, 0, 0, 0]
      ];
    } else if (mode === 'sleepy') {
      shape = [
        [1, 1, 1, 1],
        [0, 0, 0, 0]
      ];
    } else if (mode === 'surprised') {
      shape = [
        [1, 1, 1, 1],
        [1, 2, 2, 1],
        [1, 2, 2, 1],
        [1, 1, 1, 1]
      ];
    } else if (mode === 'think') {
      shape = [
        [0, 1, 1, 0],
        [1, 2, 2, 1],
        [0, 1, 1, 0]
      ];
    } else if (mode === 'alert') {
      shape = [
        [1, 3, 3, 1],
        [3, 2, 2, 3],
        [1, 3, 3, 1]
      ];
    }

    shape.forEach((row, ry) => {
      row.forEach((val, rx) => {
        const targetY = oy + ry;
        const targetX = ox + rx;
        if (m[targetY] && m[targetY][targetX] !== undefined) {
          m[targetY][targetX] = val;
        }
      });
    });
  };

  drawEye(leftEyeX, eyeY, eyeMode);
  drawEye(rightEyeX, eyeY, eyeMode);

  // Rubor / Mejillas LED suaves en filas 11..12
  m[11][3] = 1; m[11][4] = 1; m[11][15] = 1; m[11][16] = 1;

  // Boca o indicador de voz según estado
  const mouthY = 14;
  if (expr === 'TALKING') {
    const talkCycle = Math.floor(animTick / 5) % 3;
    if (talkCycle === 0) {
      [[9, mouthY], [10, mouthY]].forEach(([x, y]) => { if (m[y]) m[y][x] = 1; });
    } else if (talkCycle === 1) {
      [[8, mouthY], [9, mouthY], [10, mouthY], [11, mouthY]].forEach(([x, y]) => { if (m[y]) m[y][x] = 1; });
    } else {
      [[9, mouthY - 1], [10, mouthY - 1], [8, mouthY], [9, mouthY], [10, mouthY], [11, mouthY], [9, mouthY + 1], [10, mouthY + 1]].forEach(([x, y]) => { if (m[y]) m[y][x] = 1; });
    }
  } else if (expr === 'HAPPY') {
    [[7, mouthY], [8, mouthY + 1], [9, mouthY + 1], [10, mouthY + 1], [11, mouthY + 1], [12, mouthY]].forEach(([x, y]) => { if (m[y]) m[y][x] = 1; });
  } else if (expr === 'ALERT' || expr === 'WARN') {
    const alertVal = expr === 'ALERT' ? 3 : 2;
    [[9, mouthY], [10, mouthY], [9, mouthY + 1], [10, mouthY + 1]].forEach(([x, y]) => { if (m[y]) m[y][x] = alertVal; });
  } else {
    [[8, mouthY], [9, mouthY], [10, mouthY], [11, mouthY]].forEach(([x, y]) => { if (m[y]) m[y][x] = 1; });
  }

  return m;
}

let faceGridElements = [];

function buildPixelFaceDOM() {
  const face = $('pixelFace');
  if (!face) return;
  face.innerHTML = '';
  faceGridElements = [];

  for (let r = 0; r < 20; r++) {
    for (let c = 0; c < 20; c++) {
      const cell = document.createElement('span');
      // Máscara circular: apagar píxeles en esquinas fuera del círculo de radio 9.7
      const distSq = (r - 9.5) * (r - 9.5) + (c - 9.5) * (c - 9.5);
      if (distSq > 95) {
        cell.style.visibility = 'hidden';
      }
      cell.className = 'pixel';
      face.appendChild(cell);
      faceGridElements.push(cell);
    }
  }
}

function updatePixelFaceDOM() {
  if (!faceGridElements.length) buildPixelFaceDOM();
  const matrix = computePixelFaceMatrix();
  const flat = matrix.flat();

  for (let i = 0; i < flat.length; i++) {
    const cell = faceGridElements[i];
    if (!cell || cell.style.visibility === 'hidden') continue;
    const v = flat[i];
    if (v === 2) {
      cell.className = 'pixel white';
    } else if (v === 3) {
      cell.className = 'pixel danger';
    } else if (v === 1) {
      cell.className = 'pixel on';
    } else {
      cell.className = 'pixel';
    }
  }
}

function animLoop() {
  animTick++;

  blinkTimer++;
  if (blinkTimer >= nextBlinkIn) {
    isBlinking = true;
    if (blinkTimer >= nextBlinkIn + 12) {
      isBlinking = false;
      blinkTimer = 0;
      nextBlinkIn = Math.floor(130 + Math.random() * 180);
    }
  }

  gazeTimer++;
  if (gazeTimer >= nextGazeIn) {
    const rand = Math.random();
    if (rand < 0.35) gazeOffsetX = -1;
    else if (rand < 0.70) gazeOffsetX = 1;
    else gazeOffsetX = 0;
    
    gazeOffsetY = Math.random() < 0.25 ? -1 : 0;
    gazeTimer = 0;
    nextGazeIn = Math.floor(160 + Math.random() * 220);
  }

  updatePixelFaceDOM();
  requestAnimationFrame(animLoop);
}

function setExpression(expr) {
  currentExpression = String(expr || 'NORMAL').toUpperCase();
}

// ═════════════════════════════════════════════════════════════════════
//  INTERACCION DE CHAT Y ACCIONES DE FRONTEND (GARANTIZANDO RESPUESTA)
// ═════════════════════════════════════════════════════════════════════

function addMessage(text, user = false) {
  const messagesContainer = $('chatMessages');
  if (!messagesContainer) return;

  const wrap = document.createElement('div');
  wrap.className = `message-row ${user ? 'user' : ''}`;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.textContent = user ? '👤' : '⌁';

  const bubble = document.createElement('div');
  bubble.className = 'message-bubble';
  bubble.innerHTML = `${user ? safeText(text) : safeAIHtml(text)}<div class="message-meta">${new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</div>`;

  wrap.appendChild(avatar);
  wrap.appendChild(bubble);
  messagesContainer.appendChild(wrap);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function resetChatUI() {
  const messagesContainer = $('chatMessages');
  if (messagesContainer) messagesContainer.innerHTML = '';
  addMessage('Conversación reiniciada. ¿En qué puedo ayudarte hoy?', false);
  setExpression('NORMAL');
}

function handleAIResponsePayload(payloadRaw) {
  if (aiSafetyTimeout) { clearTimeout(aiSafetyTimeout); aiSafetyTimeout = null; }
  waitingForAI = false;

  if ($('sendBtn')) $('sendBtn').disabled = false;
  if ($('chatInput')) $('chatInput').disabled = false;
  if ($('chatInput')) $('chatInput').focus();

  let response = {};
  if (typeof payloadRaw === 'string') {
    try { response = JSON.parse(payloadRaw); } catch (e) { response = { response: payloadRaw }; }
  } else {
    response = payloadRaw || {};
  }

  // Ignorar mensajes de estado intermedio como 'Procesando...'
  if (response.response === 'Procesando con Google Gemini...' || response.response === 'Procesando consulta...') {
    return;
  }

  addMessage(response.response || 'El asistente ha procesado la consulta.', false);
  setExpression('TALKING');
  setTimeout(() => setExpression(response.expression_state || 'HAPPY'), 2200);
}

let isChannelConnecting = false;

function tryConnectQWebChannel() {
  if (window.bridge) {
    bridge = window.bridge;
    return;
  }
  if (isChannelConnecting) return;

  if (typeof QWebChannel !== 'undefined' && typeof qt !== 'undefined' && qt.webChannelTransport) {
    isChannelConnecting = true;
    try {
      new QWebChannel(qt.webChannelTransport, channel => {
        isChannelConnecting = false;
        if (channel && channel.objects && channel.objects.bridge) {
          bridge = channel.objects.bridge;
          window.bridge = bridge;

          if (bridge.state_changed) bridge.state_changed.connect(payload => updateState(JSON.parse(payload)));
          if (bridge.user_changed) bridge.user_changed.connect(payload => updateState(JSON.parse(payload)));
          if (bridge.ai_response) bridge.ai_response.connect(payload => handleAIResponsePayload(payload));

          if (bridge.get_snapshot) {
            bridge.get_snapshot(payload => updateState(JSON.parse(payload)));
          }
        }
      });
    } catch (e) {
      isChannelConnecting = false;
      console.error('[JS] QWebChannel error:', e);
    }
  }
}

const channelPoller = setInterval(() => {
  if (window.bridge) {
    clearInterval(channelPoller);
  } else {
    tryConnectQWebChannel();
  }
}, 50);

function sendPrompt(prompt) {
  const text = String(prompt || '').trim();
  if (!text || waitingForAI) return;

  addMessage(text, true);
  waitingForAI = true;
  if ($('sendBtn')) $('sendBtn').disabled = true;
  if ($('chatInput')) $('chatInput').disabled = true;
  setExpression('THINKING');

  aiSafetyTimeout = setTimeout(() => {
    if (waitingForAI) {
      waitingForAI = false;
      if ($('sendBtn')) $('sendBtn').disabled = false;
      if ($('chatInput')) $('chatInput').disabled = false;
      addMessage('La solicitud a Google Gemini superó el tiempo de espera. Por favor reintenta en un momento.', false);
      setExpression('NORMAL');
    }
  }, 45000);

  // Transmisión nativa e instantánea vía consola de QtWebEngine
  console.log('SIMA_PROMPT:' + text);
}

function wireActions() {
  document.querySelectorAll('[data-action]').forEach(btn => {
    btn.addEventListener('click', () => {
      const map = {
        connect: 'connect_serial',
        demo: 'toggle_demo',
        pause: 'toggle_pause',
        clear: 'clear_data',
        excel: 'export_excel',
        pdf: 'export_pdf',
        nn: 'open_neural_network',
        fullscreen: 'toggle_fullscreen',
        settings: 'open_settings',
        profile: 'open_profile'
      };
      const actionName = map[btn.dataset.action];
      if (actionName) {
        console.log('SIMA_ACTION:' + actionName);
      }
      tryConnectQWebChannel();
      if (bridge && actionName && typeof bridge[actionName] === 'function') {
        try { bridge[actionName](); } catch (e) {}
      }
    });
  });

  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      const targetPanel = tab.dataset.tab === 'monitor' ? 'monitorPanel' : 'assistantPanel';
      if ($(targetPanel)) $(targetPanel).classList.add('active');
    });
  });

  document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => sendPrompt(btn.dataset.quick));
  });

  if ($('sendBtn')) {
    $('sendBtn').addEventListener('click', () => {
      sendPrompt($('chatInput').value);
      $('chatInput').value = '';
    });
  }

  if ($('chatInput')) {
    $('chatInput').addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        sendPrompt(e.target.value);
        e.target.value = '';
      }
    });
  }

  if ($('resetChat')) {
    $('resetChat').addEventListener('click', () => {
      console.log('SIMA_ACTION:reset_chat');
      tryConnectQWebChannel();
      if (bridge && bridge.reset_chat) bridge.reset_chat();
      resetChatUI();
    });
  }

  window.addEventListener('resize', drawCharts);
}

let actionsWired = false;

function initAppShell() {
  if (!actionsWired) {
    actionsWired = true;
    wireActions();
    buildPixelFaceDOM();
    requestAnimationFrame(animLoop);
    addMessage('Hola. Soy SIMA. Puedo analizar tus datos ambientales y ayudarte a interpretarlos.', false);
  }

  tryConnectQWebChannel();
  // Reintentar conexión de canal por si el transport web de Qt tarda unos milisegundos más en inyectarse
  setTimeout(tryConnectQWebChannel, 100);
  setTimeout(tryConnectQWebChannel, 500);
  setTimeout(tryConnectQWebChannel, 1500);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAppShell);
} else {
  initAppShell();
}
