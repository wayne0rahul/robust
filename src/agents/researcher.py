import json
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import AgentState
from src.llm import get_llm
from src.tools.search import search_web

RESEARCHER_SYSTEM_PROMPT = """You are an elite Research Specialist Agent.
Your job is to thoroughly analyze the user's topic, uncover key facts, empirical statistics, current trends, and real-world case studies.

Given a topic, you will:
1. Formulate 2 to 3 targeted search queries to gather comprehensive, balanced perspectives.
2. Review the gathered search evidence and synthesize a clear, bulleted Research Dossier.
3. Every claim or statistic in your dossier must reference the corresponding source URL.

Be rigorous, objective, and information-dense."""

def researcher_node(state: AgentState) -> dict:
    """
    Researcher Agent Node:
    1. Formulates search queries.
    2. Searches the web (Tavily/DuckDuckGo).
    3. Synthesizes findings with source citations.
    """
    topic = state.get("topic", "")
    llm = get_llm(temperature=0.3)
    
    logs = list(state.get("agent_logs", []))
    logs.append(f"🔍 [Researcher] Formulating search strategy for topic: '{topic}'")
    
    # 1. Generate search queries
    query_prompt = f"""Given the topic: "{topic}", generate exactly 2 or 3 distinct, high-impact search queries.
Return ONLY a valid JSON list of strings, for example:
["key statistics {topic}", "latest breakthroughs in {topic}", "challenges and ethical concerns of {topic}"]"""

    try:
        response = llm.invoke([
            SystemMessage(content="You generate search queries. Output ONLY valid JSON array of strings."),
            HumanMessage(content=query_prompt)
        ])
        content = response.content.strip()
        # Extract json if wrapped in backticks
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:].strip()
        queries = json.loads(content)
        if not isinstance(queries, list):
            queries = [topic]
    except Exception:
        queries = [topic, f"{topic} latest research", f"{topic} key facts"]
        
    logs.append(f"🔍 [Researcher] Executing queries: {', '.join(queries)}")
    
    # 2. Gather search results
    all_sources = []
    seen_urls = set()
    for q in queries[:2]:
        results = search_web(q, max_results=2)
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_sources.append(r)
                
    # Limit to top 4 sources to preserve token budget
    all_sources = all_sources[:4]
    logs.append(f"🔍 [Researcher] Retrieved {len(all_sources)} unique reference sources.")
    
    # 3. Synthesize research dossier
    sources_text = "\n\n".join([
        f"Title: {s['title']}\nURL: {s['url']}\nSnippet: {s['snippet']}"
        for s in all_sources
    ])
    
    synthesis_prompt = f"""Topic: {topic}

Retrieved Search Results:
{sources_text}

Instructions:
Create a structured Research Dossier including:
1. Executive Overview & Core Problem/Theme
2. Key Factual Findings, Data Points & Statistics (cite the specific URL for each point)
3. Major Perspectives, Trends & Real-world Applications
4. Potential Challenges, Risks, or Ethical Implications
5. Consolidated Reference Sources list

Format in clean, structured Markdown."""

    summary_response = llm.invoke([
        SystemMessage(content=RESEARCHER_SYSTEM_PROMPT),
        HumanMessage(content=synthesis_prompt)
    ])
    research_summary = summary_response.content.strip()
    
    logs.append("✅ [Researcher] Completed research dossier with citations.")
    
    return {
        "current_agent": "researcher",
        "search_queries": queries,
        "research_sources": all_sources,
        "research_summary": research_summary,
        "agent_logs": logs
    }

