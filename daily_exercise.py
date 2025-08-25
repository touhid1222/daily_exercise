import time, json, datetime, pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def _tpl(s: str, **vals) -> str:
    """Very safe string templating: replaces __NAME__ tokens only."""
    for k, v in vals.items():
        s = s.replace(f"__{k}__", str(v))
    return s


# ---------- App Setup ----------
st.set_page_config(page_title="Calm Coach • Tohid", page_icon="🧘", layout="centered")

# ---------- Global CSS (mobile-first, bigger UI) ----------
st.markdown("""
<style>
html, body, [class^="css"]  { font-size: 18px; }
.block-container { padding-top: 0.8rem; padding-bottom: 3rem; }

/* Bigger controls */
.stButton>button, button { 
  width: 100%; padding: 16px 18px; font-size: 18px; 
  border-radius: 14px; border: 1px solid #ddd; 
}
.stDownloadButton>button { padding: 12px 14px; border-radius: 12px; }
.stTextInput>div>div>input, .stTextArea textarea, select {
  font-size: 18px; padding: 12px; border-radius: 12px;
}
.stSlider { padding-top: 4px; }

/* Cards & helpers */
.card {border:1px solid #e7e7e7;border-radius:16px;padding:14px;margin:10px 0;background:#fff}
.title {font-weight:700;font-size:1.25rem;margin-bottom:6px}
.hint {color:#666;font-size:0.92rem}
.small {font-size:0.85rem;}
.center {text-align:center}
.pill {display:inline-block;padding:4px 10px;border-radius:999px;background:#eef5ff;border:1px solid #cfe0ff;font-size:0.9rem;margin:2px 4px}
.timer {font-size:46px;font-weight:700; text-align:center; margin:10px 0;}
.status {font-size:26px;text-align:center;margin:4px 0 10px}

/* Breathing visual — bigger, smoother, with gradient bubble */
.breath-wrap {display:flex;justify-content:center;align-items:center;margin:10px 0 16px}
.circle {
  width: 240px; height: 240px; border-radius: 50%;
  border: 4px solid #9fc5ff;
  background: radial-gradient( circle at 50% 50%, #f7fbff 0%, #e9f3ff 60%, #d7e9ff 100% );
  box-shadow: 0 0 0 rgba(159,197,255,0.6);
  display:flex;justify-content:center;align-items:center;
  transform:scale(1); transition: transform 0.7s ease;
}
.bigPhase { font-size: 34px; font-weight: 700; }

/* Meeting Primer card */
.primer-grid {
  display: grid; grid-template-columns: 1fr; gap: 8px;
}
@media (min-width: 800px) {
  .primer-grid { grid-template-columns: 1fr 1fr; gap: 12px; }
}

footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- Session defaults ----------
if "voice_rate" not in st.session_state: st.session_state.voice_rate = 0.95
if "voice_pitch" not in st.session_state: st.session_state.voice_pitch = 1.05  # slightly brighter
if "voice_lang" not in st.session_state: st.session_state.voice_lang = "en-US"
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=["time","module","duration_sec","notes","rating"])

# ---------- Utilities ----------
def voice_picker_component():
    """
    Curated voice picker: show only 3–5 'sweet' voices if present (Siri/soft female/Google US).
    Falls back to top en voices and Bangla if found.
    Saves selection to localStorage('cc_voiceName').
    """
    components.html("""
<div class="card">
  <div class="title">🎙️ Voice Picker (curated)</div>
  <select id="vp_select" style="width:100%;padding:12px;border-radius:12px;border:1px solid #ddd;"></select>
  <div class="action-row" style="display:flex;gap:8px;margin-top:10px;">
    <button id="vp_save">💾 Save</button>
    <button id="vp_test">🔊 Test voice</button>
  </div>
  <div class="hint small" id="vp_note">Loading voices…</div>
</div>
<script>
function curate(voices){
  // Preferred patterns (order matters). Label makes it friendly for user.
  const prefs = [
    {re:/siri.*(en|us)/i, label:"Siri (Soft)"},
    {re:/samantha|ava|victoria/i, label:"Apple Female"},
    {re:/google us english/i, label:"Google US English"},
    {re:/uk english.*female|google uk english female/i, label:"UK Soft"},
    {re:/bn|bangla|bengali/i, label:"Bangla (if present)"}
  ];
  let picked = [];

  // Try to match preferred patterns first
  for (const p of prefs){
    const v = voices.find(v => p.re.test((v.name||"")+" "+(v.lang||"")));
    if (v && !picked.includes(v)) picked.push(v);
    if (picked.length >= 5) break;
  }

  // Fallback: add a couple of en voices if still short
  if (picked.length < 3) {
    const extra = voices.filter(v => (v.lang||"").toLowerCase().startsWith("en"));
    for (const v of extra){
      if (!picked.includes(v)) picked.push(v);
      if (picked.length >= 5) break;
    }
  }
  // Ensure uniqueness and cap to 5
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
""", height=230)

def tts_buttons(text, key, rate=None, pitch=None, lang=None):
    """Speak/Pause/Resume/Stop using Web Speech API with saved voice (curated)."""
    rate = rate or st.session_state.voice_rate
    pitch = pitch or st.session_state.voice_pitch
    lang = lang or st.session_state.voice_lang
    html = f"""
<div class="action-row" style="display:flex;gap:8px;">
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
    components.html(html, height=70)

def breathing_component(pattern, cycles, key="breath", rate=None, pitch=None, lang=None, chime=True):
    """Animated breathing coach with large INHALE/EXHALE, smooth bubble, optional chime. No % formatting."""
    rate = rate or st.session_state.voice_rate
    pitch = pitch or st.session_state.voice_pitch
    lang = lang or st.session_state.voice_lang

    patterns = {
        "Box (4-4-4-4)": [("Inhale",4,"expand"),("Hold",4,"hold"),("Exhale",4,"shrink"),("Hold",4,"hold")],
        "4-7-8": [("Inhale",4,"expand"),("Hold",7,"hold"),("Exhale",8,"shrink")],
        "Physiological Sigh": [("Inhale",2,"expand"),("Top-up inhale",2,"expand"),("Exhale",6,"shrink")]
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
  <div class="action-row" style="display:flex;gap:8px;">
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
        CHIME_CALL=(f"chime_{key}();" if chime else "")
    )
    components.html(html, height=420)

def sequence_caller(title, cues, interval_ms, rounds, key="seq", rate=None, pitch=None, lang=None):
    """Voice + visual cue every interval (triangle gaze, etc.). Safe templating."""
    rate = rate or st.session_state.voice_rate
    pitch = pitch or st.session_state.voice_pitch
    lang = lang or st.session_state.voice_lang

    template = """
<div class="card">
  <div class="title">__TITLE__</div>
  <div id="cue___KEY__" class="status" style="font-size:28px;">Ready</div>
  <div class="timer" id="round___KEY__"></div>
  <div class="action-row" style="display:flex;gap:8px;">
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
        LANG=lang
    )
    components.html(html, height=260)

def save_log(module, duration_sec, notes="", rating=None):
    new = pd.DataFrame([{
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "module": module,
        "duration_sec": duration_sec,
        "notes": notes,
        "rating": rating if rating is not None else ""
    }])
    st.session_state.log_df = pd.concat([st.session_state.log_df, new], ignore_index=True)
    try:
        st.session_state.log_df.to_csv("calmcoach_logs.csv", index=False)
    except Exception:
        pass

# ---------- Header ----------
st.markdown("### 🧘 Calm Coach — Public Speaking & Meeting Helper")
st.caption("Voice-guided drills for anxiety, eye contact, voice, and energy. Runs in your phone browser (Web Speech).")

# ---------- Navigation ----------
try:
    menu = st.segmented_control(
        "Choose a module:",
        options=[
            "Quick Calm", "Breathing Coach", "Voice Warmup",
            "Triangle Gaze", "Micro-Exposure", "Meeting Primer",
            "Reflect & Logs", "Settings"
        ],
        selection_mode="single",
        default="Quick Calm"
    )
except Exception:
    menu = st.radio(
        "Choose a module:",
        options=[
            "Quick Calm", "Breathing Coach", "Voice Warmup",
            "Triangle Gaze", "Micro-Exposure", "Meeting Primer",
            "Reflect & Logs", "Settings"
        ],
        index=0, horizontal=False
    )

# ---------- Modules ----------
if menu == "Settings":
    st.subheader("🎚️ Voice & App Settings")
    st.write("1) Pick **language**, 2) Pick a **curated voice** (e.g., Siri), 3) Adjust rate/pitch.")
    st.session_state.voice_lang = st.selectbox("Voice language", ["en-US","bn-BD"], index=0)
    st.session_state.voice_rate = st.slider("Voice rate (1.0 normal)", 0.6, 1.6, st.session_state.voice_rate, 0.05)
    st.session_state.voice_pitch = st.slider("Voice pitch (1.0 normal)", 0.6, 1.6, st.session_state.voice_pitch, 0.05)
    voice_picker_component()
    st.info("If you don’t hear audio: make sure Silent Mode is OFF, and tap any Speak button once.")

elif menu == "Quick Calm":
    st.subheader("⚡ 2-minute Panic Reset")
    st.markdown("""
- **Step-1:** 5× **physiological sigh** (double inhale → long exhale)  
- **Step-2:** Shoulders down, jaw loose, feet planted  
- **Step-3:** Reset line: *“Let me summarize this in one sentence.”*
""")
    tts_buttons("We will do five physiological sighs. Inhale. Top up inhale. Long exhale. Repeat.", key="qc1")
    breathing_component("Physiological Sigh", cycles=5, key="qc_breath")
    with st.expander("👀 Add face/eye comfort (30s)"):
        st.markdown("Blink gently, roll eyes: left, right, up, down. Warm palms over eyes for 10 seconds.")
        tts_buttons("Blink gently. Roll your eyes left, right, up, down. Warm your palms and cover your eyes.", key="qc2")
    col1, col2 = st.columns(2)
    with col1:
        done = st.button("✅ Log this reset", use_container_width=True)
    with col2:
        rate_now = st.select_slider("How calm now?", options=[1,2,3,4,5], value=4, help="1 = not calm, 5 = very calm")
    if done:
        save_log("Quick Calm", duration_sec=120, notes="panic reset", rating=rate_now)
        st.success("Logged.")

elif menu == "Breathing Coach":
    st.subheader("🌬️ Guided Breathing")
    pattern = st.selectbox("Pattern", ["Box (4-4-4-4)","4-7-8","Physiological Sigh"])
    cycles = st.slider("Number of cycles", 3, 12, 6)
    st.markdown('<div class="hint">Tip: Use 4-7-8 before a talk; Box during meetings; Sigh when heart is spiking.</div>', unsafe_allow_html=True)
    breathing_component(pattern, cycles, key="bc", chime=True)
    st.markdown("**Why it helps:** longer exhale → slower heart; box → steady focus.")
    tts_buttons("Start breathing now. Follow the prompts. Keep the exhale soft and longer.", key="bc2")

elif menu == "Voice Warmup":
    st.subheader("🎤 60-second Voice Prep")
    st.markdown("""
1) **Hum** “mmm” × 10  
2) **Lip trill** “brrr” × 10  
3) **Siren** “ng—ah” × 5  
4) First sentence **3 times** slowly
""")
    tts_buttons("Hum mmm ten times. Then lip trill brrr. Then siren ng to ah up and down. Now say your first sentence three times, slower each time.", key="vw1")
    st.text_input("Your first sentence here:", value="Hello, I’m Tohid. Let me summarize this in one sentence.")
    if st.button("▶️ 60s Timer", use_container_width=True):
        ph = st.empty(); ph2 = st.empty()
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
    sequence_caller("Follow the voice cues", ["Left eye","Right eye","Eyebrows"], interval*1000, rounds, key="tg")
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
        "Say a reset line: Let me summarize this step."
    ]
    prompts_txt = st.text_area("Edit prompts (one per line)", value="\n".join(prompts_default), height=140)
    prompts = [p.strip() for p in prompts_txt.split("\n") if p.strip()]
    secs = st.slider("Speaking time per prompt (seconds)", 20, 120, 45)
    rounds = st.slider("How many prompts this session?", 1, min(10, len(prompts)), 4)
    if st.button("▶️ Start session", use_container_width=True):
        total = 0
        for i in range(rounds):
            p = prompts[i % len(prompts)]
            st.markdown(f"<div class='card'><div class='title'>Prompt {i+1}/{rounds}</div><div>{p}</div></div>", unsafe_allow_html=True)
            tts_buttons(f"Start speaking. {p}. You have {secs} seconds.", key=f"mx{i}")
            ph = st.empty()
            for s in range(secs, -1, -1):
                ph.markdown(f'<div class="timer">{s}s</div>', unsafe_allow_html=True)
                time.sleep(1)
            total += secs
            st.success("Good. Next.")
        save_log("Micro-Exposure", total, notes=f"{rounds} prompts")

elif menu == "Meeting Primer":
    st.subheader("⚙️ 5-min Pre-Meeting Energy + Intel-style Prep")
    st.markdown("Make it sharp for managers, coworkers, and techs. Build your **P-R-A** (Purpose, Result, Ask).")

    with st.form("primer_form"):
        colA, colB = st.columns(2)
        with colA:
            meeting_type = st.selectbox("Meeting type", ["1:1", "Stand-up", "Design/Process Review", "Cross-team sync", "With Techs on tool"])
            audience = st.multiselect("Stakeholders", ["Manager", "Coworkers", "Techs", "Vendors", "Cross-module"], default=["Manager","Coworkers"])
        with colB:
            duration_min = st.slider("Prep timer (min)", 2, 10, 5)
            decision_needed = st.toggle("Decision needed today?")
        purpose = st.text_input("Purpose (1 line)", value="Share W-Dep update and align on blocker.")
        results = st.text_area("Result / Status (bullets)", value="- Tool uptime ↑ to 92%\n- New recipe reduces seam defects 18%\n- SPC MR rule firing dropped last 48h")
        risks_asks = st.text_area("Risk & Ask (bullets)", value="- Risk: wafer edge over-etch on lot 57A\n- Ask: approval to run 3 more quals tonight")
        opener_hint = st.text_input("First line (say 3× slower)", value="Quick 30-sec update: progress on uptime, seam defects, and one blocker.")
        submit = st.form_submit_button("✨ Build primer")

    if submit:
        # Build a compact PRA card
        pra = f"Purpose: {purpose}\nResult: {results}\nAsk: {risks_asks}\nDecision today: {'Yes' if decision_needed else 'No'}"
        st.markdown(f"""<div class="card"><div class="title">P-R-A Card</div>
<pre style="white-space:pre-wrap;font-size:16px">{pra}</pre></div>""", unsafe_allow_html=True)
        tts_buttons(f"{opener_hint}. Then purpose, result, and ask. Keep it tight.", key="mp_opener")

        # Quick energy routine
        st.markdown("#### 1) Glute squeeze (3× for 3s)")
        if st.button("▶️ Start 3×3s", use_container_width=True):
            ph = st.empty()
            for rep in range(1,4):
                for s in [3,2,1]:
                    ph.markdown(f'<div class="status">Hold — rep {rep}/3</div><div class="timer">{s}</div>', unsafe_allow_html=True)
                    time.sleep(1)
                st.success(f"Rep {rep} done.")
            save_log("Meeting Primer - glute", 9)

        st.markdown("#### 2) Box breaths (6 cycles)")
        breathing_component("Box (4-4-4-4)", 6, key="mp_box", chime=True)

        st.markdown("#### 3) First line practice")
        st.text(opener_hint)
        tts_buttons("Say your first line three times, slower each time.", key="mp2")
        st.info("If heart still races, add 2–3 physiological sighs right before you start.")

    # Optional countdown to start the meeting
    if submit and duration_min:
        if st.button(f"▶️ Start {duration_min}-min prep timer", use_container_width=True):
            ph = st.empty()
            total = duration_min * 60
            for s in range(total, -1, -1):
                mm = s // 60; ss = s % 60
                ph.markdown(f'<div class="timer">{mm:02d}:{ss:02d}</div>', unsafe_allow_html=True)
                time.sleep(1)
            st.success("Prep done. You’re ready.")
            save_log("Meeting Primer - timer", total)

elif menu == "Reflect & Logs":
    st.subheader("📝 Reflection & Progress")
    st.dataframe(st.session_state.log_df, use_container_width=True)

    # ✅ Use a form + st.form_submit_button (fixes 'Missing Submit Button' error)
    with st.form("logform", clear_on_submit=True):
        module = st.selectbox("Module", ["Quick Calm","Breathing Coach","Voice Warmup","Triangle Gaze","Micro-Exposure","Meeting Primer","Other"])
        dur = st.number_input("Duration (sec)", min_value=10, max_value=3600, value=60)
        rating = st.slider("How did it feel?", 1, 5, 4)
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("💾 Save entry")
    if submitted:
        save_log(module, dur, notes, rating)
        st.success("Saved.")

    csv = st.session_state.log_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", data=csv, file_name="calmcoach_logs.csv", mime="text/csv")
