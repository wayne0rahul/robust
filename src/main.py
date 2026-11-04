import json
import logging
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.config import settings
from src.graph import content_graph
from src.state import AgentState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("multi_agent_api")

app = FastAPI(
    title="Multi-Agent Content Creation API",
    description="Orchestrates 4 specialized AI agents (Researcher, Writer, Editor, Fact Checker) via LangGraph.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ArticleRequest(BaseModel):
    topic: str = Field(..., description="Topic of the article to generate", example="Impact of AI on Healthcare")
    tone: Optional[str] = Field("engaging yet professional", description="Desired tone and voice")
    target_audience: Optional[str] = Field("informed professionals", description="Target readership")
    max_revisions: Optional[int] = Field(2, ge=0, le=5, description="Max fact-check revision cycles")

class ArticleResponse(BaseModel):
    topic: str
    final_article: str
    fact_check_report: Dict[str, Any]
    revision_count: int
    research_summary: str
    draft_article: str
    edited_article: str
    agent_logs: List[str]

@app.get("/api/health")
def health_check():
    """Health status and provider information."""
    return {
        "status": "healthy",
        "active_provider": settings.get_active_provider(),
        "groq_configured": bool(settings.GROQ_API_KEY),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "tavily_configured": bool(settings.TAVILY_API_KEY)
    }

@app.post("/api/generate", response_model=ArticleResponse)
async def generate_article(request: ArticleRequest):
    """
    Synchronously triggers the LangGraph multi-agent workflow.
    Executes Researcher -> Writer -> Editor -> Fact Checker (with revision loop) -> Publication.
    """
    initial_state: AgentState = {
        "topic": request.topic,
        "tone": request.tone or "engaging yet professional",
        "target_audience": request.target_audience or "general audience",
        "max_revisions": request.max_revisions or 2,
        "current_agent": "start",
        "revision_count": 0,
        "search_queries": [],
        "research_sources": [],
        "research_summary": "",
        "draft_article": "",
        "edited_article": "",
        "fact_check_report": {},
        "final_article": "",
        "agent_logs": [f"🚀 Workflow initialized for topic: '{request.topic}'"],
        "error": None
    }
    
    try:
        final_state = content_graph.invoke(initial_state)
        return ArticleResponse(
            topic=final_state.get("topic", request.topic),
            final_article=final_state.get("final_article", ""),
            fact_check_report=final_state.get("fact_check_report", {}),
            revision_count=final_state.get("revision_count", 0),
            research_summary=final_state.get("research_summary", ""),
            draft_article=final_state.get("draft_article", ""),
            edited_article=final_state.get("edited_article", ""),
            agent_logs=final_state.get("agent_logs", [])
        )
    except Exception as e:
        logger.error(f"Error in multi-agent workflow: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stream")
async def stream_article(request: ArticleRequest):
    """
    Streams multi-agent step completions in real-time via Server-Sent Events (SSE).
    """
    initial_state: AgentState = {
        "topic": request.topic,
        "tone": request.tone or "engaging yet professional",
        "target_audience": request.target_audience or "general audience",
        "max_revisions": request.max_revisions or 2,
        "current_agent": "start",
        "revision_count": 0,
        "search_queries": [],
        "research_sources": [],
        "research_summary": "",
        "draft_article": "",
        "edited_article": "",
        "fact_check_report": {},
        "final_article": "",
        "agent_logs": [f"🚀 Workflow initialized for topic: '{request.topic}'"],
        "error": None
    }

    async def event_generator():
        try:
            for step in content_graph.stream(initial_state):
                for node_name, node_output in step.items():
                    data = {
                        "node": node_name,
                        "current_agent": node_output.get("current_agent", node_name),
                        "logs": node_output.get("agent_logs", [])
                    }
                    if "final_article" in node_output:
                        data["final_article"] = node_output["final_article"]
                    yield f"data: {json.dumps(data)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)

