from langchain_core.messages import SystemMessage, HumanMessage
from src.state import AgentState
from src.llm import get_llm

EDITOR_SYSTEM_PROMPT = """You are a Senior Editor and Style Director at a premier publication.
Your job is to elevate the written draft into a publication-ready masterpiece.

Your Editorial Focus:
1. Grammar, Syntax & Flow: Enhance readability, eliminate passive fluff, and ensure seamless transitions between paragraphs.
2. Tone & Voice: Match the intended tone and speak directly to the target audience.
3. Typography & Formatting: Use bold accents for key takeaways, callout quotes for highlights, and clean markdown tables or lists where beneficial.
4. Citation Integrity: DO NOT strip out markdown hyperlinks, URLs, or citations. Ensure references remain intact.
5. Factual Preservation: DO NOT invent new factual claims or statistics during editing."""

def editor_node(state: AgentState) -> dict:
    """
    Editor Agent Node:
    Polishes and structures the draft article for clarity, impact, and reading pleasure.
    """
    topic = state.get("topic", "")
    tone = state.get("tone", "engaging yet professional")
    target_audience = state.get("target_audience", "general informed audience")
    draft_article = state.get("draft_article", "")
    
    llm = get_llm(temperature=0.4)
    logs = list(state.get("agent_logs", []))
    logs.append("✂️ [Editor] Polishing draft article: enhancing style, syntax, and structural flow.")
    
    user_prompt = f"""Target Tone: {tone}
Target Audience: {target_audience}

Draft Article to Edit:
{draft_article}

Please edit and polish this article. Output the complete revised publication-ready markdown article."""

    response = llm.invoke([
        SystemMessage(content=EDITOR_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ])
    edited_article = response.content.strip()
    
    logs.append("✅ [Editor] Editorial review and enhancements completed.")
    
    return {
        "current_agent": "editor",
        "edited_article": edited_article,
        "agent_logs": logs
    }

