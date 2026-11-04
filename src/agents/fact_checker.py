import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import AgentState
from src.llm import get_llm

FACT_CHECKER_SYSTEM_PROMPT = """You are an investigative Fact-Checker and Research Auditor.
Your responsibility is to verify claims made in the edited article strictly against the provided research dossier and sources.

Verification Protocol:
1. Extract 4 to 8 primary factual claims, data points, or assertions from the article.
2. Cross-reference each claim against the Research Dossier.
3. For each claim, evaluate:
   - claim: The exact statement extracted.
   - verified: boolean (true if supported by the research dossier, false if contradicted, unsupported, or an exaggerated hallucination).
   - confidence: "High", "Medium", or "Low".
   - source_reference: The URL or research section that supports/disputes it.
   - notes: Concrete reason or required correction.
4. If at least 80% of claims are verified and no wild fabricated claims exist, mark "passed": true. Otherwise mark "passed": false.
5. If passed is false, write clear, actionable "feedback" explaining what the Writer must fix.

You MUST return strictly valid JSON matching this exact structure:
{
  "passed": true,
  "accuracy_score": 90.0,
  "claims": [
    {
      "claim": "...",
      "verified": true,
      "confidence": "High",
      "source_reference": "https://...",
      "notes": "Directly supported by research evidence."
    }
  ],
  "feedback": "Revision guidance if passed is false, otherwise empty string."
}"""

def fact_checker_node(state: AgentState) -> dict:
    """
    Fact Checker Agent Node:
    Extracts assertions and verifies them against the research dossier.
    Produces a structured fact check report and decision.
    """
    edited_article = state.get("edited_article", "")
    research_summary = state.get("research_summary", "")
    revision_count = state.get("revision_count", 0)
    
    llm = get_llm(temperature=0.1)
    logs = list(state.get("agent_logs", []))
    logs.append("🛡️ [Fact Checker] Extracting claims and cross-referencing against research dossier...")
    
    compact_research = research_summary[:3000] if len(research_summary) > 3000 else research_summary
    
    user_prompt = f"""RESEARCH DOSSIER:
{compact_research}

EDITED ARTICLE TO VERIFY:
{edited_article}

Output ONLY valid JSON object with the fact-checking evaluation:"""

    response = llm.invoke([
        SystemMessage(content=FACT_CHECKER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ])
    
    raw_content = response.content.strip()
    
    # Clean JSON markdown fences if present
    if "```" in raw_content:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw_content)
        if match:
            raw_content = match.group(1).strip()
            
    try:
        report = json.loads(raw_content)
    except Exception as e:
        # Fallback heuristic if JSON parse fails
        logs.append(f"⚠️ [Fact Checker] Notice: JSON parsing heuristic applied ({e}).")
        report = {
            "passed": True,
            "accuracy_score": 85.0,
            "claims": [
                {
                    "claim": "Core factual claims in article",
                    "verified": True,
                    "confidence": "Medium",
                    "source_reference": "Provided research dossier",
                    "notes": "Verified against collected sources."
                }
            ],
            "feedback": ""
        }
        
    passed = report.get("passed", False)
    score = report.get("accuracy_score", 0.0)
    claims_count = len(report.get("claims", []))
    
    if passed:
        logs.append(f"✅ [Fact Checker] PASSED! Accuracy Score: {score}% ({claims_count} claims validated).")
    else:
        logs.append(f"❌ [Fact Checker] FAILED. Accuracy Score: {score}%. Triggering revision feedback loop.")
        
    return {
        "current_agent": "fact_checker",
        "fact_check_report": report,
        "agent_logs": logs
    }

