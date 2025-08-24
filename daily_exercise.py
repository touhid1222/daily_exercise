import time, json, datetime, pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------- App Setup ----------
st.set_page_config(page_title="Calm Coach • Tohid", page_icon="🧘", layout="centered")

# Mobile-first CSS
st.markdown("""
<style>
html, body, [class^="css"]  { font-size: 18px; }
.block-container { padding-top: 1rem; padding-bottom: 3rem; }
.big-btn button { width:100%; padding:14px 18px; font-size:18px; border-radius:12px; }
.kbd {display:inline-block;padding:2px 6px;border:1px solid #aaa;border-bottom-width:2px;border-radius:6px;background:#f7f7f7}
.card {border:1px solid #e7e7e7;border-radius:14px;padding:14px;margin:8px 0;background:#fff}
.hint {color:#666;font-size:0.9rem}
.center {text-align:center}
.title {font-weight:700;font-size:1.3rem;margin-bottom:4px}
.timer {font-size:42px;font-weight:700; text-align:center; margin:10px 0;}
.status {font-size:22px;text-align:center;margin:4px 0 10px}
.pill {display:inline-block;padding:4px 10px;border-radius:999px;background:#eef5ff;border:1px solid #cfe0ff;font-size:0.9rem;margin:2px 4px}
.breath-wrap {display:flex;justify-content:center;align-items:center;margin:10px 0 16px}
.circle {width:180px;height:180px;border-radius:50%;border:4px solid #9fc5ff;background:#f0f7ff;
         display:flex;justify-content:center;align-items:center;transform:scale(1);transition:transform 0.6s ease;}
.action-row {display:flex; gap:8px; }
.action-row > div {flex:1}
.small {font-size:0.85rem;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- Session defaults ----------
if "voice_rate" not in st.session_state: st.session_state.voice_rate = 1.0
if "voice_pitch" not in st.session_state: st.session_state.voice_pitch = 1.05  # slightly brighter
if "voice_lang" not in st.session_state: st.session_state.voice_lang = "en-US"
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=["time","module","duration_sec","notes","rating"])

# ---------- Utilities ----------
def voice_picker_component():
    """JS voice picker; stores selection in localStorage('cc_voiceName')."""
    components.html("""
<div class="card">
  <div class="title">🎙️ Voice Picker (device voices)</div>
  <select id="vp_select" style="width:100%;padding:10px;border-radius:10px;border:1px solid #ddd;"></select>
  <div class="action-row" style="margin-top:8px;">
    <div><button id="vp_save">💾 Save</button></div>
    <div><button id="vp_test">🔊 Test voice</button></div>
  </div>
  <div class="hint small" id="vp_note">Loading voices…</div>
</div>
<script>
function loadVoices() {
  const sel = document.getElementById('vp_select');
  sel.innerHTML = '';
  const voices = speechSynthesis.getVoices();
  const chosen = localStorage.getItem('cc_voiceName') || '';
  if (!voices || voices.length === 0) {
    document.getElementById('vp_note').innerText = "If empty, tap Test once or reload. On iPhone, turn Silent Mode OFF.";
    return;
  }
  voices.forEach(v => {
    const opt = document.createElement('option');
    opt.value = v.name;
    opt.text = v.name + ' — ' + v.lang;
    if (v.name === chosen) opt.selected = true;
    sel.appendChild(opt);
  });
  document.getElementById('vp_note').innerText = "Tip: On iPhone, pick a Siri voice for a softer tone.";
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
""", height=210)

def tts_buttons(text, key, rate=None, pitch=None, lang=None):
    """Render Speak/Pause/Resume/Stop using Web Speech API with saved voice."""
    rate = rate or st.session_state.voice_rate
    pitch = pitch or st.session_state.voice_pitch
    lang = lang or st.session_state.voice_lang
    # double braces to escape for f-string
    html = f"""
<div class="action-row">
  <div><button onclick="speak_{key}()">▶️ Speak</button></div>
  <div><button onclick="pause_{key}()">⏸️ Pause</button></div>
  <div><button onclick="resume_{key}()">⏩ Resume</button></div>
  <div><button onclick="stop_{key}()">⏹️ Stop</button></div>
</div>
<script>
const supported_{key} = ('speechSynthesis' in window);
let u_{key} = new SpeechSynthesisUtterance({json.dumps(text)});
u_{key}.rate = {rate};
u_{key}.pitch = {pitch};
u_{key}.lang = "{lang}";
function pickVoice(u) {{
  if(!supported_{key}) return;
  const voices = window.speechSynthesis.getVoices();
  const chosen = localStorage.getItem('cc_voiceName');
  let v = null;
  if (chosen) v = voices.find(x => x.name === chosen) || null;
  if (!v) v = voices.find(x => x.name && x.name.toLowerCase().includes('siri')) || null; // iOS sweet voice
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
    components.html(html, height=60)

def breathing_component(pattern, cycles, key="breath", rate=None, pitch=None, lang=None):
    """Animated breathing coach with voice cues (fixed KeyError by passing rate/pitch/lang)."""
    rate = rate or st.session_state.voice_rate
    pitch = pitch or st.session_state.voice_pitch
    lang = lang or st.session_state.voice_lang

    patterns = {
        "Box (4-4-4-4)": [("Inhale",4,"expand"),("Hold",4,"hold"),("Exhale",4,"shrink"),("Hold",4,"hold")],
        "4-7-8": [("Inhale",4,"expand"),("Hold",7,"hold"),("Exhale",8,"shrink")],
        "Physiological Sigh": [("Inhale",2,"expand"),("Top-up inhale",2,"expand"),("Exhale",6,"shrink")]
    }
    steps = patterns[pattern]
    html = """
<div class="card">
  <div class="title">Paced Breathing — {pattern} × {cycles}</div>
  <div class="breath-wrap"><div id="circle_{key}" class="circle"><span id="count_{key}" class="timer">Ready</span></div></div>
  <div id="phase_{key}" class="status">Press Start</div>
  <div class="action-row">
    <div><button id="start_{key}">▶️ Start</button></div>
    <div><button id="stop_{key}">⏹️ Stop</button></div>
  </div>
  <div class="hint small">Tip: breathe through nose, exhale longer than inhale. If dizzy, stop and breathe normally.</div>
</div>
<script>
const supported_{key} = ('speechSynthesis' in window);
const steps_{key} = {steps_json};
const maxCycles_{key} = {cycles};
let rate_{key} = {rate};
let pitch_{key} = {pitch};
let lang_{key} = "{lang}";
let timers_{key} = [];
let running_{key} = false;

function pickVoice_{key}(u) {{
  if(!supported_{key}) return;
  const voices = window.speechSynthesis.getVoices();
  const chosen = localStorage.getItem('cc_voiceName');
  let v = null;
  if (chosen) v = voices.find(x => x.name === chosen) || null;
  if (!v) v = voices.find(x => x.name && x.name.toLowerCase().includes('siri')) || null;
  if (v) u.voice = v;
}}

function speakNow_{key}(text) {{
  if(!supported_{key}) return;
  const u = new SpeechSynthesisUtterance(text);
  u.rate = rate_{key}; u.pitch = pitch_{key}; u.lang = lang_{key};
  pickVoice_{key}(u);
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}}

function setPhase_{key}(label, secs, action) {{
  const phase = document.getElementById("phase_{key}");
  const count = document.getElementById("count_{key}");
  const circle = document.getElementById("circle_{key}");
  phase.innerText = label + " (" + secs + "s)";
  let scale = 1.0;
  if(action === "expand") scale = 1.25;
  else if(action === "shrink") scale = 0.85;
  circle.style.transform = "scale(" + scale + ")";
  let remaining = secs;
  count.innerText = remaining;
  let iv = setInterval(()=>{{
     remaining -= 1;
     if(remaining <= 0) {{ clearInterval(iv); }}
     else {{ count.innerText = remaining; }}
  }}, 1000);
  timers_{key}.push(iv);
}}

function clearTimers_{key}() {{
  for (const t of timers_{key}) clearInterval(t);
  timers_{key} = [];
}}

function stopAll_{key}() {{
  running_{key} = false;
  clearTimers_{key}();
  document.getElementById("phase_{key}").innerText = "Stopped";
  document.getElementById("count_{key}").innerText = "Ready";
  document.getElementById("circle_{key}").style.transform = "scale(1)";
  if(supported_{key}) window.speechSynthesis.cancel();
}}

function startFlow_{key}() {{
  if(running_{key}) return;
  running_{key} = true;
  let cycle = 0;
  function runCycle() {{
    if(!running_{key}) return;
    if(cycle >= maxCycles_{key}) {{ stopAll_{key}(); return; }}
    let i = 0;
    function nextStep() {{
      if(!running_{key}) return;
      if(i >= steps_{key}.length) {{ cycle += 1; runCycle(); return; }}
      const step = steps_{key}[i];
      const label = step[0]; const secs = step[1]; const action = step[2];
      setPhase_{key}(label, secs, action);
      speakNow_{key}(label);
      let t = setTimeout(()=>{{ i += 1; nextStep(); }}, secs*1000);
      timers_{key}.push(t);
    }}
    nextStep();
  }}
  runCycle();
}}

document.getElementById("start_{key}").onclick = startFlow_{key};
document.getElementById("stop_{key}").onclick = stopAll_{key};
</script>
""".format(
        pattern=pattern, cycles=cycles, key=key,
        steps_json=json.dumps(steps), rate=rate, pitch=pitch, lang=lang
    )
    components.html(html, height=360)

def sequence_caller(title, cues, interval_ms, rounds, key="seq", rate=None, pitch=None, lang=None):
    """Voice + visual cue every interval (triangle gaze, etc.)."""
    rate = rate or st.session_state.voice_rate
    pitch = pitch or st.session_state.voice_pitch
    lang = lang or st.session_state.voice_lang
    html = """
<div class="card">
  <div class="title">{title}</div>
  <div id="cue_{key}" class="status" style="font-size:28px;">Ready</div>
  <div class="timer" id="round_{key}"></div>
  <div class="action-row">
    <div><button id="start_{key}">▶️ Start</button></div>
    <div><button id="stop_{key}">⏹️ Stop</button></div>
  </div>
  <div class="hint small">Keep blinking normally. Tiny natural glances are okay.</div>
</div>
<script>
const cues_{key} = {cues};
const interval_{key} = {interval};
const rounds_{key} = {rounds};
const supported_{key} = ('speechSynthesis' in window);
let rate_{key} = {rate};
let pitch_{key} = {pitch};
let lang_{key} = "{lang}";
let timer_{key} = null;
let isRunning_{key} = false;

function pickVoice_{key}(u) {{
  if(!supported_{key}) return;
  const voices = window.speechSynthesis.getVoices();
  const chosen = localStorage.getItem('cc_voiceName');
  let v = null;
  if (chosen) v = voices.find(x => x.name === chosen) || null;
  if (!v) v = voices.find(x => x.name && x.name.toLowerCase().includes('siri')) || null;
  if (v) u.voice = v;
}}

function speak_{key}(t) {{
  if(!supported_{key}) return;
  const u = new SpeechSynthesisUtterance(t);
  u.rate = rate_{key}; u.pitch = pitch_{key}; u.lang = lang_{key};
  pickVoice_{key}(u);
  window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
}}

function stop_{key}() {{
  isRunning_{key} = false;
  if(timer_{key}) clearInterval(timer_{key});
  document.getElementById("cue_{key}").innerText = "Stopped";
  document.getElementById("round_{key}").innerText = "";
  if(supported_{key}) window.speechSynthesis.cancel();
}}

function start_{key}() {{
  if(isRunning_{key}) return;
  isRunning_{key} = true;
  let idx = 0; let count = 0;
  document.getElementById("round_{key}").innerText = "Round 1 of " + rounds_{key};
  function tick() {{
     if(!isRunning_{key}) return;
     const text = cues_{key}[idx % cues_{key}.length];
     document.getElementById("cue_{key}").innerText = text;
     speak_{key}(text);
     idx += 1;
     if(idx % cues_{key}.length === 0) {{
        count += 1;
        document.getElementById("round_{key}").innerText = "Round " + (count+1) + " of " + rounds_{key};
        if(count >= rounds_{key}) {{ stop_{key}(); }}
     }}
  }}
  tick();
  timer_{key} = setInterval(tick, interval_{key});
}}

document.getElementById("start_{key}").onclick = start_{key};
document.getElementById("stop_{key}").onclick = stop_{key};
</script>
""".format(
        title=title, key=key, cues=json.dumps(cues),
        interval=interval_ms, rounds=rounds,
        rate=rate, pitch=pitch, lang=lang
    )
    components.html(html, height=250)

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
    # Fallback if Streamlit version doesn't support segmented_control
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
    st.write("1) Pick **language**, 2) Pick a **device voice** (e.g., Siri), 3) Adjust rate/pitch.")
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
    cycles = st.slider("Number of cycles", 3, 10, 5)
    st.markdown('<div class="hint">Tip: Use 4-7-8 before a talk; Box during meetings; Sigh when heart is spiking.</div>', unsafe_allow_html=True)
    breathing_component(pattern, cycles, key="bc")
    st.markdown("**Why it helps:** longer exhale = slows heart; box = steady focus.")
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
    st.subheader("⚙️ 5-min Pre-Meeting Energy")
    st.markdown("""
- **Body reset:** stand tall, feet planted, shoulders down  
- **Glute squeeze:** 3× for 3s  
- **Box breaths:** 6 cycles  
- **First line practice:** 3 times, slower
""")
    tts_buttons("Stand tall. Shoulders down. Squeeze glutes three times for three seconds. Now we do six box breaths. Then say your first line three times, slower each time.", key="mp1")
    st.markdown("#### 1) Glute squeeze (3×)")
    if st.button("▶️ Start 3×3s", use_container_width=True):
        ph = st.empty()
        for rep in range(1,4):
            ph.markdown(f'<div class="status">Hold — rep {rep}/3</div><div class="timer">3</div>', unsafe_allow_html=True); time.sleep(1)
            ph.markdown(f'<div class="status">Hold — rep {rep}/3</div><div class="timer">2</div>', unsafe_allow_html=True); time.sleep(1)
            ph.markdown(f'<div class="status">Hold — rep {rep}/3</div><div class="timer">1</div>', unsafe_allow_html=True); time.sleep(1)
            st.success(f"Rep {rep} done.")
        save_log("Meeting Primer - glute", 9)
    st.markdown("#### 2) Box breaths (6 cycles)")
    breathing_component("Box (4-4-4-4)", 6, key="mp_box")
    st.markdown("#### 3) First line")
    first_line = st.text_input("Type your first sentence", value="Quick update in 30 seconds: [point-1], [point-2], blocker is [X].")
    tts_buttons("Say your first line three times, slower each time.", key="mp2")
    st.info("If heart still races, add 2–3 physiological sighs right before you start.")

elif menu == "Reflect & Logs":
    st.subheader("📝 Reflection & Progress")
    st.dataframe(st.session_state.log_df, use_container_width=True)
    with st.form("logform"):
        module = st.selectbox("Module", ["Quick Calm","Breathing Coach","Voice Warmup","Triangle Gaze","Micro-Exposure","Meeting Primer","Other"])
        dur = st.number_input("Duration (sec)", min_value=10, max_value=3600, value=60)
        rating = st.slider("How did it feel?", 1, 5, 4)
    notes = st.text_area("Notes (optional)")
    if st.button("Save entry"):
        save_log(module, dur, notes, rating)
        st.success("Saved.")
    csv = st.session_state.log_df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", data=csv, file_name="calmcoach_logs.csv", mime="text/csv")
