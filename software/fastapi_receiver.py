"""FastAPI receiver for Classroom Indicator Lights.

Run with:
    uvicorn software.teacherApplication.fastapi_receiver:app --reload

Environment variables:
    SERIAL_PORT   - Optional explicit serial port (e.g. COM5 or /dev/ttyACM0).
    TABLE_RANGE   - Optional inclusive range formatted as "start-end" (default "1-50").
    BAUD_RATE     - Optional baud rate override (default 115200).
"""
from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from collections import Counter
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, List, Optional

import serial
import serial.tools.list_ports
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, root_validator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("receiver.web")

COLOR_CODE = {0: "green", 1: "orange", 2: "red"}
COLOR_NAME_TO_ID = {value: key for key, value in COLOR_CODE.items()}
VALID_COLORS = set(COLOR_NAME_TO_ID.keys())
HTML_PAGE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>Classroom Indicator Lights</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&display=swap');
:root {
  --bg: #030712;
  --panel: #10182b;
  --accent: #29b6f6;
  --green: #57d86b;
  --orange: #ffa534;
  --red: #ff4d4d;
  --muted: #94a3b8;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  font-family: 'Space Grotesk', 'Trebuchet MS', sans-serif;
  background: radial-gradient(circle at top, #0f172a, #030712 60%);
  color: #f8fafc;
  display: flex;
  justify-content: center;
  padding: 1.2rem;
}
main {
  width: min(1100px, 100%);
  display: flex;
  flex-direction: column;
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Classroom Indicator Lights</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&display=swap');
:root {
    --bg: #030712;
    --panel: #10182b;
    --accent: #29b6f6;
    --green: #57d86b;
    --orange: #ffa534;
    --red: #ff4d4d;
    --muted: #94a3b8;
}
* { box-sizing: border-box; }
body {
    margin: 0;
    min-height: 100vh;
    font-family: 'Space Grotesk', 'Trebuchet MS', sans-serif;
    background: radial-gradient(circle at top, #0f172a, #030712 60%);
    color: #f8fafc;
    display: flex;
    justify-content: center;
    padding: 1.2rem;
}
main {
    width: min(1100px, 100%);
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
}
header {
    background: var(--panel);
    border-radius: 20px;
    padding: 1.2rem 1.5rem;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 1rem;
    align-items: center;
}
.status-chip {
    padding: 0.4rem 0.8rem;
    border-radius: 999px;
    background: rgba(41, 182, 246, 0.15);
    color: var(--accent);
    font-size: 0.85rem;
    justify-self: end;
}
button {
    font-family: 'Space Grotesk', 'Trebuchet MS', sans-serif;
    font-weight: 600;
    border: none;
    border-radius: 12px;
    background: var(--accent);
    color: #030712;
    padding: 0.45rem 0.8rem;
    cursor: pointer;
    transition: opacity 0.2s ease, transform 0.2s ease;
}
button:hover:not(:disabled) {
    opacity: 0.9;
    transform: translateY(-1px);
}
button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}
.counter {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
}
.counter span:first-child {
    font-size: 0.85rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.counter strong {
    font-size: clamp(1.8rem, 5vw, 2.6rem);
}
.counter.orange strong { color: var(--orange); }
.counter.red strong { color: var(--red); }
.control-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 1rem;
}
.control-card {
    background: rgba(16, 24, 43, 0.95);
    border-radius: 18px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
}
.serial-summary strong {
    font-size: 1.1rem;
}
.range-inputs {
    display: flex;
    gap: 0.6rem;
}
.range-inputs label {
    flex: 1;
    display: flex;
    flex-direction: column;
    font-size: 0.85rem;
    color: var(--muted);
    gap: 0.2rem;
}
.range-inputs input {
    background: #020617;
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 12px;
    color: #f8fafc;
    padding: 0.4rem 0.6rem;
}
.action-card small {
    color: var(--muted);
    font-size: 0.85rem;
}
.red-card ol {
    margin: 0;
    padding-left: 1.2rem;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    max-height: 200px;
    overflow-y: auto;
}
.serial-actions {
    display: flex;
    gap: 0.6rem;
    align-items: stretch;
}
.serial-actions select {
    flex: 1;
    background: #020617;
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 14px;
    color: #f8fafc;
    padding: 0.45rem 0.6rem;
    font-size: 0.95rem;
}
.serial-actions select:focus {
    outline: 2px solid rgba(41, 182, 246, 0.6);
    outline-offset: 2px;
}
.serial-buttons {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}
.serial-buttons button {
    width: 120px;
}
.control-card button#applyRange,
.control-card button#resetAll {
    width: 100%;
}
.serial-status {
    font-size: 0.85rem;
    color: var(--muted);
}
.serial-modal {
    border: none;
    border-radius: 24px;
    padding: 0;
    max-width: 480px;
    width: calc(100% - 2rem);
}
.serial-modal[hidden] {
    display: none;
}
.serial-modal.visible {
    display: block;
}
.serial-modal::backdrop {
    background: rgba(3, 7, 18, 0.75);
}
.serial-modal-content {
    background: var(--panel);
    border-radius: 24px;
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}
.modal-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 0.6rem;
}
.ghost-button {
    background: transparent;
    border: 1px solid rgba(148, 163, 184, 0.4);
    color: var(--muted);
}
.table-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
    gap: 0.9rem;
}
.table-card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 18px;
    padding: 1rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: transform 0.2s ease, background 0.2s ease;
    cursor: pointer;
    user-select: none;
}
.table-card:hover {
    transform: translateY(-3px);
}
.table-card[data-color="green"] {
    background: var(--green);
    color: #041207;
    border: 1px solid rgba(0, 0, 0, 0.08);
    box-shadow: 0 8px 18px rgba(87, 216, 107, 0.22);
}
.table-card[data-color="orange"] {
    background: var(--orange);
    color: #2d1600;
    border: 1px solid rgba(0, 0, 0, 0.08);
    box-shadow: 0 8px 18px rgba(255, 165, 52, 0.28);
}
.table-card[data-color="red"] {
    background: var(--red);
    color: #2d0202;
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-shadow: 0 8px 22px rgba(255, 77, 77, 0.35);
}
.table-card strong {
    font-size: 1.5rem;
}
.mute-btn {
    background: transparent;
    border: none;
    width: 1.2rem;
    height: 1.2rem;
    padding: 0;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.7;
    transition: opacity 0.2s;
    color: currentColor;
}
.mute-btn:hover {
    opacity: 1;
}
.mute-btn svg {
    width: 100%;
    height: 100%;
    stroke-linecap: round;
    stroke-linejoin: round;
}
footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.6rem;
    color: var(--muted);
    font-size: 0.9rem;
}
@media (max-width: 600px) {
    body { padding: 0.6rem; }
    header { grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); }
    .table-card { padding: 0.8rem; }
    .serial-actions { flex-direction: column; }
    .serial-buttons { flex-direction: row; }
    .serial-buttons button { flex: 1; width: auto; }
    .range-inputs { flex-direction: column; }
}
</style>
</head>
<body>
<main>
    <header>
        <div class="counter orange">
            <span>Orange</span>
            <strong id="orangeCount">0</strong>
        </div>
        <div class="counter red">
            <span>Red</span>
            <strong id="redCount">0</strong>
        </div>
        <div class="status-chip" id="statusChip">Connecting...</div>
    </header>
    <section class="control-grid">
        <article class="control-card serial-summary">
            <span class="label">Serial Port</span>
            <strong id="serialSummary">Detecting devices...</strong>
            <button id="openSerialModal" type="button">Change Port</button>
        </article>
        <article class="control-card">
            <span class="label">Table Range</span>
            <div class="range-inputs">
                <label>
                    Start
                    <input type="number" id="startTable" min="1" value="1" />
                </label>
                <label>
                    End
                    <input type="number" id="endTable" min="1" value="50" />
                </label>
            </div>
            <button id="applyRange" type="button">Apply Range</button>
        </article>
        <article class="control-card action-card">
            <span class="label">Quick Actions</span>
            <button id="resetAll" type="button">Reset All To Green</button>
            <button id="beepNow" type="button">Beeps On</button>
            <small>Tap any table tile to cycle between green > orange > red.</small>
        </article>
        <article class="control-card red-card">
            <span class="label">Longest On Red</span>
            <ol id="redList"></ol>
        </article>
    </section>
    <dialog id="serialModal" class="serial-modal">
        <div class="serial-modal-content">
            <h3>Serial Connection</h3>
            <p>Select the micro:bit receiver port that is connected to this computer.</p>
            <div class="serial-actions">
                <select id="portSelect">
                    <option value="">Loading...</option>
                </select>
                <div class="serial-buttons">
                    <button id="refreshPorts" type="button">Refresh</button>
                    <button id="connectPort" type="button">Connect</button>
                </div>
            </div>
            <span class="serial-status" id="serialStatusDetail">Detecting devices...</span>
            <div class="modal-buttons">
                <button id="closeSerialModal" type="button" class="ghost-button">Close</button>
            </div>
        </div>
    </dialog>
    <section class="table-grid" id="tableGrid"></section>
    <footer>
        <span>Tap a tile on the teacher console to cycle colors.</span>
        <span id="lastUpdated">Last update: --</span>
    </footer>
</main>
<script>
const grid = document.getElementById('tableGrid');
const statusChip = document.getElementById('statusChip');
const orangeCount = document.getElementById('orangeCount');
const redCount = document.getElementById('redCount');
const lastUpdated = document.getElementById('lastUpdated');
const portSelect = document.getElementById('portSelect');
const connectPortBtn = document.getElementById('connectPort');
const refreshPortsBtn = document.getElementById('refreshPorts');
const serialSummary = document.getElementById('serialSummary');
const serialStatusDetail = document.getElementById('serialStatusDetail');
const serialModal = document.getElementById('serialModal');
const openSerialModalBtn = document.getElementById('openSerialModal');
const closeSerialModalBtn = document.getElementById('closeSerialModal');
const startTableInput = document.getElementById('startTable');
const endTableInput = document.getElementById('endTable');
const applyRangeBtn = document.getElementById('applyRange');
const resetAllBtn = document.getElementById('resetAll');
const beepBtn = document.getElementById('beepNow');
const redList = document.getElementById('redList');
const COLOR_SEQUENCE = ['green', 'orange', 'red'];
const NEXT_COLOR = { green: 'orange', orange: 'red', red: 'green' };
const ALERT_COLORS = new Set(['orange', 'red']);
let tables = new Map();
let mutedTables = new Set();
let beepsEnabled = true;
let autoSerialPrompted = false;
let audioCtx = null;

function ensureAudioContext() {
    try {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (audioCtx.state === 'suspended') audioCtx.resume();
        return audioCtx;
    } catch (error) {
        return null;
    }
}

function playTone(ctx, freq, startTime, duration = 0.12, gainLevel = 0.18) {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'square';
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(gainLevel, startTime);
    gain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
    osc.connect(gain).connect(ctx.destination);
    osc.start(startTime);
    osc.stop(startTime + duration + 0.02);
}

function beepAlert() {
    if (!beepsEnabled) return;
    const ctx = ensureAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime + 0.01;
    playTone(ctx, 880, now, 0.12);
    playTone(ctx, 660, now + 0.16, 0.12);
}

function toggleTableMute(tableId) {
    if (mutedTables.has(tableId)) {
        mutedTables.delete(tableId);
    } else {
        mutedTables.add(tableId);
    }
    updateMuteButton(tableId);
}

function updateMuteButton(tableId) {
    const card = document.querySelector(`[data-table="${tableId}"]`);
    if (!card) return;
    const btn = card.querySelector('.mute-btn');
    if (!btn) return;
    const isMuted = mutedTables.has(tableId);
    btn.innerHTML = isMuted ? getMutedSVG() : getUnmutedSVG();
    btn.title = isMuted ? 'Beep enabled for this table' : 'Beep disabled for this table';
}

function getMutedSVG() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 5L6 9H2v6h4l5 4v-4"></path><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>';
}

function getUnmutedSVG() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path><path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path></svg>';
}

function enteredAlert(prevColor, nextColor) {
    if (!ALERT_COLORS.has(nextColor)) return false;
    return !ALERT_COLORS.has(prevColor);
}

function upsertCard(data) {
    tables.set(data.table, data.color);
    let card = document.querySelector(`[data-table="${data.table}"]`);
    if (!card) {
        card = document.createElement('article');
        card.className = 'table-card';
        card.dataset.table = data.table;
        grid.appendChild(card);
    }
    card.dataset.color = data.color;
    const isMuted = mutedTables.has(data.table);
    card.innerHTML = `<strong>${data.table}</strong><button class="mute-btn" title="${isMuted ? 'Beep enabled for this table' : 'Beep disabled for this table'}">${isMuted ? getMutedSVG() : getUnmutedSVG()}</button>`;
    const muteBtn = card.querySelector('.mute-btn');
    if (muteBtn) {
        muteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleTableMute(data.table);
        });
    }
}

function renderSnapshot(payload) {
    const previous = new Map(tables);
    grid.innerHTML = '';
    tables.clear();
    let shouldBeep = false;
    payload.tables.forEach((entry) => {
        if (!shouldBeep && enteredAlert(previous.get(entry.table), entry.color) && !mutedTables.has(entry.table)) {
            shouldBeep = true;
        }
        upsertCard(entry);
    });
    updateCounts(payload.counts);
    updateRangeFields(payload.range);
    updateRedList(payload.redDurations);
    stampUpdate();
    if (shouldBeep) beepAlert();
}

function updateCounts(counts) {
    orangeCount.textContent = counts.orange ?? 0;
    redCount.textContent = counts.red ?? 0;
}

function stampUpdate() {
    lastUpdated.textContent = `Last update: ${new Date().toLocaleTimeString()}`;
}

function updateRangeFields(range) {
    if (!range || !startTableInput || !endTableInput) return;
    startTableInput.value = range.start;
    endTableInput.value = range.end;
}

function updateRedList(entries) {
    if (!redList) return;
    redList.innerHTML = '';
    if (!entries || entries.length === 0) {
        redList.innerHTML = '<li>All clear</li>';
        return;
    }
    entries.forEach((entry) => {
        const item = document.createElement('li');
        item.textContent = `Table ${entry.table}: ${entry.seconds}s`;
        redList.appendChild(item);
    });
}

async function fetchSerialStatus() {
    try {
        const response = await fetch('/api/serial');
        if (!response.ok) throw new Error('Failed to load serial status');
        const payload = await response.json();
        populateSerialOptions(payload);
        updateSerialStatus(payload);
        maybePromptSerial(payload);
    } catch (error) {
        if (serialSummary) {
            serialSummary.textContent = 'Serial status unavailable';
        }
        if (serialStatusDetail) {
            serialStatusDetail.textContent = 'Serial status unavailable';
        }
    }
}

function populateSerialOptions(payload) {
    if (!portSelect) return;
    const ports = payload?.available_ports ?? [];
    const desiredSelection = payload?.configured_port ?? payload?.connected_port ?? '';
    portSelect.innerHTML = '';
    const autoOption = document.createElement('option');
    autoOption.value = '';
    autoOption.textContent = 'Auto detect (micro:bit)';
    portSelect.appendChild(autoOption);
    ports.forEach((port) => {
        const option = document.createElement('option');
        option.value = port.device;
        option.textContent = `${port.device} - ${port.description}`;
        portSelect.appendChild(option);
    });
    const hasDesiredValue = Array.from(portSelect.options).some((option) => option.value === desiredSelection);
    portSelect.value = hasDesiredValue ? desiredSelection : '';
}

function updateSerialStatus(payload) {
    const activePort = payload?.connected_port;
    const configuredPort = payload?.configured_port;
    let summaryText = 'Not connected';
    if (activePort) {
        summaryText = `Connected to ${activePort}`;
    } else if (configuredPort) {
        summaryText = `Waiting for ${configuredPort}`;
    }
    if (serialSummary) {
        serialSummary.textContent = summaryText;
    }
    if (serialStatusDetail) {
        serialStatusDetail.textContent = summaryText;
    }
}

function openSerialModal(autoTriggered = false) {
    if (!serialModal) return;
    fetchSerialStatus();
    if (typeof serialModal.showModal === 'function') {
        if (!serialModal.open) {
            serialModal.showModal();
        }
    } else {
        serialModal.classList.add('visible');
        serialModal.removeAttribute('hidden');
    }
    if (autoTriggered) {
        serialModal.dataset.auto = 'true';
    }
}

function closeSerialModal() {
    if (!serialModal) return;
    if (typeof serialModal.close === 'function') {
        if (serialModal.open) {
            serialModal.close();
        }
    } else {
        serialModal.classList.remove('visible');
        serialModal.setAttribute('hidden', 'hidden');
    }
    delete serialModal.dataset.auto;
}

function maybePromptSerial(payload) {
    const isConnected = Boolean(payload?.connected_port);
    if (!isConnected && !autoSerialPrompted) {
        autoSerialPrompted = true;
        openSerialModal(true);
    }
    if (isConnected) {
        autoSerialPrompted = false;
        closeSerialModal();
    }
}

async function connectSelectedPort() {
    if (!connectPortBtn) return;
    const desiredPort = portSelect ? portSelect.value : '';
    connectPortBtn.disabled = true;
    connectPortBtn.textContent = 'Connecting...';
    try {
        const response = await fetch('/api/serial', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ port: desiredPort || null }),
        });
        if (!response.ok) throw new Error('Failed to configure serial');
        const payload = await response.json();
        populateSerialOptions(payload);
        updateSerialStatus(payload);
        maybePromptSerial(payload);
    } catch (error) {
        alert('Unable to configure the serial port. Please ensure the device is available.');
    } finally {
        connectPortBtn.disabled = false;
        connectPortBtn.textContent = 'Connect';
    }
}

async function sendTableUpdate(tableId, color) {
    try {
        const response = await fetch(`/api/table/${tableId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ color })
        });
        const payload = await response.json().catch(() => null);
        if (!response.ok || !payload) {
            throw new Error(payload?.detail || 'Failed to update table');
        }
        const prevColor = tables.get(tableId);
        upsertCard(payload.table);
        updateCounts(payload.counts);
        updateRedList(payload.redDurations);
        stampUpdate();
        if (enteredAlert(prevColor, payload.table.color) && !mutedTables.has(tableId)) beepAlert();
    } catch (error) {
        alert(error.message || 'Unable to update the table.');
    }
}

function cycleTableColor(tableId) {
    const currentColor = tables.get(tableId) || 'green';
    const nextColor = NEXT_COLOR[currentColor] || COLOR_SEQUENCE[0];
    sendTableUpdate(tableId, nextColor);
}

async function applyTableRange() {
    if (!startTableInput || !endTableInput) return;
    const start = Number(startTableInput.value);
    const end = Number(endTableInput.value);
    if (!Number.isInteger(start) || !Number.isInteger(end) || start <= 0 || end < start) {
        alert('Enter a valid start/end range (start <= end).');
        return;
    }
    try {
        const response = await fetch('/api/table-range', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start, end })
        });
        if (!response.ok) {
            const payload = await response.json().catch(() => ({}));
            throw new Error(payload?.detail || 'Failed to update table range');
        }
        const payload = await response.json();
        renderSnapshot(payload);
    } catch (error) {
        alert(error.message || 'Unable to update table range.');
    }
}

async function resetAllTables() {
    try {
        const response = await fetch('/api/reset', { method: 'POST' });
        if (!response.ok) throw new Error('Failed to reset tables');
        const payload = await response.json();
        renderSnapshot(payload);
    } catch (error) {
        alert(error.message || 'Unable to reset tables.');
    }
}

function connectSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const socket = new WebSocket(`${protocol}://${window.location.host}/ws`);
    socket.addEventListener('open', () => {
        statusChip.textContent = 'Live';
    });
    socket.addEventListener('close', () => {
        statusChip.textContent = 'Reconnecting...';
        setTimeout(connectSocket, 2000);
    });
    socket.addEventListener('message', (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type === 'snapshot') {
            renderSnapshot(payload);
        } else if (payload.type === 'table_update') {
            const prevColor = tables.get(payload?.table?.table);
            upsertCard(payload.table);
            updateCounts(payload.counts);
            updateRedList(payload.redDurations);
            stampUpdate();
            if (enteredAlert(prevColor, payload.table.color) && !mutedTables.has(payload?.table?.table)) beepAlert();
        }
    });
    socket.addEventListener('error', () => {
        socket.close();
    });
}

if (refreshPortsBtn) {
    refreshPortsBtn.addEventListener('click', fetchSerialStatus);
}
if (connectPortBtn) {
    connectPortBtn.addEventListener('click', connectSelectedPort);
}
if (openSerialModalBtn) {
    openSerialModalBtn.addEventListener('click', () => openSerialModal(false));
}
if (closeSerialModalBtn) {
    closeSerialModalBtn.addEventListener('click', closeSerialModal);
}
if (serialModal) {
    serialModal.addEventListener('cancel', (event) => {
        event.preventDefault();
        closeSerialModal();
    });
    serialModal.addEventListener('click', (event) => {
        if (event.target === serialModal) {
            closeSerialModal();
        }
    });
}
if (applyRangeBtn) {
    applyRangeBtn.addEventListener('click', applyTableRange);
}
if (resetAllBtn) {
    resetAllBtn.addEventListener('click', resetAllTables);
}
if (beepBtn) {
    beepBtn.addEventListener('click', () => {
        beepsEnabled = !beepsEnabled;
        beepBtn.textContent = beepsEnabled ? 'Beeps On' : 'Beeps Off';
    });
}
if (grid) {
    grid.addEventListener('click', (event) => {
        const card = event.target.closest('.table-card');
        if (!card) return;
        const tableId = Number(card.dataset.table);
        if (!Number.isInteger(tableId)) return;
        cycleTableColor(tableId);
    });
}
if (statusChip) {
    statusChip.addEventListener('click', () => openSerialModal(false));
}

fetchSerialStatus();
connectSocket();
</script>
</body>
</html>"""


def parse_table_range(raw: Optional[str]) -> tuple[int, int]:
    if not raw:
        return 1, 50
    try:
        start_str, end_str = raw.split("-", 1)
        start = int(start_str)
        end = int(end_str)
        if start <= 0 or end < start:
            raise ValueError
        return start, end
    except ValueError:
        LOGGER.warning("Invalid TABLE_RANGE '%s'. Falling back to 1-50.", raw)
        return 1, 50


class TableState:
    """Thread-safe store for the latest table colors."""

    def __init__(self, start: int, end: int) -> None:
        self._lock = threading.Lock()
        self._start = start
        self._end = end
        self._colors: Dict[int, str] = {table_id: "green" for table_id in range(start, end + 1)}
        self._red_started: Dict[int, Optional[float]] = {table_id: None for table_id in range(start, end + 1)}

    def snapshot(self) -> Dict[str, object]:
        with self._lock:
            return self._snapshot_locked()

    def update_table(self, table: int, color: str) -> Dict[str, object]:
        with self._lock:
            if table not in self._colors:
                self._colors[table] = "green"
                self._red_started[table] = None
            self._colors[table] = color
            if color == "red":
                if not self._red_started.get(table):
                    self._red_started[table] = time.time()
            else:
                self._red_started[table] = None
            payload = {
                "type": "table_update",
                "table": {"table": table, "color": color},
                "counts": self._counts_locked(),
                "range": self._range_locked(),
                "redDurations": self._red_durations_locked(),
            }
        return payload

    def reset_all(self) -> Dict[str, object]:
        with self._lock:
            for table in self._colors:
                self._colors[table] = "green"
                self._red_started[table] = None
            return self._snapshot_locked()

    def configure_range(self, start: int, end: int) -> Dict[str, object]:
        if start <= 0 or end < start:
            raise ValueError("Invalid table range")
        with self._lock:
            self._start = start
            self._end = end
            self._colors = {table_id: "green" for table_id in range(start, end + 1)}
            self._red_started = {table_id: None for table_id in range(start, end + 1)}
            return self._snapshot_locked()

    def _counts_locked(self) -> Dict[str, int]:
        counts = Counter(self._colors.values())
        return {
            "green": counts.get("green", 0),
            "orange": counts.get("orange", 0),
            "red": counts.get("red", 0),
        }

    def _red_durations_locked(self, limit: int = 10) -> List[Dict[str, int]]:
        now = time.time()
        durations = [
            {"table": table_id, "seconds": int(now - started)}
            for table_id, started in self._red_started.items()
            if started
        ]
        durations.sort(key=lambda entry: entry["seconds"], reverse=True)
        return durations[:limit]

    def _range_locked(self) -> Dict[str, int]:
        return {"start": self._start, "end": self._end}

    def _snapshot_locked(self) -> Dict[str, object]:
        tables = [
            {"table": table_id, "color": color}
            for table_id, color in sorted(self._colors.items())
        ]
        return {
            "type": "snapshot",
            "tables": tables,
            "counts": self._counts_locked(),
            "range": self._range_locked(),
            "redDurations": self._red_durations_locked(),
        }


class WebsocketManager:
    def __init__(self) -> None:
        self._connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)

    async def broadcast(self, message: Dict[str, object]) -> None:
        async with self._lock:
            stale: List[WebSocket] = []
            for connection in list(self._connections):
                try:
                    await connection.send_json(message)
                except Exception:
                    stale.append(connection)
            for connection in stale:
                self._connections.remove(connection)


class SerialReceiver:
    """Bridges micro:bit serial data into the web application."""

    RETRY_SECONDS = 3

    def __init__(self, state: TableState, ws_manager: WebsocketManager) -> None:
        self._state = state
        self._ws_manager = ws_manager
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._connection_lock = threading.Lock()
        self._connection: Optional[serial.Serial] = None

        self._configured_port = os.getenv("SERIAL_PORT")
        self._active_port: Optional[str] = None
        self._baud = int(os.getenv("BAUD_RATE", "115200"))

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, name="SerialReceiver", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        with self._connection_lock:
            if self._connection:
                try:
                    self._connection.close()
                except Exception:
                    pass
                self._connection = None
            self._active_port = None

    def set_port(self, port: Optional[str]) -> None:
        normalized = (port or "").strip() or None
        self._configured_port = normalized
        LOGGER.info("Configured serial port set to %s", normalized or "auto-detect")
        self._force_reconnect()

    def serial_status(self) -> Dict[str, object]:
        return {
            "configured_port": self._configured_port,
            "connected_port": self._active_port,
            "available_ports": self._enumerate_ports(),
        }

    def send_teacher_command(self, table: int, color: str) -> None:
        color_id = COLOR_NAME_TO_ID[color]
        message = f"T,{table},{color_id}\n".encode("utf-8")
        with self._connection_lock:
            if not self._connection or not self._connection.is_open:
                raise RuntimeError("Serial link is not connected.")
            self._connection.write(message)
            LOGGER.info("Sent teacher command for table %s -> %s", table, color)

    def reset_all(self) -> None:
        message = "T,-1,0\n".encode("utf-8")
        with self._connection_lock:
            if not self._connection or not self._connection.is_open:
                raise RuntimeError("Serial link is not connected.")
            self._connection.write(message)
            LOGGER.info("Sent reset command")

    def _worker(self) -> None:
        while not self._stop_event.is_set():
            port = self._resolve_port()
            if not port:
                LOGGER.info("Waiting for micro:bit receiver...")
                time.sleep(self.RETRY_SECONDS)
                continue
            try:
                with serial.Serial(port, self._baud, timeout=1) as connection:
                    LOGGER.info("Connected to %s", port)
                    with self._connection_lock:
                        self._connection = connection
                        self._active_port = port
                    self._read_loop(connection)
            except serial.SerialException as exc:
                LOGGER.warning("Serial error on %s: %s", port, exc)
            finally:
                with self._connection_lock:
                    self._connection = None
                    self._active_port = None
                time.sleep(self.RETRY_SECONDS)

    def _read_loop(self, connection: serial.Serial) -> None:
        while not self._stop_event.is_set():
            try:
                raw = connection.readline().decode("utf-8", errors="ignore").strip()
            except Exception as exc:
                LOGGER.warning("Failed to read serial data: %s", exc)
                break
            if not raw:
                continue
            payload = self._parse_message(raw)
            if not payload:
                continue
            table, color = payload
            update = self._state.update_table(table, color)
            if self._loop:
                asyncio.run_coroutine_threadsafe(self._ws_manager.broadcast(update), self._loop)

    def _parse_message(self, raw: str) -> Optional[tuple[int, str]]:
        parts = raw.split(",")
        if len(parts) != 3:
            LOGGER.debug("Ignoring malformed packet: %s", raw)
            return None
        role, table_str, color_str = parts
        if role == "RT":  # echo of our own teacher command
            return None
        try:
            table = int(table_str)
            color_index = int(color_str)
        except ValueError:
            LOGGER.debug("Invalid numeric values in packet: %s", raw)
            return None
        color = COLOR_CODE.get(color_index)
        if not color:
            LOGGER.debug("Unknown color index in packet: %s", raw)
            return None
        return table, color

    def _resolve_port(self) -> Optional[str]:
        if self._configured_port:
            return self._configured_port
        for port in serial.tools.list_ports.comports():
            description = (port.description or "").lower()
            if "microbit" in description or "mbed" in description or "cdc" in description:
                return port.device
        return None

    def _enumerate_ports(self) -> List[Dict[str, str]]:
        ports: List[Dict[str, str]] = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                "device": port.device,
                "description": port.description or "Unknown",
            })
        return ports

    def _force_reconnect(self) -> None:
        with self._connection_lock:
            if self._connection and self._connection.is_open:
                try:
                    self._connection.close()
                except Exception:
                    pass
            self._connection = None
            self._active_port = None


class TableUpdateRequest(BaseModel):
    color: str = Field(pattern="^(green|orange|red)$")


class SerialConfigRequest(BaseModel):
    port: Optional[str] = Field(
        default=None,
        description="Serial device identifier (e.g. COM5). Use null for auto-detect.",
    )


class TableRangeRequest(BaseModel):
    start: int = Field(ge=1, description="First table identifier (inclusive).")
    end: int = Field(ge=1, description="Last table identifier (inclusive).")

    @root_validator(skip_on_failure=True)
    def ensure_valid_range(cls, values: Dict[str, int]) -> Dict[str, int]:
        start = values.get("start")
        end = values.get("end")
        if start is None or end is None:
            return values
        if end < start:
            raise ValueError("end must be greater than or equal to start")
        return values


start_table, end_table = parse_table_range(os.getenv("TABLE_RANGE"))
table_state = TableState(start_table, end_table)
ws_manager = WebsocketManager()
serial_receiver = SerialReceiver(table_state, ws_manager)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    loop = asyncio.get_running_loop()
    serial_receiver.bind_loop(loop)
    serial_receiver.start()
    try:
        yield
    finally:
        serial_receiver.stop()


app = FastAPI(title="Classroom Indicator Lights Receiver", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    return HTML_PAGE


@app.get("/api/status")
async def api_status() -> Dict[str, object]:
    return table_state.snapshot()


@app.post("/api/table/{table_id}")
async def api_update_table(table_id: int, request: TableUpdateRequest) -> Dict[str, object]:
    update = table_state.update_table(table_id, request.color)
    if serial_receiver:
        try:
            await asyncio.to_thread(serial_receiver.send_teacher_command, table_id, request.color)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    await ws_manager.broadcast(update)
    return update


@app.post("/api/reset")
async def api_reset() -> Dict[str, object]:
    snapshot = table_state.reset_all()
    if serial_receiver:
        try:
            await asyncio.to_thread(serial_receiver.reset_all)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    await ws_manager.broadcast(snapshot)
    return snapshot


@app.post("/api/table-range")
async def api_table_range(request: TableRangeRequest) -> Dict[str, object]:
    try:
        snapshot = table_state.configure_range(request.start, request.end)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    await ws_manager.broadcast(snapshot)
    return snapshot


@app.get("/api/serial")
async def api_serial_status() -> Dict[str, object]:
    return serial_receiver.serial_status()


@app.post("/api/serial")
async def api_serial_config(request: SerialConfigRequest) -> Dict[str, object]:
    desired_port = (request.port or "").strip() or None
    serial_receiver.set_port(desired_port)
    return serial_receiver.serial_status()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json(table_state.snapshot())
        while True:
            await websocket.receive_text()  # clients are read-only; ignore payloads
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
