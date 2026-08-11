/**
 * Joy-Con (L) Locomotion System & Feasibility Test Harness
 */

// State & Config
const state = {
  connected: false,
  device: null,
  packetCounter: 0,
  isSimulator: false,
  simulatorMode: null,
  mode: 'normal',
  
  params: {
    sensThreshold: 0.45,
    runSpmThreshold: 140,
    silentAngleThreshold: 12,
    filterAlpha: 0.2
  },

  motion: {
    status: 'STOP',
    speedOutput: 0.0,
    spm: 0,
    pitchAngle: 0.0,
    dynAccel: 0.0,
    lastStepTime: 0,
    consecutiveSteps: 0,
    keyW: false,
    keyShift: false
  },

  history: {
    accel: new Array(150).fill(0),
    pitch: new Array(150).fill(0),
    trigger: new Array(150).fill(false)
  }
};

const elements = {
  btnConnect: document.getElementById('btnConnect'),
  btnSimulate: document.getElementById('btnSimulate'),
  deviceBadge: document.getElementById('deviceBadge'),
  deviceName: document.getElementById('deviceName'),
  sampleRate: document.getElementById('sampleRate'),
  currentModeLabel: document.getElementById('currentModeLabel'),

  motionBadge: document.getElementById('motionBadge'),
  speedOutputText: document.getElementById('speedOutputText'),
  speedProgressBar: document.getElementById('speedProgressBar'),
  keyW: document.getElementById('keyW'),
  keyShift: document.getElementById('keyShift'),

  cadenceVal: document.getElementById('cadenceVal'),
  pitchAngleVal: document.getElementById('pitchAngleVal'),
  accelDynVal: document.getElementById('accelDynVal'),

  modeNormal: document.getElementById('modeNormal'),
  modeSilent: document.getElementById('modeSilent'),

  sliderSens: document.getElementById('sliderSens'),
  sliderRunSpm: document.getElementById('sliderRunSpm'),
  sliderSilentAngle: document.getElementById('sliderSilentAngle'),
  sliderFilter: document.getElementById('sliderFilter'),

  lblSensVal: document.getElementById('lblSensVal'),
  lblRunSpmVal: document.getElementById('lblRunSpmVal'),
  lblSilentAngleVal: document.getElementById('lblSilentAngleVal'),

  btnSimWalk: document.getElementById('btnSimWalk'),
  btnSimRun: document.getElementById('btnSimRun'),
  btnSimSilent: document.getElementById('btnSimSilent'),
  btnSimStop: document.getElementById('btnSimStop'),

  waveformCanvas: document.getElementById('waveformCanvas')
};

// Mode Listeners
elements.modeNormal.addEventListener('click', () => {
  state.mode = 'normal';
  elements.modeNormal.classList.add('active');
  elements.modeSilent.classList.remove('active');
  elements.currentModeLabel.textContent = '通常足踏み';
});

elements.modeSilent.addEventListener('click', () => {
  state.mode = 'silent';
  elements.modeSilent.classList.add('active');
  elements.modeNormal.classList.remove('active');
  elements.currentModeLabel.textContent = 'サイレント (静音)';
});

elements.sliderSens.addEventListener('input', (e) => {
  state.params.sensThreshold = parseFloat(e.target.value);
  elements.lblSensVal.textContent = `${state.params.sensThreshold.toFixed(2)} G`;
});

elements.sliderRunSpm.addEventListener('input', (e) => {
  state.params.runSpmThreshold = parseInt(e.target.value);
  elements.lblRunSpmVal.textContent = `${state.params.runSpmThreshold} SPM`;
});

// Simulator
elements.btnSimulate.addEventListener('click', () => startSimulator('walk'));
elements.btnSimWalk.addEventListener('click', () => startSimulator('walk'));
elements.btnSimRun.addEventListener('click', () => startSimulator('run'));
elements.btnSimSilent.addEventListener('click', () => startSimulator('silent'));
elements.btnSimStop.addEventListener('click', () => stopSimulator());

function startSimulator(simType) {
  state.isSimulator = true;
  state.simulatorMode = simType;
  state.connected = true;
  if (simType === 'silent') elements.modeSilent.click();
  else elements.modeNormal.click();

  elements.deviceBadge.className = 'badge badge-online';
  elements.deviceBadge.textContent = 'シミュレーター';
  elements.deviceName.textContent = `Joy-Con (L) Virtual (${simType.toUpperCase()})`;
  elements.sampleRate.textContent = '60 Hz';
}

function stopSimulator() {
  state.isSimulator = false;
  state.simulatorMode = null;
  state.motion.status = 'STOP';
  state.motion.speedOutput = 0.0;
  state.motion.spm = 0;
  updateUI();
}

/* WebHID Connection */
elements.btnConnect.addEventListener('click', async () => {
  if (!('hid' in navigator)) {
    alert('WebHID API 非対応のブラウザです。');
    return;
  }
  try {
    const devices = await navigator.hid.requestDevice({
      filters: [{ vendorId: 0x057e, productId: 0x2006 }]
    });
    if (devices.length === 0) return;

    state.device = devices[0];
    await state.device.open();

    state.connected = true;
    state.isSimulator = false;

    elements.deviceBadge.className = 'badge badge-online';
    elements.deviceBadge.textContent = '接続済み';
    elements.deviceName.textContent = state.device.productName || 'Joy-Con (L)';

    // Enable IMU & 60Hz Full Report
    await enableJoyConSensors(state.device);

    state.device.addEventListener('inputreport', handleJoyConReport);
  } catch (err) {
    alert(`Joy-Con接続エラー: ${err.message}`);
  }
});

async function enableJoyConSensors(device) {
  const sendSub = async (subcmd, args) => {
    const rumble = [0x00, 0x01, 0x40, 0x40, 0x00, 0x01, 0x40, 0x40];
    const buf = new Uint8Array([state.packetCounter & 0x0F, ...rumble, subcmd, ...args]);
    state.packetCounter = (state.packetCounter + 1) & 0x0F;
    try { await device.sendReport(0x01, buf); } catch (e) {}
  };

  // Subcmd 0x03 -> 0x30 (Set Standard Full Report Mode)
  await sendSub(0x03, [0x30]);
  await new Promise(r => setTimeout(r, 50));
  // Subcmd 0x40 -> 0x01 (Enable IMU)
  await sendSub(0x40, [0x01]);
}

let lastReportTime = performance.now();
let frameCount = 0;

function handleJoyConReport(event) {
  const { reportId, data } = event;
  const now = performance.now();

  frameCount++;
  if (now - lastReportTime >= 1000) {
    elements.sampleRate.textContent = `${frameCount} Hz`;
    frameCount = 0;
    lastReportTime = now;
  }

  // Parse Standard Full Input Report (Report ID 0x30 or 0x21)
  if ((reportId === 0x30 || reportId === 0x21) && data.byteLength >= 24) {
    // In WebHID API, data starts after reportId, so Accel X is at offset 12
    const rawAx = data.getInt16(12, true) * 0.000244;
    const rawAy = data.getInt16(14, true) * 0.000244;
    const rawAz = data.getInt16(16, true) * 0.000244;

    const rawGx = data.getInt16(18, true) * 0.061;
    const rawGy = data.getInt16(20, true) * 0.061;

    processSensorData(rawAx, rawAy, rawAz, rawGx, rawGy, now);
  }
}

let filteredAx = 0, filteredAy = 0, filteredAz = 0;
let estimatedPitch = 0.0;
let baselinePitch = 0.0;
let motionCooldownTimer = 0;

function processSensorData(ax, ay, az, gx, gy, timestamp) {
  const alpha = state.params.filterAlpha;

  filteredAx = alpha * ax + (1 - alpha) * filteredAx;
  filteredAy = alpha * ay + (1 - alpha) * filteredAy;
  filteredAz = alpha * az + (1 - alpha) * filteredAz;

  const accelPitch = Math.atan2(filteredAx, filteredAz) * (180.0 / Math.PI);
  const dt = 0.016;
  estimatedPitch = 0.95 * (estimatedPitch + gy * dt) + 0.05 * accelPitch;

  const accelTotal = Math.sqrt(filteredAx * filteredAx + filteredAy * filteredAy + filteredAz * filteredAz);
  const dynAccel = Math.abs(accelTotal - 1.0);

  state.motion.dynAccel = dynAccel;
  state.motion.pitchAngle = estimatedPitch;

  let stepTriggered = false;

  if (state.mode === 'normal') {
    if (dynAccel > state.params.sensThreshold) {
      if (state.motion.lastStepTime === 0) {
        state.motion.lastStepTime = timestamp;
        state.motion.consecutiveSteps = 1;
      } else {
        const dtStep = timestamp - state.motion.lastStepTime;
        if (dtStep > 220 && dtStep < 900) {
          stepTriggered = true;
          state.motion.spm = Math.min(Math.max(Math.round(60000 / dtStep), 60), 220);
          state.motion.lastStepTime = timestamp;
          state.motion.consecutiveSteps++;
          motionCooldownTimer = 800;
        } else if (dtStep >= 900) {
          state.motion.lastStepTime = timestamp;
          state.motion.consecutiveSteps = 1;
        }
      }
    }
  } else {
    const deltaPitch = Math.abs(estimatedPitch - baselinePitch);
    if (deltaPitch > state.params.silentAngleThreshold) {
      stepTriggered = true;
      motionCooldownTimer = 600;
      state.motion.spm = Math.min(Math.round(Math.abs(gy) * 0.8), 180);
      state.motion.consecutiveSteps = 2;
    } else {
      baselinePitch = 0.98 * baselinePitch + 0.02 * estimatedPitch;
    }
  }

  if (motionCooldownTimer > 0) {
    motionCooldownTimer -= 16;
    if (state.motion.consecutiveSteps >= 2) {
      if (state.motion.spm >= state.params.runSpmThreshold) {
        state.motion.status = 'RUN';
        state.motion.speedOutput = 1.0;
        state.motion.keyW = true;
        state.motion.keyShift = true;
      } else {
        state.motion.status = 'WALK';
        state.motion.speedOutput = 0.5;
        state.motion.keyW = true;
        state.motion.keyShift = false;
      }
    }
  } else {
    state.motion.status = 'STOP';
    state.motion.speedOutput = 0.0;
    state.motion.spm = 0;
    state.motion.consecutiveSteps = 0;
    state.motion.keyW = false;
    state.motion.keyShift = false;
  }

  state.history.accel.shift(); state.history.accel.push(dynAccel);
  state.history.pitch.shift(); state.history.pitch.push(estimatedPitch);
  state.history.trigger.shift(); state.history.trigger.push(stepTriggered);

  updateUI();
}

function updateUI() {
  elements.speedOutputText.textContent = state.motion.speedOutput.toFixed(2);
  elements.speedProgressBar.style.width = `${state.motion.speedOutput * 100}%`;

  if (state.motion.status === 'RUN') {
    elements.motionBadge.className = 'badge badge-run';
    elements.motionBadge.textContent = 'RUN (走行)';
  } else if (state.motion.status === 'WALK') {
    elements.motionBadge.className = 'badge badge-walk';
    elements.motionBadge.textContent = 'WALK (歩行)';
  } else {
    elements.motionBadge.className = 'badge badge-stop';
    elements.motionBadge.textContent = 'STOP (静止)';
  }

  elements.keyW.className = state.motion.keyW ? 'key-cap active' : 'key-cap';
  elements.keyShift.className = state.motion.keyShift ? 'key-cap active' : 'key-cap';

  elements.cadenceVal.childNodes[0].nodeValue = `${state.motion.spm} `;
  elements.pitchAngleVal.textContent = `${state.motion.pitchAngle.toFixed(1)}°`;
  elements.accelDynVal.textContent = `${state.motion.dynAccel.toFixed(2)} G`;

  drawWaveform();
}

function drawWaveform() {
  const canvas = elements.waveformCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.width = canvas.clientWidth;
  const height = canvas.height = canvas.clientHeight;

  ctx.clearRect(0, 0, width, height);

  ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
  ctx.lineWidth = 1;
  for (let y = 0; y < height; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
  }

  const stepX = width / (state.history.accel.length - 1);

  ctx.strokeStyle = '#f59e0b';
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let i = 0; i < state.history.pitch.length; i++) {
    const x = i * stepX;
    const y = height / 2 - (state.history.pitch[i] / 40.0) * (height / 3);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.stroke();

  ctx.strokeStyle = '#06b6d4';
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let i = 0; i < state.history.accel.length; i++) {
    const x = i * stepX;
    const y = height - 20 - (state.history.accel[i] / 1.2) * (height - 40);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.stroke();

  for (let i = 0; i < state.history.trigger.length; i++) {
    if (state.history.trigger[i]) {
      const x = i * stepX;
      ctx.fillStyle = '#10b981';
      ctx.beginPath(); ctx.arc(x, 25, 6, 0, Math.PI * 2); ctx.fill();
    }
  }
}
