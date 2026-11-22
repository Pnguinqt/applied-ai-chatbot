"""
TechBuddy - an AI chatbot for computer hardware issues (Streamlit)

Run:
    pip install streamlit anthropic
    export ANTHROPIC_API_KEY="your-key"     # optional - without it, offline mode is used
    streamlit run techbuddy_app.py
"""
import os
import re
from datetime import datetime
import time

import streamlit as st

from src.services.llm_service import generate_response
# ----------------------------------------------------------------- config
st.set_page_config(page_title="TechBuddy", page_icon="🖥️", layout="centered")

SYSTEM_PROMPT = """You are TechBuddy, a friendly expert assistant that ONLY helps with computer hardware:
CPUs, GPUs, RAM, motherboards, storage (SSD/HDD/NVMe), power supplies, cooling, fans, laptops,
monitors, peripherals, PC building, upgrades, compatibility, benchmarking, thermals, and troubleshooting
boot, display, noise, power and performance problems.
Rules:
- If the question is not about computers/hardware, politely decline in one sentence and steer back to hardware.
- Give clear, numbered troubleshooting steps, safest/cheapest checks first.
- Ask for specs (model, OS, symptoms, recent changes) when you need them.
- Warn about safety (unplug power, ESD, PSU capacitors) when relevant.
- Keep answers concise and practical. Use markdown."""

CARDS = [
    ("🩺", "Diagnose my PC",
     "Describe symptoms like crashes, freezes or slowdowns and get a step-by-step diagnosis.",
     "Run Diagnosis",
     "My PC keeps freezing and crashing randomly. Help me diagnose the hardware cause."),
    ("🌡️", "Overheating issues?",
     "Check CPU/GPU temperatures, fan behavior and airflow, and learn how to cool things down.",
     "Check Thermals",
     "My computer is running hot and the fans are loud. How do I find and fix the cause?"),
    ("⚡", "What should I upgrade?",
     "Find the best upgrade for your budget: RAM, SSD, GPU or CPU, with compatibility tips.",
     "Get Upgrade Advice",
     "What is the best hardware upgrade to make my older PC faster? Ask me what you need to know."),
]

# ----------------------------------------------------------------- state
ss = st.session_state
ss.setdefault("messages", [])
ss.setdefault("pending", None)
ss.setdefault("user_name", "there")


# ----------------------------------------------------------------- styling
st.markdown(
    """
<style>
#MainMenu, footer, header {visibility: hidden;}
.stApp {background: linear-gradient(135deg,#f4f5fb 0%,#ffffff 45%,#f3f1fb 100%);}
.block-container {max-width: 860px; padding-top: 1.2rem; padding-bottom: 7rem;}

/* pill buttons */
.stButton > button, .stDownloadButton > button, [data-testid="stPopover"] > div > button {
    border-radius: 999px; border: 1px solid #e6e7ee; background: #fff;
    font-size: 0.78rem; font-weight: 600; color: #1f2230; padding: .25rem .9rem;
    box-shadow: 0 1px 4px rgba(20,20,60,.05);
}
.stButton > button:hover, .stDownloadButton > button:hover {border-color:#8b8fd8; color:#4a4fc0;}

/* welcome */
.tb-badge {width:46px;height:46px;border-radius:50%;margin:3.2rem auto 1.1rem;display:flex;
    align-items:center;justify-content:center;font-size:1.3rem;background:#fff;
    box-shadow:0 4px 16px rgba(80,80,160,.18);}
.tb-hello {text-align:center;font-size:2rem;font-weight:600;color:#1c1e2b;margin:0;}
.tb-hello span {color:#6b6e80;}
.tb-sub {text-align:center;color:#6b6e80;font-size:.85rem;margin:.4rem 0 2.2rem;}

/* suggestion cards */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 16px; border: 1px solid #ececf3; background: rgba(255,255,255,.75);
    box-shadow: 0 2px 10px rgba(20,20,60,.04);
}
.tb-card-icon {font-size:1.1rem;margin-bottom:.5rem;}
.tb-card-title {font-weight:600;font-size:.95rem;color:#1c1e2b;margin-bottom:.35rem;}
.tb-card-desc {font-size:.74rem;color:#8a8d9e;line-height:1.45;min-height:3.2rem;margin-bottom:.6rem;}

/* chat */
[data-testid="stChatMessage"] {background: rgba(255,255,255,.8); border:1px solid #ececf3;
    border-radius:16px; padding:.8rem 1rem;}
[data-testid="stChatInput"] {border-radius: 999px;}
[data-testid="stChatInput"] textarea {font-size:.9rem;}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------- offline brain
KB = [
    (("overheat", "hot", "temperature", "temp", "thermal", "throttl", "fan", "loud", "noisy"),
     "### 🌡️ Heat & fan troubleshooting\n"
     "1. **Check temps** with HWMonitor, HWiNFO or Core Temp. Idle >60 °C or load >90 °C is a problem.\n"
     "2. **Clean the dust**: power off, unplug, and blow out heatsinks, fans and filters with compressed air.\n"
     "3. **Check airflow**: intake fans in front, exhaust at the back or top. Keep cables out of the way.\n"
     "4. **Fan curves**: set a more aggressive curve in BIOS or a tool like FanControl.\n"
     "5. **Re-paste the CPU** (every 3-5 years) if temps spike quickly under load.\n"
     "6. Laptops: use a stand or cooling pad and avoid soft surfaces.\n\n"
     "What CPU/GPU do you have, and what temps are you seeing?"),
    (("freez", "crash", "bsod", "blue screen", "restart", "reboot", "random shut", "unstable"),
     "### 🩺 Crashes & freezes\n"
     "1. **Test RAM**: run Windows Memory Diagnostic or MemTest86 overnight.\n"
     "2. **Check temps** (see overheating) since thermal shutdowns look like random crashes.\n"
     "3. **Check disk health** with CrystalDiskInfo (look for reallocated or pending sectors).\n"
     "4. **Reseat** RAM and GPU, and try one RAM stick at a time.\n"
     "5. **Disable XMP/EXPO** to rule out unstable memory overclocks.\n"
     "6. **Suspect the PSU** if crashes happen under heavy GPU load.\n\n"
     "Does it happen idle, in games, or at boot? Any error code on the blue screen?"),
    (("no display", "no signal", "black screen", "no post", "won't boot", "wont boot", "doesn't boot",
      "not turning on", "won't turn on", "beep", "no power", "dead"),
     "### 🔌 Won't boot / no display\n"
     "1. Check the PSU switch, wall outlet and the 24-pin + CPU power connectors.\n"
     "2. Plug the monitor into the **GPU**, not the motherboard (unless you have no GPU).\n"
     "3. **Reseat RAM** and try a single stick in slot A2 (check the manual).\n"
     "4. Clear CMOS (remove the coin battery for 5 minutes).\n"
     "5. Unplug everything non-essential: drives, USB devices and extra fans.\n"
     "6. Note the **motherboard debug LEDs/beep codes** (CPU, DRAM, VGA, BOOT) to find the failing part.\n\n"
     "Do any lights or fans turn on when you press the power button?"),
    (("slow", "lag", "stutter", "performance", "fps", "bottleneck", "speed up", "faster"),
     "### 🚀 Performance issues\n"
     "1. Open Task Manager and check what is maxed out: **CPU, RAM, Disk or GPU**.\n"
     "2. **Disk at 100%?** Move the OS to an SSD. This is the single biggest speed-up on old PCs.\n"
     "3. **RAM >80% used?** 16 GB is the modern minimum; 32 GB for heavy workloads.\n"
     "4. Make sure RAM runs in **dual channel** and XMP/EXPO is enabled.\n"
     "5. Check thermal throttling (see overheating).\n"
     "6. Update chipset and GPU drivers.\n\n"
     "Share your CPU, GPU, RAM and storage and I'll point at the real bottleneck."),
    (("upgrade", "buy", "worth", "recommend", "build", "compatib", "which gpu", "which cpu"),
     "### ⚡ Upgrade guide (best value first)\n"
     "1. **HDD → SATA/NVMe SSD**: huge boost to boot and load times.\n"
     "2. **RAM to 16-32 GB** (dual channel, matching speed).\n"
     "3. **GPU** for gaming, video and AI work. Check PSU wattage and case clearance first.\n"
     "4. **CPU** last. It often requires a new motherboard and RAM.\n\n"
     "To check compatibility I need: CPU model, motherboard model, PSU wattage, "
     "current GPU/RAM, and your budget and use case."),
    (("ram", "memory", "ddr"),
     "### 🧠 RAM help\n"
     "- Match the type (**DDR4 vs DDR5**) to your motherboard. They are not interchangeable.\n"
     "- Use **2 sticks** (dual channel) rather than 1 for better performance.\n"
     "- Enable **XMP/EXPO** in BIOS to reach the rated speed.\n"
     "- Mixing kits can cause instability, so buy a matched kit.\n\n"
     "What's your motherboard or laptop model? I can tell you the max supported RAM."),
    (("ssd", "hdd", "nvme", "storage", "hard drive", "disk", "sata", "m.2"),
     "### 💾 Storage help\n"
     "- **NVMe (M.2)** is the fastest, **SATA SSD** is the cheap upgrade, **HDD** is for bulk storage.\n"
     "- Check your board has a free M.2 slot (and whether it's PCIe 3.0/4.0/5.0).\n"
     "- Use **CrystalDiskInfo** to check health; clicking or 'Caution' status means back up now.\n"
     "- Keep 10-20% of an SSD free to maintain speed.\n\n"
     "Are you trying to fix a failing drive or pick a new one?"),
    (("gpu", "graphics", "nvidia", "amd", "radeon", "geforce", "artifact", "vram"),
     "### 🎮 GPU troubleshooting\n"
     "1. Reseat the card and check **all PCIe power cables** are fully clicked in.\n"
     "2. Use **DDU** to clean-install the latest driver.\n"
     "3. Watch temps and clocks in MSI Afterburner. Artifacts usually mean heat, bad VRAM or an OC.\n"
     "4. Check the PSU can handle the card's recommended wattage.\n"
     "5. Test in another PCIe slot or PC if possible.\n\n"
     "Which GPU is it, and what exactly do you see on screen?"),
    (("psu", "power supply", "watt", "wattage"),
     "### 🔋 Power supply\n"
     "- Add up your CPU + GPU power draw, then add **30-40% headroom**.\n"
     "- Prefer 80+ Bronze or better from reputable brands.\n"
     "- Symptoms of a failing PSU: random shutdowns under load, clicking or burning smell, no power.\n"
     "- ⚠️ Never open a PSU. Capacitors hold a dangerous charge even when unplugged.\n\n"
     "What parts are you running?"),
    (("battery", "laptop", "charge", "charging"),
     "### 💻 Laptop battery & charging\n"
     "1. Try a different outlet and check the charger tip for damage.\n"
     "2. Check battery health (`powercfg /batteryreport` on Windows).\n"
     "3. Update BIOS and chipset drivers.\n"
     "4. Cap charge at 80% if your laptop supports it, to extend battery life.\n"
     "5. Swelling battery? **Stop using it** and get it replaced.\n\n"
     "What's the laptop model?"),
    (("monitor", "screen", "display", "flicker", "refresh", "hdmi", "displayport"),
     "### 🖥️ Monitor & display\n"
     "1. Try a different cable (DisplayPort is best for high refresh rates).\n"
     "2. Plug into the GPU, not the motherboard.\n"
     "3. Set the refresh rate in Windows Display Settings (Advanced).\n"
     "4. Flicker? Disable G-Sync/FreeSync to test, and update the GPU driver.\n\n"
     "What monitor and cable are you using?"),
]
HARDWARE_WORDS = ("pc", "computer", "cpu", "motherboard", "bios", "usb", "keyboard", "mouse", "laptop",
                  "desktop", "hardware", "windows", "driver", "wifi", "network card", "case", "cooler")


def offline_reply(prompt: str) -> str:
    text = prompt.lower()
    scored = [(sum(k in text for k in keys), ans) for keys, ans in KB]
    best = max(scored, key=lambda x: x[0])
    if best[0] > 0:
        return best[1]
    if any(w in text for w in HARDWARE_WORDS):
        return ("I can help with that! 🔧 Tell me more:\n\n"
                "1. Your **device/model** and OS\n2. The **exact symptom** and when it started\n"
                "3. Any **recent changes** (new part, driver, update, move)\n\n"
                "Then I'll walk you through the fix.")
    return ("I'm TechBuddy, and I only help with **computer hardware** 🖥️ (PCs, laptops, parts, "
            "upgrades and troubleshooting). Ask me about overheating, slow performance, boot issues, "
            "or what to upgrade!")



def stream_reply(history):
    """
    Uses Gemini to generate hardware-related responses.
    Falls back to the offline knowledge base if Gemini fails.
    """

    print("\n[TechBuddy] Sending request to Gemini...", flush=True)

    try:
        answer = generate_response(
            history=history,
            system_instruction=SYSTEM_PROMPT,
        )

        print("[TechBuddy] Gemini responded successfully.", flush=True)

        yield answer

    except Exception as e:
        print(f"[TechBuddy] Gemini failed: {repr(e)}", flush=True)
        print("[TechBuddy] Switching to offline mode.", flush=True)

        yield (
            f"⚠️ Gemini is currently unavailable "
            f"({type(e).__name__}). Using offline mode instead.\n\n"
        )

        answer = offline_reply(history[-1]["content"])

        for word in re.findall(r"\S+\s*", answer):
            yield word
            time.sleep(0.015)

# ----------------------------------------------------------------- top bar
def greeting() -> str:
    h = datetime.now().hour
    return "Good Morning" if h < 12 else "Good Afternoon" if h < 18 else "Good Evening"


def transcript() -> str:
    lines = ["TechBuddy chat", datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
    for m in ss.messages:
        who = "You" if m["role"] == "user" else "TechBuddy"
        lines += [f"{who}: {m['content']}", ""]
    return "\n".join(lines)


left, mid, right = st.columns([1, 6, 3])
with left:
    with st.popover("🔍"):
        q = st.text_input("Search this chat", placeholder="Search…", label_visibility="collapsed")
        if q:
            hits = [m["content"] for m in ss.messages if q.lower() in m["content"].lower()]
            if hits:
                for h in hits[:5]:
                    st.caption(h[:140] + ("…" if len(h) > 140 else ""))
            else:
                st.caption("No matches.")
with mid:
    c1, c2 = st.columns([1.3, 5])
    with c1:
        if st.button("＋ New Chat"):
            ss.messages, ss.pending = [], None
            st.rerun()
    with c2:
        with st.popover("⚙️ Settings"):
            st.caption("TechBuddy AI Assistant")
            st.caption("Powered by Google Gemini")
            st.caption("Specialized in computer hardware assistance.")
with right:
    st.download_button("⬆ Share", transcript(), file_name="techbuddy_chat.txt",
                       disabled=not ss.messages)

# ----------------------------------------------------------------- welcome screen
if not ss.messages and ss.pending is None:
    st.markdown('<div class="tb-badge">✨</div>', unsafe_allow_html=True)
    st.markdown(
    f'<h1 class="tb-hello">{greeting()}, <span>Buddy!</span></h1>',
    unsafe_allow_html=True,
)
    st.markdown('<p class="tb-sub">Hey there! What hardware problem can I help you fix today?</p>',
                unsafe_allow_html=True)
    cols = st.columns(3)
    for col, (icon, title, desc, btn, prompt_text) in zip(cols, CARDS):
        with col, st.container(border=True):
            st.markdown(
                f'<div class="tb-card-icon">{icon}</div><div class="tb-card-title">{title}</div>'
                f'<div class="tb-card-desc">{desc}</div>', unsafe_allow_html=True)
            if st.button(btn, key=f"card_{title}", use_container_width=True):
                ss.pending = prompt_text
                st.rerun()

# ----------------------------------------------------------------- chat history
for m in ss.messages:
    with st.chat_message(m["role"], avatar="🧑‍💻" if m["role"] == "user" else "🖥️"):
        st.markdown(m["content"])

# ----------------------------------------------------------------- input + response
typed = st.chat_input("Describe your computer problem…")
if typed:
    ss.pending = typed

if ss.pending:
    prompt, ss.pending = ss.pending, None
    ss.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🖥️"):
        reply = st.write_stream(stream_reply(ss.messages))
    ss.messages.append({"role": "assistant", "content": reply})
    st.rerun()