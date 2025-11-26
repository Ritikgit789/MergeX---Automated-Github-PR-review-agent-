"""LangGraph workflow orchestration for PR review."""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.models.schemas import AgentState
from app.agents.github_fetcher import fetch_github_pr
from app.agents.code_parser import parse_code_changes
from app.agents.logic_reviewer import review_logic
from app.agents.security_reviewer import review_security
from app.agents.performance_reviewer import review_performance
from app.agents.readability_reviewer import review_readability
import logging

logger = logging.getLogger(__name__)


def should_fetch_github(state: AgentState) -> str:
    """Determine if we should fetch from GitHub or use manual diff."""
    if state.pr_url:
        return "fetch_github"
    return "parse_code"


def aggregate_results(state: Any) -> dict:
    """Aggregate all review comments from different agents."""
    all_comments = []
    
    # Handle both dict and object access
    if isinstance(state, dict):
        all_comments.extend(state.get("logic_comments", []))
        all_comments.extend(state.get("security_comments", []))
        all_comments.extend(state.get("performance_comments", []))
        all_comments.extend(state.get("readability_comments", []))
    else:
        all_comments.extend(getattr(state, "logic_comments", []))
        all_comments.extend(getattr(state, "security_comments", []))
        all_comments.extend(getattr(state, "performance_comments", []))
        all_comments.extend(getattr(state, "readability_comments", []))
    
    # Deduplicate based on file_path and message (ignoring line number to avoid near-duplicates)
    seen = set()
    unique_comments = []
    
    for comment in all_comments:
        # Normalize message to avoid slight variations
        msg_key = comment.message.strip().lower()
        key = (comment.file_path, msg_key)
        
        if key not in seen:
            seen.add(key)
            unique_comments.append(comment)
    
    # Sort by severity (critical > error > warning > info) and then by file path
    severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
    unique_comments.sort(
        key=lambda c: (severity_order.get(c.severity.value, 4), c.file_path, c.line_number or 0)
    )
    
    logger.info(f"Aggregated {len(unique_comments)} unique comments from {len(all_comments)} total")
    
    return {"all_comments": unique_comments}


def create_review_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for PR review.
    
    Workflow:
    1. Conditional: Fetch from GitHub OR use manual diff
    2. Parse code changes
    3. Run all reviewers in parallel
    4. Aggregate results
    """
    # Create state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("fetch_github", fetch_github_pr)
    workflow.add_node("parse_code", parse_code_changes)
    workflow.add_node("review_logic", review_logic)
    workflow.add_node("review_security", review_security)
    workflow.add_node("review_performance", review_performance)
    workflow.add_node("review_readability", review_readability)
    workflow.add_node("aggregate", aggregate_results)
    
    # Set entry point with conditional routing
    workflow.set_conditional_entry_point(
        should_fetch_github,
        {
            "fetch_github": "fetch_github",
            "parse_code": "parse_code"
        }
    )
    
    # GitHub fetch -> parse code
    workflow.add_edge("fetch_github", "parse_code")
    
    # Parse code -> all reviewers (parallel execution)
    workflow.add_edge("parse_code", "review_logic")
    workflow.add_edge("parse_code", "review_security")
    workflow.add_edge("parse_code", "review_performance")
    workflow.add_edge("parse_code", "review_readability")
    
    # All reviewers -> aggregate
    workflow.add_edge("review_logic", "aggregate")
    workflow.add_edge("review_security", "aggregate")
    workflow.add_edge("review_performance", "aggregate")
    workflow.add_edge("review_readability", "aggregate")
    
    # Aggregate -> end
    workflow.add_edge("aggregate", END)
    
    return workflow.compile()


# Create compiled workflow
review_workflow = create_review_workflow()


# Create compiled workflow
review_workflow = create_review_workflow()

if __name__ == "__main__":
    from pathlib import Path

    # Get graph object
    graph = review_workflow.get_graph()

    # Mermaid PNG generate karo
    png_bytes = graph.draw_mermaid_png()

    # Save as image file near this script
    out_path = Path(__file__).parent / "review_workflow.png"
    out_path.write_bytes(png_bytes)

    print(f"✅ Saved LangGraph workflow diagram to: {out_path}")
