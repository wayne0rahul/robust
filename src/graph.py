from typing import Literal
from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.agents.researcher import researcher_node
from src.agents.writer import writer_node
from src.agents.editor import editor_node
from src.agents.fact_checker import fact_checker_node

def revision_prep_node(state: AgentState) -> dict:
    """Prepares the state for a revision cycle."""
    rev = state.get("revision_count", 0) + 1
    logs = list(state.get("agent_logs", []))
    logs.append(f"🔄 [Workflow] Initiating revision round #{rev} back to Writer Agent.")
    return {
        "revision_count": rev,
        "agent_logs": logs
    }

def finalize_node(state: AgentState) -> dict:
    """Finalizes the validated article for publication."""
    edited = state.get("edited_article", "")
    report = state.get("fact_check_report", {})
    score = report.get("accuracy_score", 100.0)
    passed = report.get("passed", True)
    rev_count = state.get("revision_count", 0)
    
    status_badge = "✅ Fact-Checked & Verified" if passed else "⚠️ Published with Review Notes"
    
    header = (
        f"> **Publication Status:** {status_badge} | "
        f"**Accuracy Score:** {score}% | "
        f"**Revisions:** {rev_count}\n\n"
    )
    final_article = header + edited
    
    logs = list(state.get("agent_logs", []))
    logs.append("🎉 [Workflow] Article successfully finalized and ready for export.")
    
    return {
        "final_article": final_article,
        "current_agent": "complete",
        "agent_logs": logs
    }

def check_fact_check_verdict(state: AgentState) -> Literal["finalize", "revision_prep"]:
    """
    Conditional edge evaluator:
    If article passes fact check OR max revisions are exhausted -> finalize.
    Otherwise, route back to revision_prep -> writer.
    """
    report = state.get("fact_check_report", {})
    passed = report.get("passed", False)
    rev_count = state.get("revision_count", 0)
    max_rev = state.get("max_revisions", 2)
    
    if passed:
        return "finalize"
    elif rev_count >= max_rev:
        return "finalize"
    else:
        return "revision_prep"

def create_content_graph():
    """Builds and compiles the multi-agent content creation StateGraph."""
    builder = StateGraph(AgentState)
    
    # Register Nodes
    builder.add_node("researcher", researcher_node)
    builder.add_node("writer", writer_node)
    builder.add_node("editor", editor_node)
    builder.add_node("fact_checker", fact_checker_node)
    builder.add_node("revision_prep", revision_prep_node)
    builder.add_node("finalize", finalize_node)
    
    # Register Linear Flow
    builder.add_edge(START, "researcher")
    builder.add_edge("researcher", "writer")
    builder.add_edge("writer", "editor")
    builder.add_edge("editor", "fact_checker")
    
    # Conditional Routing (Fact Checker feedback loop)
    builder.add_conditional_edges(
        "fact_checker",
        check_fact_check_verdict,
        {
            "finalize": "finalize",
            "revision_prep": "revision_prep"
        }
    )
    
    # Loop back to Writer after revision preparation
    builder.add_edge("revision_prep", "writer")
    
    # Finalize goes to END
    builder.add_edge("finalize", END)
    
    return builder.compile()

# Singleton graph instance
content_graph = create_content_graph()

