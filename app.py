import os
import streamlit as st
from dotenv import load_dotenv

# Load environment
load_dotenv()

from src.config import settings
from src.graph import content_graph
from src.state import AgentState

st.set_page_config(
    page_title="Rahul's Multi-Agent Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Main Hero Header */
    .hero-container {
        padding: 1.8rem 2rem;
        background: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.12) 0%, rgba(236, 72, 153, 0.05) 90.5%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60A5FA 0%, #A78BFA 50%, #F472B6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
        letter-spacing: -0.02em;
    }
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        line-height: 1.6;
        margin-bottom: 1.2rem;
    }

    /* Agent Architecture Cards Grid */
    .agent-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.85rem;
        margin-bottom: 1.5rem;
    }
    .agent-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 1rem 1.1rem;
        transition: all 0.25s ease;
    }
    .agent-card:hover {
        border-color: rgba(129, 140, 248, 0.4);
        transform: translateY(-2px);
        background: rgba(30, 41, 59, 0.65);
    }
    .agent-icon {
        font-size: 1.4rem;
        margin-bottom: 0.4rem;
    }
    .agent-name {
        font-weight: 700;
        font-size: 0.95rem;
        color: #F8FAFC;
        margin-bottom: 0.25rem;
    }
    .agent-desc {
        font-size: 0.78rem;
        color: #94A3B8;
        line-height: 1.4;
    }

    /* Metric Badges */
    .metric-box {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.1rem;
        text-align: center;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #38BDF8;
    }
    .metric-lbl {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-top: 0.2rem;
    }

    /* Claim Cards */
    .claim-card-pass {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.75rem;
    }
    .claim-card-fail {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.25);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.75rem;
    }

    /* Status Pill */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    /* Footer */
    .app-footer {
        margin-top: 3.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        text-align: center;
        color: #64748B;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Configuration (Deployment Mode: Clean, zero API keys exposed)
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/bot.png", width=64)
    st.title("Studio Controls")
    st.caption("Rahul's Autonomous Multi-Agent System")

    # Production Server Status
    active_prov = settings.get_active_provider()
    has_key = bool(settings.GROQ_API_KEY if active_prov == "groq" else settings.GEMINI_API_KEY)
    
    if has_key:
        st.markdown("""
        <div class="status-pill">
            <span style="font-size: 10px;">●</span> Production Engine Online
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("🔴 Missing server credentials. Add keys to .env or deployment secrets.")

    st.write("")
    
    with st.expander("⚙️ System Architecture", expanded=False):
        st.markdown(f"""
        - **Primary Engine:** `{settings.GROQ_MODEL}`
        - **Inference Speed:** ~400 tokens/sec
        - **Web Research:** Tavily / DuckDuckGo
        - **Orchestration:** LangGraph StateGraph
        - **Self-Correction:** Automated loopback
        """)

    st.subheader("Model & Execution")
    provider = st.selectbox(
        "LLM Provider",
        options=["Groq", "Gemini"],
        index=0 if active_prov == "groq" else 1,
        help="Fast Groq LPU inference or Google Gemini"
    )
    settings.LLM_PROVIDER = provider.lower()

    if provider == "Groq":
        groq_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
        default_idx = groq_models.index(settings.GROQ_MODEL) if settings.GROQ_MODEL in groq_models else 0
        groq_model = st.selectbox("Groq Model", options=groq_models, index=default_idx)
        settings.GROQ_MODEL = groq_model
        os.environ["GROQ_MODEL"] = groq_model
    else:
        gemini_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-flash-latest"]
        default_idx = gemini_models.index(settings.GEMINI_MODEL) if settings.GEMINI_MODEL in gemini_models else 0
        gemini_model = st.selectbox("Gemini Model", options=gemini_models, index=default_idx)
        settings.GEMINI_MODEL = gemini_model
        os.environ["GEMINI_MODEL"] = gemini_model

    st.divider()
    st.subheader("Editorial Parameters")
    tone = st.selectbox(
        "Writing Tone",
        options=[
            "Engaging & Professional",
            "Deeply Technical & Analytical",
            "Executive Briefing & Strategic",
            "Conversational & Accessible"
        ],
        index=0
    )
    target_audience = st.text_input("Target Audience", value="Tech & Industry Professionals")
    max_revisions = st.slider(
        "Max Fact-Check Revisions",
        min_value=0,
        max_value=3,
        value=1,
        help="Automated loopback limit: how many times the Fact-Checker can reject a draft and return it to the Writer for corrections."
    )

# Hero Header
st.markdown("""
<div class="hero-container">
    <div class="hero-title">Rahul's Multi-Agent Content Studio</div>
    <div class="hero-subtitle">
        An enterprise-grade autonomous content intelligence system. Four specialized AI agents coordinate via 
        <strong>LangGraph</strong> with dynamic, self-correcting fact-checking loops.
    </div>
    <div class="agent-grid">
        <div class="agent-card">
            <div class="agent-icon">🔍</div>
            <div class="agent-name">1. Researcher</div>
            <div class="agent-desc">Queries live web sources, extracts empirical stats & citations.</div>
        </div>
        <div class="agent-card">
            <div class="agent-icon">✍️</div>
            <div class="agent-name">2. Writer</div>
            <div class="agent-desc">Synthesizes evidence into structured, comprehensive drafts.</div>
        </div>
        <div class="agent-card">
            <div class="agent-icon">✂️</div>
            <div class="agent-name">3. Editor</div>
            <div class="agent-desc">Elevates syntax, narrative flow, readability & typography.</div>
        </div>
        <div class="agent-card">
            <div class="agent-icon">🛡️</div>
            <div class="agent-name">4. Fact Checker</div>
            <div class="agent-desc">Audits claims against evidence; triggers revision if flawed.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Sample Topic Chips
st.markdown("<p style='font-size:0.88rem; color:#94A3B8; margin-bottom:0.4rem; font-weight:600;'>💡 SUGGESTED TOPICS:</p>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
default_topic = "Impact of AI on Healthcare Diagnostics and Patient Care"

if "selected_topic" not in st.session_state:
    st.session_state["selected_topic"] = default_topic

if c1.button("🏥 AI in Healthcare", use_container_width=True):
    st.session_state["selected_topic"] = "Impact of AI on Healthcare Diagnostics and Patient Care"
if c2.button("⚛️ Quantum Computing", use_container_width=True):
    st.session_state["selected_topic"] = "Breakthroughs in Quantum Computing and Cryptography in 2026"
if c3.button("🤖 Autonomous Agents", use_container_width=True):
    st.session_state["selected_topic"] = "Rise of Autonomous Multi-Agent Systems in Software Engineering"
if c4.button("⚡ Renewable Energy", use_container_width=True):
    st.session_state["selected_topic"] = "Next-Generation Solid-State Batteries and Clean Energy Storage"

# Search Input Bar
topic_input = st.text_input(
    "Enter Article Topic or Research Query",
    value=st.session_state["selected_topic"],
    placeholder="e.g. Breakthroughs in Quantum Computing in 2026..."
)

col_run, col_space = st.columns([1, 3])
with col_run:
    generate_btn = st.button("Generate Article 🚀", type="primary", use_container_width=True)

# Execution Pipeline & Results Display
if generate_btn:
    chosen_provider = provider.lower()
    active_key = settings.GROQ_API_KEY if chosen_provider == "groq" else settings.GEMINI_API_KEY
    if not active_key:
        st.error(f"⚠️ {provider} credentials missing on server. Please configure keys in your server environment / secrets.")
        st.stop()
        
    settings.LLM_PROVIDER = chosen_provider
    active_model = settings.GROQ_MODEL if chosen_provider == "groq" else settings.GEMINI_MODEL
    
    st.info(f"⚡ Orchestrating 4-Agent Pipeline using **{provider.upper()}** (`{active_model}`) with live Tavily Web Intelligence...")

    # Real-time Status Card
    progress_bar = st.progress(5)
    status_card = st.empty()
    trace_expander = st.expander("📋 Live Multi-Agent Execution Log", expanded=True)
    trace_container = trace_expander.empty()

    initial_state: AgentState = {
        "topic": topic_input,
        "tone": tone,
        "target_audience": target_audience,
        "max_revisions": max_revisions,
        "current_agent": "start",
        "revision_count": 0,
        "search_queries": [],
        "research_sources": [],
        "research_summary": "",
        "draft_article": "",
        "edited_article": "",
        "fact_check_report": {},
        "final_article": "",
        "agent_logs": [f"🚀 Multi-agent mission initialized for: '{topic_input}'"],
        "error": None
    }

    final_state = initial_state
    step_weights = {
        "researcher": 25,
        "writer": 50,
        "editor": 70,
        "fact_checker": 85,
        "revision_prep": 60,
        "finalize": 100
    }

    with st.spinner("Collaborative Agents Working..."):
        try:
            for step in content_graph.stream(initial_state):
                for node_name, node_output in step.items():
                    final_state.update(node_output)
                    pct = step_weights.get(node_name, 50)
                    progress_bar.progress(pct)
                    status_card.markdown(f"**Active Node:** `{node_name.upper()}`")
                    
                    logs = final_state.get("agent_logs", [])
                    log_text = "\n".join([f"- {l}" for l in logs])
                    trace_container.markdown(log_text)
                    
            progress_bar.progress(100)
            status_card.success("✨ Article Successfully Produced & Fact-Checked!")
            
        except Exception as e:
            st.error(f"❌ Execution failed: {str(e)}")
            st.stop()

    # Results Section
    st.divider()
    
    report = final_state.get("fact_check_report", {})
    score = report.get("accuracy_score", 100.0)
    passed = report.get("passed", True)
    revisions = final_state.get("revision_count", 0)
    sources_count = len(final_state.get("research_sources", []))
    word_count = len(final_state.get("final_article", "").split())

    # Metric Cards Grid
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-val">{score}%</div>
            <div class="metric-lbl">Accuracy Score</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        badge_text = "VERIFIED" if passed else "REVISION LIMIT"
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-val" style="color: {'#34D399' if passed else '#F87171'};">{badge_text}</div>
            <div class="metric-lbl">Audit Verdict</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-val">{revisions} / {max_revisions}</div>
            <div class="metric-lbl">Revision Cycles</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-val">{sources_count}</div>
            <div class="metric-lbl">Sources Cited</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    
    # Structured Inspection Tabs
    tab_article, tab_audit, tab_research, tab_compare, tab_trace = st.tabs([
        "📰 Published Article",
        "🛡️ Fact-Check Audit",
        "🔍 Research Dossier",
        "✍️ Writer vs. Editor",
        "📜 Execution Trace"
    ])

    with tab_article:
        final_text = final_state.get("final_article", "")
        st.markdown(final_text)
        st.divider()
        st.download_button(
            label="📥 Download Article (.md)",
            data=final_text,
            file_name=f"{topic_input[:30].replace(' ', '_').lower()}_verified.md",
            mime="text/markdown"
        )

    with tab_audit:
        st.subheader("🛡️ Investigative Fact-Check Report")
        if passed:
            st.success("✅ **Publication Clearance:** Article meets rigorous accuracy standards without hallucinations.")
        else:
            st.warning("⚠️ **Review Flagged:** Some assertions required qualification or exceeded revision limits.")
            
        claims = report.get("claims", [])
        if claims:
            for idx, c in enumerate(claims, 1):
                is_v = c.get("verified", False)
                card_class = "claim-card-pass" if is_v else "claim-card-fail"
                status_icon = "✅ VERIFIED" if is_v else "⚠️ UNVERIFIED / FLAGGED"
                confidence = c.get("confidence", "Medium")
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div style="font-size:0.8rem; font-weight:700; color:{'#34D399' if is_v else '#F87171'};">
                        {status_icon} &nbsp;•&nbsp; Confidence: {confidence}
                    </div>
                    <div style="font-size:0.95rem; font-weight:600; margin:0.3rem 0; color:#F8FAFC;">
                        "{c.get('claim')}"
                    </div>
                    <div style="font-size:0.82rem; color:#94A3B8;">
                        <strong>Source Reference:</strong> {c.get('source_reference', 'General Research Evidence')}
                    </div>
                    {f'<div style="font-size:0.82rem; color:#CBD5E1; margin-top:0.2rem;"><em>Notes: {c.get("notes")}</em></div>' if c.get("notes") else ''}
                </div>
                """, unsafe_allow_html=True)
                
        if report.get("feedback"):
            st.info(f"**Auditor Guidance:**\n{report.get('feedback')}")

    with tab_research:
        st.subheader("🔍 Synthesized Research Dossier")
        st.markdown(final_state.get("research_summary", "No research notes."))
        st.subheader("Retrieved Citations")
        for s in final_state.get("research_sources", []):
            st.markdown(f"- 🔗 [{s.get('title')}]({s.get('url')}) — *{s.get('snippet')}*")

    with tab_compare:
        col_draft, col_edit = st.columns(2)
        with col_draft:
            st.subheader("✍️ 1. Initial Writer Draft")
            st.markdown(final_state.get("draft_article", "Draft empty."))
        with col_edit:
            st.subheader("✂️ 2. Polished Editor Version")
            st.markdown(final_state.get("edited_article", "Editor output empty."))

    with tab_trace:
        st.subheader("📜 Detailed Chronological Execution Trace")
        for log in final_state.get("agent_logs", []):
            st.markdown(f"`{log}`")

# Footer
st.markdown("""
<div class="app-footer">
    <strong>Rahul's Multi-Agent Studio</strong> • Built with LangGraph, Groq, Tavily & Streamlit<br>
    <em>Engineered for robust autonomous content generation and fact verification</em>
</div>
""", unsafe_allow_html=True)
