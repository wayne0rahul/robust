from langchain_core.messages import SystemMessage, HumanMessage
from src.state import AgentState
from src.llm import get_llm

WRITER_SYSTEM_PROMPT = """You are a Master Content Writer and Journalist.
Your task is to write a compelling, comprehensive, and well-structured article based strictly on the provided research evidence.

Guidelines:
1. Craft an engaging Title and Subtitle.
2. Structure the article with clear H2 and H3 markdown headings.
3. Every factual statement, metric, or case study must be grounded in the provided research dossier.
4. Seamlessly incorporate markdown hyperlink citations pointing to the source URLs.
5. If revision feedback from the Fact Checker is provided, you MUST explicitly address and fix the flagged issues.
6. Conclude with key takeaways and a full References section."""

def writer_node(state: AgentState) -> dict:
    """
    Writer Agent Node:
    Takes research dossier (and any previous revision feedback) to draft or revise an article.
    """
    topic = state.get("topic", "")
    tone = state.get("tone", "engaging yet professional")
    target_audience = state.get("target_audience", "general informed audience")
    research_summary = state.get("research_summary", "")
    sources = state.get("research_sources", [])
    revision_count = state.get("revision_count", 0)
    fact_check_report = state.get("fact_check_report", {})
    feedback = fact_check_report.get("feedback", "")
    
    llm = get_llm(temperature=0.7)
    logs = list(state.get("agent_logs", []))
    
    if revision_count > 0 and feedback:
        logs.append(f"✍️ [Writer] Revising article draft (Revision #{revision_count}) to address fact-check critiques.")
        user_prompt = f"""Topic: {topic}
Tone: {tone}
Target Audience: {target_audience}

CRITICAL REVISION INSTRUCTIONS FROM FACT CHECKER:
{feedback}

Original Research Dossier:
{research_summary}

Please rewrite and revise the article thoroughly to eliminate or accurately qualify the unverified claims while preserving narrative flow and citations."""
    else:
        logs.append(f"✍️ [Writer] Crafting initial comprehensive article draft on: '{topic}'")
        user_prompt = f"""Topic: {topic}
Tone: {tone}
Target Audience: {target_audience}

Research Dossier:
{research_summary}

Please write an article of approximately 600-900 words adhering to the guidelines. Include full markdown formatting and inline source citations."""

    response = llm.invoke([
        SystemMessage(content=WRITER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ])
    draft_article = response.content.strip()
    
    logs.append(f"✅ [Writer] Draft completed ({len(draft_article.split())} words).")
    
    return {
        "current_agent": "writer",
        "draft_article": draft_article,
        "agent_logs": logs
    }

