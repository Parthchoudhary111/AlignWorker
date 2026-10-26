import os
import sys
import time
import importlib
import streamlit as st

# Setup Path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import app.agent.dynamic_agent
importlib.reload(app.agent.dynamic_agent)
from app.agent.dynamic_agent import DynamicAlignWorker, StepRecord
from app.mock_portal.database import list_invoices, reset_db

st.set_page_config(
    page_title="AlignWorker // CyberDeck Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Futuristic Cyber Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
    
    .stApp {
        background-color: #060911;
        background-image: 
            radial-gradient(circle at 15% 15%, rgba(0, 245, 255, 0.05) 0%, transparent 40%),
            radial-gradient(circle at 85% 85%, rgba(168, 85, 247, 0.06) 0%, transparent 45%);
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 0.05em;
        color: #fff !important;
    }
    
    .stTextInput > div > div > input {
        background-color: rgba(14, 21, 38, 0.9) !important;
        color: #00f5ff !important;
        font-family: 'JetBrains Mono', monospace !important;
        border: 1px solid rgba(0, 245, 255, 0.3) !important;
        border-radius: 8px !important;
        box-shadow: 0 0 15px rgba(0, 245, 255, 0.1) !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #00f5ff 0%, #0284c7 100%) !important;
        color: #000 !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        box-shadow: 0 0 20px rgba(0, 245, 255, 0.35) !important;
    }
    
    .step-card {
        background: rgba(14, 23, 42, 0.85);
        border: 1px solid rgba(0, 245, 255, 0.2);
        border-left: 4px solid #00f5ff;
        padding: 14px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-family: 'JetBrains Mono', monospace;
    }
</style>
""", unsafe_allow_html=True)

# Top Telemetry Header
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 18px; background: rgba(14, 21, 38, 0.85); border: 1px solid rgba(0, 245, 255, 0.2); border-radius: 10px; margin-bottom: 20px;">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="display: inline-block; width: 10px; height: 10px; background: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981;"></span>
        <span style="font-family: 'Rajdhani', sans-serif; font-size: 1.1rem; font-weight: 700; color: #fff;">
            ALIGN<span style="color: #00f5ff;">//WORKER</span> &bull; AUTONOMOUS NEURAL CYBERDECK
        </span>
    </div>
    <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; color: #94a3b8;">
        FLAGSHIP STUDIO ACTIVE &bull; <a href="http://127.0.0.1:8000/agent" target="_blank" style="color: #00f5ff; text-decoration: underline;">OPEN NATIVE WEB STUDIO</a>
    </div>
</div>
""", unsafe_allow_html=True)

st.title("⚡ Autonomous Task Agent Studio")
st.caption("Direct neural decomposition & ReAct execution via Playwright Chromium automation.")

# Session state initialization
if "latest_screenshot" not in st.session_state:
    st.session_state["latest_screenshot"] = None
if "history" not in st.session_state:
    st.session_state["history"] = []
if "status_msg" not in st.session_state:
    st.session_state["status_msg"] = None

# Top Controls
col_input, col_btn = st.columns([4, 1])

with col_input:
    user_prompt = st.text_input(
        "Natural Language Objective / Instructions:",
        value="Navigate to http://127.0.0.1:8000/invoices/new, create an invoice for vendor 'Anthropic AI' with amount $7,200.00 and due date 2026-12-10 under Software Subscriptions, and submit.",
        placeholder="Type any instructions for the agent..."
    )

with col_btn:
    st.write("")
    st.write("")
    run_clicked = st.button("🚀 EXECUTE", type="primary", use_container_width=True)

# Quick Preset Buttons
st.markdown("**Tactical Scenario Triggers:**")
p1, p2, p3, p4 = st.columns(4)
if p1.button("📄 Acme Corp PDF"):
    st.session_state["prompt_override"] = "Read invoice_acme_corp.pdf from sample_data, navigate to http://127.0.0.1:8000/invoices/new, enter the details, and verify."
    st.rerun()
if p2.button("🔄 Apex Date Self-Correction"):
    st.session_state["prompt_override"] = "Read invoice_apex_logistics.pdf, navigate to http://127.0.0.1:8000/invoices/new, fill the form, recover from any date errors, and verify."
    st.rerun()
if p3.button("📝 NVIDIA AI Hardware"):
    st.session_state["prompt_override"] = "Navigate to http://127.0.0.1:8000/invoices/new and create an invoice for vendor 'NVIDIA AI Systems' with amount $18,400.00 and due date 2026-12-15 under Hardware & Office Supplies, and submit."
    st.rerun()
if p4.button("🗑️ Reset ERP Database"):
    reset_db()
    st.session_state["history"] = []
    st.session_state["latest_screenshot"] = None
    st.session_state["status_msg"] = "Database reset to initial state."
    st.rerun()

if "prompt_override" in st.session_state:
    user_prompt = st.session_state.pop("prompt_override")

st.divider()

# Main Workspace: Split Screen
left_pane, right_pane = st.columns([1.1, 1.2])

with left_pane:
    st.subheader("🧠 Neural Reasoning & Trace")
    log_container = st.container()

with right_pane:
    st.subheader("👁️ Optical Telemetry & Ledger")
    browser_display = st.empty()
    st.markdown("##### 📊 Live Records in AcmeFlow ERP (`erp.db`)")
    db_display = st.empty()

    # Render current state
    if st.session_state["latest_screenshot"] and os.path.exists(st.session_state["latest_screenshot"]):
        browser_display.image(st.session_state["latest_screenshot"], caption="Live Optical Feed", use_column_width=True)
    else:
        browser_display.info("The browser screenshot will update here live as the agent executes actions.")

    db_display.dataframe(list_invoices(), use_container_width=True)

# Render historical steps if present
if st.session_state["history"] and not run_clicked:
    with log_container:
        for s in st.session_state["history"]:
            with st.expander(f"Step {s['step']}: {s['action']}", expanded=False):
                st.markdown(f"**Thought:** {s['thought']}")
                st.markdown(f"**Action:** `{s['action']}`(`{s['action_input']}`)")
                st.markdown(f"**Observation:** `{s['observation']}`")

if st.session_state["status_msg"] and not run_clicked:
    with left_pane:
        st.success(st.session_state["status_msg"])

# Execution Logic
if run_clicked and user_prompt.strip():
    st.session_state["history"] = []
    
    with left_pane:
        st.info(f"**Executing Objective:** {user_prompt}")
        status_placeholder = st.empty()

    def on_step(step: StepRecord):
        obs_str = str(step.observation)
        if len(obs_str) > 200:
            obs_str = obs_str[:200] + "..."
        st.session_state["history"].append({
            "step": step.step_number,
            "thought": step.thought,
            "action": step.action,
            "action_input": step.action_input,
            "observation": obs_str
        })

        with log_container:
            with st.expander(f"Step {step.step_number}: {step.action}", expanded=True):
                st.markdown(f"**Thought:** {step.thought}")
                st.markdown(f"**Action:** `{step.action}`(`{step.action_input}`)")
                st.markdown(f"**Observation:** `{obs_str}`")

        # Update Live Browser View on Right
        if step.screenshot_path and os.path.exists(step.screenshot_path):
            st.session_state["latest_screenshot"] = step.screenshot_path
            browser_display.image(
                step.screenshot_path,
                caption=f"Optical Telemetry Frame — Step {step.step_number} ({step.action})",
                use_column_width=True
            )

        # Update DB State on Right
        db_display.dataframe(list_invoices(), use_container_width=True)

    agent = DynamicAlignWorker(
        headless=True,
        max_steps=10,
        step_callback=on_step
    )

    try:
        with st.spinner("Agent is decomposing goal, orchestrating Playwright, and committing..."):
            result = agent.run(user_prompt)

        with left_pane:
            if result.success:
                st.session_state["status_msg"] = f"✅ **Goal Attained & Verified ({result.total_steps} steps, {result.execution_time:.2f}s)!**\n\n{result.summary}"
                status_placeholder.success(st.session_state["status_msg"])
            else:
                status_placeholder.error(f"❌ **Task Halted:** {result.summary}")

        # Final refresh
        if result.final_screenshot and os.path.exists(result.final_screenshot):
            st.session_state["latest_screenshot"] = result.final_screenshot
            browser_display.image(result.final_screenshot, caption="Final Visual Proof", use_column_width=True)
        db_display.dataframe(list_invoices(), use_container_width=True)
    except Exception as run_err:
        import traceback
        st.error(f"Execution Error: {str(run_err)}")
        st.code(traceback.format_exc())
    finally:
        try:
            agent.browser.close()
        except Exception:
            pass
