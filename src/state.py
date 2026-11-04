from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FactClaim(BaseModel):
    claim: str = Field(description="The factual claim extracted from the article")
    verified: bool = Field(description="Whether the claim is supported by research evidence")
    confidence: str = Field(description="High, Medium, or Low confidence level")
    source_reference: Optional[str] = Field(default=None, description="Source URL or snippet supporting or disputing the claim")
    notes: Optional[str] = Field(default=None, description="Explanation or correction if unsupported")

class FactCheckReport(BaseModel):
    passed: bool = Field(description="True if article is factually sound and ready for publication")
    accuracy_score: float = Field(description="Percentage score from 0.0 to 100.0 based on verified claims")
    claims: List[FactClaim] = Field(default_factory=list, description="Detailed list of checked claims")
    feedback: str = Field(default="", description="Specific guidance for the writer if revisions are needed")

class AgentState(TypedDict):
    # Inputs
    topic: str
    tone: str
    target_audience: str
    max_revisions: int
    
    # State tracking
    current_agent: str
    revision_count: int
    
    # Research stage
    search_queries: List[str]
    research_sources: List[Dict[str, str]]  # [{'title': ..., 'snippet': ..., 'url': ...}]
    research_summary: str
    
    # Writing & Editing
    draft_article: str
    edited_article: str
    
    # Fact Checking
    fact_check_report: Dict[str, Any]
    
    # Final Output
    final_article: str
    
    # Execution trace / logs
    agent_logs: List[str]
    error: Optional[str]

