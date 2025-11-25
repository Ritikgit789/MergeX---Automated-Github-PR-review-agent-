"""LangGraph workflow orchestration for PR review."""
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.models import AgentState
from app.agents import (
    fetch_github_pr,
    parse_code_changes,
    review_logic,
    review_security,
    review_performance,
    review_readability,
)
import logging

logger = logging.getLogger(__name__)


def should_fetch_github(state: AgentState) -> str:
    """Determine if we should fetch from GitHub or use manual diff."""
    if state.pr_url:
        return "fetch_github"
    return "parse_code"


def aggregate_results(state: AgentState) -> AgentState:
    """Aggregate all review comments from different agents."""
    all_comments = []
    
    # Combine all comments
    all_comments.extend(state.logic_comments)
    all_comments.extend(state.security_comments)
    all_comments.extend(state.performance_comments)
    all_comments.extend(state.readability_comments)
    
    # Deduplicate based on file_path, line_number, and message
    seen = set()
    unique_comments = []
    
    for comment in all_comments:
        key = (comment.file_path, comment.line_number, comment.message)
        if key not in seen:
            seen.add(key)
            unique_comments.append(comment)
    
    # Sort by severity (critical > error > warning > info) and then by file path
    severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
    unique_comments.sort(
        key=lambda c: (severity_order.get(c.severity.value, 4), c.file_path, c.line_number or 0)
    )
    
    state.all_comments = unique_comments
    logger.info(f"Aggregated {len(unique_comments)} unique comments from {len(all_comments)} total")
    
    return state


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
