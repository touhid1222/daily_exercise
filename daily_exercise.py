# ==============================
# Calm Coach — Public Speaking & Meeting Helper
# Streamlit app (mobile-first) with TTS + practice tools
# ==============================

from __future__ import annotations

# --- Standard libs
import time
import json
import datetime
from typing import Dict, List

# --- Third-party
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# ==============================
# Constants & Helpers
# ==============================
LOG_CSV_PATH = "calmcoach_logs.csv"
MEETING_TYPES = [
    "1:1",
    "Stand-up",
    "Design/Process Review",
    "Cross-team sync",
    "With Techs on tool",
    "Vendor call",
    "Escalation/Issue review",
]


def _tpl(s: str, **vals) -> str:
    """
    Very safe string templating for HTML/JS blocks.
    Replaces tokens of the form __NAME__ only.
    Avoids conflicts with % and {} used by JS/CSS.
    """
    for k, v in vals.items():
        s = s.replace(f"__{k}__", str(v))
    return s


def render_global_css() -> None:
    """
    Inject mobile-first CSS with big, readable typography.
    >>> To change sizes again, edit values below (look for font-size, min-height).
    """
    st.markdown(
        """
<style>
/* ========= Design tokens (light) ========= */
:root{
  --bg: #f8fafc;                /* page background */
  --surface: #ffffff;            /* card background */
  --text: #0f172a;               /* main text */
  --muted: #475569;              /* secondary text */
  --border: #e2e8f0;             /* card/input borders */
  --primary: #2563eb;            /* primary button */
  --primary-contrast: #ffffff;   /* text on primary */
  --focus: #60a5fa;              /* focus outline */
  --pill-bg: #eef2ff;
  --pill-text: #1e3a8a;

  /* Button defaults */
  --btn-bg: var(--primary);
  --btn-text: var(--primary-contrast);
  --btn-border: transparent;
  --btn-hover-filter: brightness(0.97);
  --btn-active-filter: brightness(0.94);
}

/* ========= Design tokens (dark) ========= */
@media (prefers-color-scheme: dark){
  :root{
    --bg: #0b0f14;
    --surface: #111827;
    --text: #e5e7eb;
    --muted: #a9b8c9;
    --border: #1f2937;
    --primary: #3b82f6;
    --primary-contrast: #0b0f14;
    --focus: #60a5fa;
    --pill-bg: #0b1b3a;
    --pill-text: #c7d2fe;

    --btn-bg: var(--primary);
    --btn-text: var(--primary-contrast);
    --btn-border: transparent;
    --btn-hover-filter: brightness(1.05);
    --btn-active-filter: brightness(1.08);
  }
}

/* ========= Base layout & global typography =========
   MAIN KNOB for app-wide text size: font-size
*/
html, body { 
  background: var(--bg);
  color: var(--text);
  -webkit-text-size-adjust: 100%;
}
[class^="css"] { font-size: 22px; line-height: 1.6; }  /* ⬅️ Global base text size */

.block-container { 
  padding-top: 3.8rem !important;  /* keep header visible */
  padding-bottom: 3.2rem; 
}

/* ========= Links ========= */
a { color: var(--primary); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ========= Buttons (BIG & touch-friendly) =========
   MAIN KNOBS: min-height, padding, font-size
*/
.stButton>button, .stDownloadButton>button, button { 
  min-height: 64px;                 /* ⬅️ big touch target */
  padding: 18px 22px;               /* ⬅️ thicker padding */
  font-size: 22px;                  /* ⬅️ bigger label */
  font-weight: 700;
  border-radius: 18px;
  border: 1px solid var(--btn-border);
  background: var(--btn-bg);
  color: var(--btn-text);
  box-shadow: 0 8px 22px rgba(37, 99, 235, 0.18);
  transition: transform .04s ease, filter .12s ease, box-shadow .2s ease;
  cursor: pointer;
}
.stButton>button:hover, .stDownloadButton>button:hover, button:hover {
  filter: var(--btn-hover-filter);
  transform: translateY(-0.5px);
  box-shadow: 0 10px 26px rgba(37, 99, 235, 0.22);
}
.stButton>button:active, .stDownloadButton>button:active, button:active {
  filter: var(--btn-active-filter);
  transform: translateY(0);
}
.stButton>button:focus-visible, .stDownloadButton>button:focus-visible, button:focus-visible {
  outline: 3px solid var(--focus);
  outline-offset: 2px;
}

/* Make download button a subtle/secondary style for contrast with primaries */
.stDownloadButton>button{
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--border);
  box-shadow: none;
}
.stDownloadButton>button:hover{
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.12);
}

/* ========= Inputs & selects =========
   KNOB: font-size
*/
.stTextInput>div>div>input, .stTextArea textarea, select {
  font-size: 20px;                  /* ⬅️ larger input text */
  padding: 16px 14px; 
  border-radius: 16px;
  background: var(--surface); 
  color: var(--text);
  border: 1px solid var(--border);
}
.stTextInput>div>div>input::placeholder, .stTextArea textarea::placeholder { color: var(--muted); }

/* ========= Cards & helpers ========= */
.card {
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 18px;
  margin: 14px 0;
  background: var(--surface);
  box-shadow: 0 10px 28px rgba(2, 6, 23, 0.06);
}
/* KNOB: Title size */
.title { font-weight: 800; font-size: 1.6rem; margin-bottom: 10px; }  /* ~25.6px */
.hint  { color: var(--muted); font-size: 1.05rem; }
.small { font-size: 0.98rem; }
.center{ text-align: center; }
.pill  { display:inline-block; padding:6px 12px; border-radius:999px; 
         background: var(--pill-bg); color: var(--pill-text);
         border: 1px solid rgba(99, 102, 241, 0.25); font-size:1rem; margin:2px 4px; }

/* KNOBS: status/timer emphasis */
.status{ font-size: 34px; text-align: center; margin: 8px 0 14px; color: var(--text);}
.timer { font-size: 60px; font-weight: 800; text-align: center; margin: 14px 0; color: var(--text);}

/* ========= Breathing visual ========= */
.breath-wrap { display:flex; justify-content:center; align-items:center; margin:14px 0 20px; }
.circle {
  width: 270px; height: 270px; border-radius: 50%;
  border: 4px solid rgba(99, 102, 241, 0.35);
  background: radial-gradient(circle at 50% 50%, #f7fbff 0%, #e9f3ff 58%, #d7e9ff 100%);
  display:flex; justify-content:center; align-items:center;
  transform: scale(1); transition: transform 0.7s ease;
  box-shadow: inset 0 0 40px rgba(37, 99, 235, 0.08), 0 10px 30px rgba(37, 99, 235, 0.15);
}
@media (prefers-color-scheme: dark){
  .circle{
    background: radial-gradient(circle at 50% 50%, #0b1220 0%, #0f1c33 58%, #0c213e 100%);
    border-color: rgba(99, 102, 241, 0.55);
    box-shadow: inset 0 0 40px rgba(59, 130, 246, 0.18), 0 10px 30px rgba(37, 99, 235, 0.20);
  }
}
.bigPhase { font-size: 44px; font-weight: 800; color: var(--text); }

/* ========= Meeting Primer grid ========= */
.primer-grid { display: grid; grid-template-columns: 1fr; gap: 12px; }
@media (min-width: 800px) {
  .primer-grid { grid-template-columns: 1fr 1fr; gap: 16px; }
}

footer { visibility: hidden; }
</style>
""",
        unsafe_allow_html=True,
    )


# ==============================
# App Setup & Session Defaults
# ==============================
st.set_page_config(page_title="Calm Coach • Tohid", page_icon="🧘", layout="centered")
render_global_css()

# Store user-tunable voice & basic log DF in session
if "voice_rate" not in st.session_state:
    st.session_state.voice_rate = 0.95
if "voice_pitch" not in st.session_state:
    st.session_state.voice_pitch = 1.05  # slightly brighter
if "voice_lang" not in st.session_state:
    st.session_state.voice_lang = "en-US"
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(
        columns=["time", "module", "duration_sec", "notes", "rating"]
    )


# ==============================
# Voice & TTS Components
# ==============================
def voice_picker_component() -> None:
    """
    Curated device-voice picker (Web Speech API).
    Shows up to 3–5 soft voices (Siri/Apple/Google US + Bangla if present).
    Saves selection to localStorage('cc_voiceName').
    """
    components.html(
        """
<div class="card">
  <div class="title">🎙️ Voice Picker (curated)</div>
  <select id="vp_select" style="width:100%;padding:16px;border-radius:16px;border:1px solid var(--border);background:var(--surface);color:var(--text)"></select>
  <div class="action-row" style="display:flex;gap:12px;margin-top:12px;">
    <button id="vp_save">💾 Save</button>
    <button id="vp_test">🔊 Test voice</button>
  </div>
  <div class="hint small" id="vp_note">Loading voices…</div>
</div>
<script>
function curate(voices){
  const prefs = [
    {re:/siri.*(en|us)/i, label:"Siri (Soft)"},
    {re:/samantha|ava|victoria/i, label:"Apple Female"},
    {re:/google us english/i, label:"Google US English"},
    {re:/uk english.*female|google uk english female/i, label:"UK Soft"},
    {re:/bn|bangla|bengali/i, label:"Bangla (if present)"}
  ];
  let picked = [];
  for (const p of prefs){
    const v = voices.find(v => p.re.test((v.name||"")+" "+(v.lang||"")));
    if (v && !picked.includes(v)) picked.push(v);
    if (picked.length >= 5) break;
  }
  if (picked.length < 3) {
    const extra = voices.filter(v => (v.lang||"").toLowerCase().startsWith("en"));
    for (const v of extra){
      if (!picked.includes(v)) picked.push(v);
      if (picked.length >= 5) break;
    }
  }
  return picked.slice(0,5);
}
function loadVoices() {
  const sel = document.getElementById('vp_select');
  sel.innerHTML = '';
  const chosen = localStorage.getItem('cc_voiceName') || '';
  const all = speechSynthesis.getVoices() || [];
  if (all.length === 0) {
    document.getElementById('vp_note').innerText = "If empty, tap Test once or reload. On iPhone, turn Silent Mode OFF.";
    return;
  }
  const filtered = curate(all);
  filtered.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.name;
    opt.text = (v.name || 'Voice') + ' — ' + (v.lang || '');
    if (v.name === chosen) opt.selected = true;
    sel.appendChild(opt);
  });
  document.getElementById('vp_note').innerText = "Tip: On iPhone, pick a Siri voice for a soft, natural guide.";
}
window.speechSynthesis.onvoiceschanged = loadVoices;
loadVoices();
document.getElementById('vp_save').onclick = () => {
  const name = document.getElementById('vp_select').value;
  localStorage.setItem('cc_voiceName', name);
  alert('Saved voice: ' + name);
};
document.getElementById('vp_test').onclick = () => {
  const name = document.getElementById('vp_select').value;
  const u = new SpeechSynthesisUtterance('Hi Tohid, this is your calm practice voice.');
  const v = speechSynthesis.getVoices().find(x => x.name === name);
  if (v) u.voice = v;
  u.rate = 0.95; u.pitch = 1.05;
  speechSynthesis.cancel(); speechSynthesis.speak(u);
};
</script>
""",
        height=238,
    )


def tts_buttons(text: str, key: str, rate: float | None = None, pitch: float | None = None, lang: str | None = None) -> None:
    """
    Render Speak/Pause/Resume/Stop controls using the browser's Web Speech API.
    - Uses voice saved in localStorage('cc_voiceName') if available.
    - Falls back to a Siri-like voice when present.
    """
    rate = rate or st.session_state.voice_rate
    pitch = pitch or st.session_state.voice_pitch
    lang = lang or st.session_state.voice_lang

    html = f"""
<div class="action-row" style="display:flex;gap:12px;">
  <button onclick="speak_{key}()">▶️ Speak</button>
  <button onclick="pause_{key}()">⏸️ Pause</button>
  <button onclick="resume_{key}()">⏩ Resume</button>
  <button onclick="stop_{key}()">⏹️ Stop</button>
</div>
<script>
const supported_{key} = ('speechSynthesis' in window);
let u_{key} = new SpeechSynthesisUtterance({json.dumps(text)});
u_{key}.rate = {rate}; u_{key}.pitch = {pitch}; u_{key}.lang = "{lang}";
function pickVoice(u) {{
  if(!supported_{key}) return;
  const voices = window.speechSynthesis.getVoices();
  const chosen = localStorage.getItem('cc_voiceName');
  let v = null;
  if (chosen) v = voices.find(x => x.name === chosen) || null;
  if (!v) v = voices.find(x => /siri/i.test((x.name||'')+' '+(x.lang||''))) || null; // prefer Siri if present
  if (v) u.voice = v;
}}
function speak_{key}() {{
  if(!supported_{key}) {{ alert("Voice not supported on this browser."); return; }}
  pickVoice(u_{key});
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u_{key});
}}
function pause_{key}() {{ if(supported_{key}) window.speechSynthesis.pause(); }}
function resume_{key}() {{ if(supported_{key}) window.speechSynthesis.resume(); }}
function stop_{key}() {{ if(supported_{key}) window.speechSynthesis.cancel(); }}
</script>
"""
    components.html(html, height=84)


# ==============================
# Content: Phrase Bank & Tips
# ==============================
def get_meeting_templates() -> Dict[str, Dict[str, List[str]]]:
    """
    Short, neutral, data-first lines for a Module Development Engineer (Intel, fab context).
    Compact lines help break silence and steer discussion.
    """
    common_resets = [
        "Let me summarize in one sentence.",
        "Quick status → result → ask.",
        "One risk and one mitigation next.",
        "I’ll keep it to 30 seconds.",
    ]
    clarifiers = [
        "To confirm, the decision needed today is ____.",
        "If helpful, I can show the SPC chart next.",
        "Do we prefer a 24-hour trial or a full qual?",
    ]
    handoffs = [
        "Looping in techs for on-tool checks after this.",
        "I’ll sync with CMP after this to confirm downstream impact.",
        "Vendor is available this afternoon if we approve.",
    ]
    pushbacks = [
        "Given our WIP risk, I recommend the lower-variance option.",
        "We can take that as a follow-up to keep this decision moving.",
        "If we gate on more data, lead time pushes ~24 hours.",
    ]
    wraps = [
        "That’s the update. Ask: approval for three quals tonight.",
        "No more from me. Next steps are in the notes.",
        "Thanks — I’ll send the SPC snapshot and plan today.",
    ]

    return {
        "1:1": {
            "shortlines": [
                "30-sec update: uptime, seam defects, and one blocker.",
                "Uptime is at 92%, trend improving 48h.",
                "Seam defect rate dropped 18% with the new recipe.",
                "Blocker: edge over-etch on lot 57A; mitigation running.",
                "Ask: approval to run three quals tonight.",
            ]
            + common_resets
            + clarifiers
            + handoffs
            + wraps
        },
        "Stand-up": {
            "shortlines": [
                "Yesterday: recipe A tweaks; Today: run quals; Blockers: none.",
                "Metric: MR rule clears down 3 in last shift.",
                "If no objections, I’ll proceed with recipe A across two lots.",
                "Escalation only if SPC breaches WECO rule 2.",
            ]
            + common_resets
            + wraps
        },
        "Design/Process Review": {
            "shortlines": [
                "Goal: reduce seam defects with minimal cycle time hit.",
                "Option 1 lowers variance; Option 2 improves mean — I recommend 1.",
                "Risk: film stress at 1200 W; mitigation: step-ramp.",
                "Decision needed: move Option 1 to pilot on 3 lots.",
            ]
            + clarifiers
            + pushbacks
            + wraps
        },
        "Cross-team sync": {
            "shortlines": [
                "Impact to CMP is minimal; to Litho, alignment window tight.",
                "Ask: confirm downstream tolerance so we unlock pilot.",
                "I can provide SPC evidence if that helps now.",
            ]
            + handoffs
            + wraps
        },
        "With Techs on tool": {
            "shortlines": [
                "Plan: verify endpoint, log drift, and capture before/after.",
                "Safety first — we’ll pause if sensor flags out of band.",
                "If drift exceeds 2σ, we roll back and notify.",
            ]
            + handoffs
            + wraps
        },
        "Vendor call": {
            "shortlines": [
                "We see drift post-PM; need parameter bounds and fix plan.",
                "Request: remote diag window and patched firmware ETA.",
                "If patch passes two quals, we expand gradually.",
            ]
            + clarifiers
            + wraps
        },
        "Escalation/Issue review": {
            "shortlines": [
                "Issue: yield dip on lots 46–49; suspected over-etch.",
                "Containment: stop on recipe B; move to B-prime.",
                "Ask: approve 6-hour hold while we validate B-prime.",
            ]
            + pushbacks
            + wraps
        },
    }


def get_tips_pack() -> Dict[str, List[str]]:
    """Actionable tips for anxiety, watery eyes, and impression management."""
    return {
        "anxiety": [
            "Do 2–3 physiological sighs 60–90s before speaking.",
            "Drop shoulders, unclench jaw, heels grounded.",
            "Use a reset line: 'Let me summarize in one sentence.'",
        ],
        "eyes": [
            "Blink normally; don’t hold eyes wide.",
            "Triangle gaze (left eye → right eye → eyebrows).",
            "Warm palms on eyes for 10s if watery.",
        ],
        "impression": [
            "Chin level, chest tall, breathe low and slow.",
            "Lead with a number → then meaning → then ask.",
            "Finish with one clear next step.",
        ],
    }


# ==============================
# Interactive Visual Components
# ==============================
def breathing_component(
    pattern: str,
    cycles: int,
    key: str = "breath",
    rate: float | None = None,
    pitch: float | None = None,
    lang: str | None = None,
    chime: bool = True,
) -> None:
    """
    Animated breathing bubble with large INHALE/EXHALE label + optional soft chime.
    Safe templating — no % or {} formatting on the JS.
    """
    rate = rate or st.session_state.voice_rate
    pitch = pitch or st.session_state.voice_pitch
    lang = lang or st.session_state.voice_lang

    patterns = {
        "Box (4-4-4-4)": [
            ("Inhale", 4, "expand"),
            ("Hold", 4, "hold"),
            ("Exhale", 4, "shrink"),
            ("Hold", 4, "hold"),
        ],
        "4-7-8": [("Inhale", 4, "expand"), ("Hold", 7, "hold"), ("Exhale", 8, "shrink")],
        "Physiological Sigh": [
            ("Inhale", 2, "expand"),
            ("Top-up inhale", 2, "expand"),
            ("Exhale", 6, "shrink"),
        ],
    }
    steps = patterns[pattern]

    template = """
<div class="card">
  <div class="title">Paced Breathing — __PATTERN__ × __CYCLES__</div>
  <div class="breath-wrap">
    <div id="circle___KEY__" class="circle">
      <div style="text-align:center;">
        <div id="phaseBig___KEY__" class="bigPhase">Ready</div>
        <div id="count___KEY__" class="timer">—</div>
      </div>
    </div>
  </div>
  <div class="action-row" style="display:flex;gap:12px;">
    <button id="start___KEY__">▶️ Start</button>
    <button id="stop___KEY__">⏹️ Stop</button>
  </div>
  <div class="hint small">Tip: Nose breathing. Exhale slightly longer. If dizzy, stop and breathe normally.</div>
</div>
<script>
const supported___KEY__ = ('speechSynthesis' in window);
const steps___KEY__ = __STEPS__;
const maxCycles___KEY__ = __CYCLES__;
let rate___KEY__ = __RATE__, pitch___KEY__ = __PITCH__, lang___KEY__ = "__LANG__";
let timers___KEY__ = []; let running___KEY__ = false;

// Optional soft chime using WebAudio
function chime___KEY__(){
  try{
    const ctx = new (window.AudioContext||window.webkitAudioContext)();
    const o = ctx.createOscillator(); const g = ctx.createGain();
    o.type = 'sine'; o.frequency.value = 660;
    o.connect(g); g.connect(ctx.destination);
    g.gain.value = 0.0001; o.start();
    g.gain.exponentialRampToValueAtTime(0.02, ctx.currentTime+0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime+0.3);
    o.stop(ctx.currentTime+0.32);
  }catch(e){}
}

function pickVoice___KEY__(u){
  if(!supported___KEY__) return;
  const voices = window.speechSynthesis.getVoices();
  const chosen = localStorage.getItem('cc_voiceName');
  let v = null;
  if (chosen) v = voices.find(x => x.name === chosen) || null;
  if (!v) v = voices.find(x => /siri/i.test((x.name||'')+' '+(x.lang||''))) || null;
  if (v) u.voice = v;
}
function speakNow___KEY__(text){
  if(!supported___KEY__) return;
  const u = new SpeechSynthesisUtterance(text);
  u.rate = rate___KEY__; u.pitch = pitch___KEY__; u.lang = lang___KEY__;
  pickVoice___KEY__(u);
  window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
}

function setPhase___KEY__(label, secs, action){
  const big = document.getElementById("phaseBig___KEY__");
  const count = document.getElementById("count___KEY__");
  const circle = document.getElementById("circle___KEY__");

  big.innerText = label;
  let scale = 1.0;
  if(action === "expand") scale = 1.35;
  else if(action === "shrink") scale = 0.83;
  circle.style.transform = "scale(" + scale + ")";

  let remaining = secs;
  count.innerText = remaining;
  const iv = setInterval(()=>{
    remaining -= 1;
    if(remaining <= 0){ clearInterval(iv); }
    else { count.innerText = remaining; }
  }, 1000);
  timers___KEY__.push(iv);
}

function clearTimers___KEY__(){ for (const t of timers___KEY__) clearInterval(t); timers___KEY__ = []; }

function stopAll___KEY__(){
  running___KEY__ = false;
  clearTimers___KEY__();
  document.getElementById("phaseBig___KEY__").innerText = "Stopped";
  document.getElementById("count___KEY__").innerText = "—";
  document.getElementById("circle___KEY__").style.transform = "scale(1)";
  if(supported___KEY__) window.speechSynthesis.cancel();
}

function startFlow___KEY__(){
  if(running___KEY__) return;
  running___KEY__ = true;
  let cycle = 0;
  function runCycle(){
    if(!running___KEY__) return;
    if(cycle >= maxCycles___KEY__){ stopAll___KEY__(); return; }
    let i = 0;
    function nextStep(){
      if(!running___KEY__) return;
      if(i >= steps___KEY__.length){ cycle += 1; runCycle(); return; }
      const step = steps___KEY__[i];
      const label = step[0]; const secs = step[1]; const action = step[2];
      setPhase___KEY__(label, secs, action);
      __SPEAK_CALL__
      __CHIME_CALL__
      let t = setTimeout(()=>{ i += 1; nextStep(); }, secs*1000);
      timers___KEY__.push(t);
    }
    nextStep();
  }
  runCycle();
}

document.getElementById("start___KEY__").onclick = startFlow___KEY__;
document.getElementById("stop___KEY__").onclick = stopAll___KEY__;
</script>
"""
    html = _tpl(
        template,
        PATTERN=pattern,
        CYCLES=cycles,
        KEY=key,
        STEPS=json.dumps(steps),
        RATE=rate,
        PITCH=pitch,
        LANG=lang,
        SPEAK_CALL=f"speakNow_{key}(label);",
        CHIME_CALL=(f"chime_{key}();" if chime else ""),
    )
    components.html(html, height=450)


def sequence_caller(
    title: str,
    cues: List[str],
    interval_ms: int,
    rounds: int,
    key: str = "seq",
    rate: float | None = None,
    pitch: float | None = None,
    lang: str | None = None,
) -> None:
    """
    Periodic voice + visual cue (e.g., Triangle gaze).
    Uses safe templating to avoid %/{} collisions.
    """
    rate = rate or st.session_state.voice_rate
    pitch = pitch or st.session_state.voice_pitch
    lang = lang or st.session_state.voice_lang

    template = """
<div class="card">
  <div class="title">__TITLE__</div>
  <div id="cue___KEY__" class="status" style="font-size:30px;">Ready</div>
  <div class="timer" id="round___KEY__"></div>
  <div class="action-row" style="display:flex;gap:12px;">
    <button id="start___KEY__">▶️ Start</button>
    <button id="stop___KEY__">⏹️ Stop</button>
  </div>
  <div class="hint small">Keep blinking normally. Tiny natural glances are okay.</div>
</div>
<script>
const cues___KEY__ = __CUES__;
const interval___KEY__ = __INTERVAL__;
const rounds___KEY__ = __ROUNDS__;
const supported___KEY__ = ('speechSynthesis' in window);
let rate___KEY__ = __RATE__, pitch___KEY__ = __PITCH__, lang___KEY__ = "__LANG__";
let timer___KEY__ = null, isRunning___KEY__ = false;

function pickVoice___KEY__(u){
  if(!supported___KEY__) return;
  const voices = window.speechSynthesis.getVoices();
  const chosen = localStorage.getItem('cc_voiceName');
  let v = null;
  if (chosen) v = voices.find(x => x.name === chosen) || null;
  if (!v) v = voices.find(x => /siri/i.test((x.name||'')+' '+(x.lang||''))) || null;
  if (v) u.voice = v;
}
function speak___KEY__(t){
  if(!supported___KEY__) return;
  const u = new SpeechSynthesisUtterance(t);
  u.rate = rate___KEY__; u.pitch = pitch___KEY__; u.lang = lang___KEY__;
  pickVoice___KEY__(u);
  window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
}
function stop___KEY__(){
  isRunning___KEY__ = false;
  if(timer___KEY__) clearInterval(timer___KEY__);
  document.getElementById("cue___KEY__").innerText = "Stopped";
  document.getElementById("round___KEY__").innerText = "";
  if(supported___KEY__) window.speechSynthesis.cancel();
}
function start___KEY__(){
  if(isRunning___KEY__) return;
  isRunning___KEY__ = true;
  let idx = 0; let count = 0;
  document.getElementById("round___KEY__").innerText = "Round 1 of " + rounds___KEY__;
  function tick(){
     if(!isRunning___KEY__) return;
     const text = cues___KEY__[idx % cues___KEY__.length];
     document.getElementById("cue___KEY__").innerText = text;
     speak___KEY__(text);
     idx += 1;
     if(idx % cues___KEY__.length === 0) {
        count += 1;
        document.getElementById("round___KEY__").innerText = "Round " + (count+1) + " of " + rounds___KEY__;
        if(count >= rounds___KEY__) { stop___KEY__(); }
     }
  }
  tick();
  timer___KEY__ = setInterval(tick, interval___KEY__);
}
document.getElementById("start___KEY__").onclick = start___KEY__;
document.getElementById("stop___KEY__").onclick = stop___KEY__;
</script>
"""
    html = _tpl(
        template,
        TITLE=title,
        KEY=key,
        CUES=json.dumps(cues),
        INTERVAL=interval_ms,
        ROUNDS=rounds,
        RATE=rate,
        PITCH=pitch,
        LANG=lang,
    )
    components.html(html, height=280)


# ==============================
# Meeting Primer: Practice & Widgets
# ==============================
def practice_lines_component(
    meeting_type: str, secs_per: int = 8, rounds: int = 1, key: str = "mp_practice"
) -> None:
    """
    Practice loop for default short sentences from the phrase bank.
    - TTS for each line + countdown.
    - Writes a log entry on completion.
    """
    bank = get_meeting_templates()
    lines = bank.get(meeting_type, bank["1:1"])["shortlines"][:12]  # keep it tight
    st.markdown(
        f"**Practice: {meeting_type} short lines** — {secs_per}s each × {rounds} round(s)"
    )
    if st.button("▶️ Start practice", use_container_width=True, key=f"{key}_start"):
        total = 0
        for r in range(rounds):
            for i, line in enumerate(lines):
                st.markdown(
                    f"<div class='card'><div class='title'>Line {i+1}/{len(lines)}</div><div>{line}</div></div>",
                    unsafe_allow_html=True,
                )
                try:
                    tts_buttons(line, key=f"{key}_{r}_{i}")
                except Exception:
                    pass
                ph = st.empty()
                for s in range(secs_per, -1, -1):
                    ph.markdown(f"<div class='timer'>{s}s</div>", unsafe_allow_html=True)
                    time.sleep(1)
                total += secs_per
        save_log(
            "Meeting Primer - practice",
            total,
            notes=f"{meeting_type} {rounds}r x {secs_per}s",
        )
        st.success("Practice done ✅")


def anti_silence_widget(meeting_type: str, haptics: bool = True, key: str = "mp_next") -> None:
    """
    On-tap anti-silence “Next line” widget with optional haptics.
    - Shows the next short sentence from the phrase bank.
    - Speaks it via TTS; optionally triggers a tiny vibration on mobile.
    """
    bank = get_meeting_templates()
    lines = bank.get(meeting_type, bank["1:1"])["shortlines"][:20]
    template = """
<div class="card">
  <div class="title">🗣️ Anti-silence — tap “Next”</div>
  <div id="as_line___KEY__" class="status">Ready</div>
  <div class="action-row" style="display:flex;gap:12px;">
    <button id="as_next___KEY__">Next</button>
    <button id="as_repeat___KEY__">Repeat</button>
  </div>
  <div class="hint small">Tip: say it calmly; then PRA.</div>
</div>
<script>
const supported___KEY__ = ('speechSynthesis' in window);
const lines___KEY__ = __LINES__;
let idx___KEY__ = -1;

function pickVoice___KEY__(u){
  if(!supported___KEY__) return;
  const voices = window.speechSynthesis.getVoices();
  const chosen = localStorage.getItem('cc_voiceName');
  let v = null;
  if (chosen) v = voices.find(x => x.name === chosen) || null;
  if (!v) v = voices.find(x => /siri/i.test((x.name||'')+' '+(x.lang||''))) || null;
  if (v) u.voice = v;
}
function speak___KEY__(t){
  if(!supported___KEY__) return;
  const u = new SpeechSynthesisUtterance(t);
  u.rate = 0.95; u.pitch = 1.05; u.lang = "en-US";
  pickVoice___KEY__(u);
  window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
}
function vibrate___KEY__(){
  try { if("__HAPTICS__"==="true" && navigator.vibrate) navigator.vibrate([40]); } catch(e){}
}
function showLine___KEY__(repeat=false){
  if(!repeat){ idx___KEY__ = (idx___KEY__ + 1) % lines___KEY__.length; }
  const t = lines___KEY__[idx___KEY__];
  document.getElementById("as_line___KEY__").innerText = t;
  speak___KEY__(t);
  vibrate___KEY__();
}
document.getElementById("as_next___KEY__").onclick = ()=>showLine___KEY__(false);
document.getElementById("as_repeat___KEY__").onclick = ()=>showLine___KEY__(true);
</script>
"""
    html = _tpl(
        template,
        KEY=key,
        LINES=json.dumps(lines),
        HAPTICS="true" if haptics else "false",
    )
    components.html(html, height=224)


def build_pra_card(purpose: str, results: str, risks_asks: str, decision_needed: bool) -> None:
    """
    Render a Purpose–Result–Ask summary card and optional TTS cue.
    """
    pra = (
        f"Purpose: {purpose}\n"
        f"Result: {results}\n"
        f"Ask / Risk: {risks_asks}\n"
        f"Decision today: {'Yes' if decision_needed else 'No'}"
    )
    st.markdown(
        f"""<div class="card"><div class="title">P-R-A Card</div>
<pre style="white-space:pre-wrap;font-size:18px">{pra}</pre></div>""",
        unsafe_allow_html=True,
    )
    try:
        tts_buttons("Purpose, result, and ask. Keep it tight.", key="pra_tts")
    except Exception:
        pass


# ==============================
# Logging
# ==============================
def save_log(module: str, duration_sec: int, notes: str = "", rating: int | None = None) -> None:
    """
    Append a row to session log dataframe and try to persist to CSV.
    """
    new = pd.DataFrame(
        [
            {
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "module": module,
                "duration_sec": duration_sec,
                "notes": notes,
                "rating": rating if rating is not None else "",
            }
        ]
    )
    st.session_state.log_df = pd.concat([st.session_state.log_df, new], ignore_index=True)
    try:
        st.session_state.log_df.to_csv(LOG_CSV_PATH, index=False)
    except Exception:
        # Silently ignore write issues (e.g., sandbox/permission)
        pass


# ==============================
# Header & Navigation
# ==============================
st.markdown("### 🧘 Calm Coach — Public Speaking & Meeting Helper")
st.caption("Voice-guided drills for anxiety, eye contact, voice, and energy. Runs in your phone browser (Web Speech).")

# Use segmented control when available; fallback to radio
try:
    menu = st.segmented_control(
        "Choose a module:",
        options=[
            "Quick Calm",
            "Breathing Coach",
            "Voice Warmup",
            "Triangle Gaze",
            "Micro-Exposure",
            "Meeting Primer",
            "Reflect & Logs",
            "Settings",
        ],
        selection_mode="single",
        default="Quick Calm",
    )
except Exception:
    menu = st.radio(
        "Choose a module:",
        options=[
            "Quick Calm",
            "Breathing Coach",
            "Voice Warmup",
            "Triangle Gaze",
            "Micro-Exposure",
            "Meeting Primer",
            "Reflect & Logs",
            "Settings",
        ],
        index=0,
        horizontal=False,
    )


# ==============================
# Modules
# ==============================
if menu == "Settings":
    st.subheader("🎚️ Voice & App Settings")
    st.write("1) Pick **language**, 2) Pick a **curated voice** (e.g., Siri), 3) Adjust rate/pitch.")
    st.session_state.voice_lang = st.selectbox("Voice language", ["en-US", "bn-BD"], index=0)
    st.session_state.voice_rate = st.slider("Voice rate (1.0 normal)", 0.6, 1.6, st.session_state.voice_rate, 0.05)
    st.session_state.voice_pitch = st.slider("Voice pitch (1.0 normal)", 0.6, 1.6, st.session_state.voice_pitch, 0.05)
    voice_picker_component()
    st.info("If you don’t hear audio: make sure Silent Mode is OFF, and tap any Speak button once.")

elif menu == "Quick Calm":
    st.subheader("⚡ 2-minute Panic Reset")
    st.markdown(
        """
- **Step-1:** 5× **physiological sigh** (double inhale → long exhale)  
- **Step-2:** Shoulders down, jaw loose, feet planted  
- **Step-3:** Reset line: *“Let me summarize this in one sentence.”*
"""
    )
    tts_buttons("We will do five physiological sighs. Inhale. Top up inhale. Long exhale. Repeat.", key="qc1")
    breathing_component("Physiological Sigh", cycles=5, key="qc_breath")

    with st.expander("👀 Add face/eye comfort (30s)"):
        st.markdown("Blink gently, roll eyes: left, right, up, down. Warm palms over eyes for 10 seconds.")
        tts_buttons(
            "Blink gently. Roll your eyes left, right, up, down. Warm your palms and cover your eyes.", key="qc2"
        )

    col1, col2 = st.columns(2)
    with col1:
        done = st.button("✅ Log this reset", use_container_width=True)
    with col2:
        rate_now = st.select_slider("How calm now?", options=[1, 2, 3, 4, 5], value=4, help="1 = not calm, 5 = very calm")
    if done:
        save_log("Quick Calm", duration_sec=120, notes="panic reset", rating=rate_now)
        st.success("Logged.")

elif menu == "Breathing Coach":
    st.subheader("🌬️ Guided Breathing")
    pattern = st.selectbox("Pattern", ["Box (4-4-4-4)", "4-7-8", "Physiological Sigh"])
    cycles = st.slider("Number of cycles", 3, 12, 6)
    st.markdown(
        '<div class="hint">Tip: Use 4-7-8 before a talk; Box during meetings; Sigh when heart is spiking.</div>',
        unsafe_allow_html=True,
    )
    breathing_component(pattern, cycles, key="bc", chime=True)
    st.markdown("**Why it helps:** longer exhale → slower heart; box → steady focus.")
    tts_buttons("Start breathing now. Follow the prompts. Keep the exhale soft and longer.", key="bc2")

elif menu == "Voice Warmup":
    st.subheader("🎤 60-second Voice Prep")
    st.markdown(
        """
1) **Hum** “mmm” × 10  
2) **Lip trill** “brrr” × 10  
3) **Siren** “ng—ah” × 5  
4) First sentence **3 times** slowly
"""
    )
    tts_buttons(
        "Hum mmm ten times. Then lip trill brrr. Then siren ng to ah up and down. Now say your first sentence three times, slower each time.",
        key="vw1",
    )
    st.text_input("Your first sentence here:", value="Hello, I’m Tohid. Let me summarize this in one sentence.")
    if st.button("▶️ 60s Timer", use_container_width=True):
        ph = st.empty()
        ph2 = st.empty()
        for s in range(60, -1, -1):
            ph.markdown(f'<div class="timer">{s}s</div>', unsafe_allow_html=True)
            ph2.markdown('<div class="status">Warm up the sound, not loudness.</div>', unsafe_allow_html=True)
            time.sleep(1)
        st.success("Done! Voice should feel easier.")
        save_log("Voice Warmup", 60, notes="mmm/brrr/siren")

elif menu == "Triangle Gaze":
    st.subheader("👁️ Triangle-Gaze Trainer")
    st.caption("Cycle focus: left eye → right eye → eyebrows. Natural eye contact without staring.")
    rounds = st.slider("Rounds (each = Left→Right→Eyebrows)", 3, 20, 8)
    interval = st.slider("Cue every (seconds)", 2, 5, 3)
    sequence_caller("Follow the voice cues", ["Left eye", "Right eye", "Eyebrows"], interval * 1000, rounds, key="tg")
    tts_buttons("Keep normal blinking. Small glances are fine. If eyes water, pause and add tears later.", key="tg2")
    st.markdown('<span class="pill">Tip</span> Blink normally. Don’t hold eyes wide.', unsafe_allow_html=True)

elif menu == "Micro-Exposure":
    st.subheader("🧠 Speaking Practice (prompts + timer)")
    st.caption("Train the body to speak even with faster heartbeat. Short, frequent reps.")
    prompts_default = [
        "Explain your project in one sentence.",
        "Problem → idea → method → result.",
        "Say your opening: Hello, I’m Tohid…",
        "Summarize this slide title in one line.",
        "What’s the key number and why it matters?",
        "Say a reset line: Let me summarize this step.",
    ]
    prompts_txt = st.text_area("Edit prompts (one per line)", value="\n".join(prompts_default), height=160)
    prompts = [p.strip() for p in prompts_txt.split("\n") if p.strip()]
    secs = st.slider("Speaking time per prompt (seconds)", 20, 120, 45)
    rounds = st.slider("How many prompts this session?", 1, min(10, len(prompts)), 4)
    if st.button("▶️ Start session", use_container_width=True):
        total = 0
        for i in range(rounds):
            p = prompts[i % len(prompts)]
            st.markdown(
                f"<div class='card'><div class='title'>Prompt {i+1}/{rounds}</div><div>{p}</div></div>",
                unsafe_allow_html=True,
            )
            tts_buttons(f"Start speaking. {p}. You have {secs} seconds.", key=f"mx{i}")
            ph = st.empty()
            for s in range(secs, -1, -1):
                ph.markdown(f'<div class="timer">{s}s</div>', unsafe_allow_html=True)
                time.sleep(1)
            total += secs
            st.success("Good. Next.")
        save_log("Micro-Exposure", total, notes=f"{rounds} prompts")

elif menu == "Meeting Primer":
    st.subheader("⚙️ World-class Meeting Primer (Intel-tuned)")
    tips = get_tips_pack()

    # --- Config form
    with st.form("primer_form"):
        colA, colB = st.columns(2)
        with colA:
            meeting_type = st.selectbox("Meeting type", MEETING_TYPES, index=0)
            audience = st.multiselect(
                "Stakeholders",
                ["Manager", "Coworkers", "Techs", "Vendors", "Cross-module"],
                default=["Manager", "Coworkers"],
            )
        with colB:
            duration_min = st.slider("Prep timer (min)", 2, 10, 5)
            decision_needed = st.toggle("Decision needed today?")
        purpose = st.text_input("Purpose (1 line)", value="Share W-Dep update and align on blocker.")
        results = st.text_area(
            "Result / Status (bullets)",
            value="- Uptime ↑ to 92%\n- Seam defects −18% with recipe A\n- MR rule clears improved over last 48h",
        )
        risks_asks = st.text_area(
            "Risk & Ask (bullets)", value="- Risk: edge over-etch on lot 57A\n- Ask: approval to run 3 quals tonight"
        )
        opener_hint = st.text_input(
            "First line (say 3× slower)", value="Quick 30-sec update: uptime, defects, and one ask."
        )
        submitted = st.form_submit_button("✨ Build primer")

    if submitted:
        # PRA summary card + short-lines practice + anti-silence tool
        build_pra_card(purpose, results, risks_asks, decision_needed)

        st.markdown("#### Anti-silence button")
        anti_silence_widget(meeting_type, haptics=True, key="asw1")

        st.markdown("#### Practice the default short lines")
        practice_lines_component(meeting_type, secs_per=8, rounds=1, key="prac1")

        st.markdown("#### First line practice")
        st.text(opener_hint)
        try:
            tts_buttons("Say your first line three times, slower each time.", key="mp_firstline")
        except Exception:
            pass

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 6× Box breaths")
            breathing_component("Box (4-4-4-4)", 6, key="mp_box", chime=True)
        with col2:
            st.markdown("#### 3×3s glute squeeze")
            if st.button("▶️ Start 3×3s", use_container_width=True, key="mp_glute"):
                ph = st.empty()
                for rep in range(1, 4):
                    for s in [3, 2, 1]:
                        ph.markdown(
                            f'<div class="status">Hold — rep {rep}/3</div><div class="timer">{s}</div>',
                            unsafe_allow_html=True,
                        )
                        time.sleep(1)
                    st.success(f"Rep {rep} done.")
                save_log("Meeting Primer - glute", 9)

        # Optional prep timer
        if st.button(f"▶️ Start {duration_min}-min prep timer", use_container_width=True, key="mp_timer"):
            ph = st.empty()
            total = duration_min * 60
            for s in range(total, -1, -1):
                mm = s // 60
                ss = s % 60
                ph.markdown(f'<div class="timer">{mm:02d}:{ss:02d}</div>', unsafe_allow_html=True)
                time.sleep(1)
            st.success("Prep done. You’re ready.")
            save_log("Meeting Primer - timer", total)

        # Compact coaching panel
        with st.expander("🧩 Anxiety / Eyes / Impression — quick tips"):
            cc = st.columns(3)
            with cc[0]:
                st.markdown("**Anxiety**")
                for t in tips["anxiety"]:
                    st.markdown(f"- {t}")
            with cc[1]:
                st.markdown("**Eyes**")
                for t in tips["eyes"]:
                    st.markdown(f"- {t}")
            with cc[2]:
                st.markdown("**Impression**")
                for t in tips["impression"]:
                    st.markdown(f"- {t}")

elif menu == "Reflect & Logs":
    st.subheader("📝 Reflection & Progress")
    st.dataframe(st.session_state.log_df, use_container_width=True)

    # Use a form + form_submit_button (fixes 'Missing Submit Button' warning)
    with st.form("logform", clear_on_submit=True):
        module = st.selectbox(
            "Module",
            ["Quick Calm", "Breathing Coach", "Voice Warmup", "Triangle Gaze", "Micro-Exposure", "Meeting Primer", "Other"],
        )
        dur = st.number_input("Duration (sec)", min_value=10, max_value=3600, value=60)
        rating = st.slider("How did it feel?", 1, 5, 4)
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("💾 Save entry")

    if submitted:
        save_log(module, dur, notes, rating)
        st.success("Saved.")

    csv_bytes = st.session_state.log_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", data=csv_bytes, file_name=LOG_CSV_PATH, mime="text/csv")
