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


def should_continue_after_fetch(state: AgentState) -> str:
    """Check if we should continue after GitHub fetch or stop due to error."""
    # Handle both dict and object access
    if isinstance(state, dict):
        error = state.get("error")
        diff_content = state.get("diff_content")
    else:
        error = getattr(state, "error", None)
        diff_content = getattr(state, "diff_content", None)
    
    # If there's an error or no diff content, stop the workflow
    if error or not diff_content:
        return "end"
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
    
    # Basic deduplication before quality control
    seen = set()
    unique_comments = []
    
    for comment in all_comments:
        msg_key = comment.message.strip().lower()
        key = (comment.file_path, msg_key)
        
        if key not in seen:
            seen.add(key)
            unique_comments.append(comment)
    
    logger.info(f"Aggregated {len(unique_comments)} unique comments from {len(all_comments)} total (before quality control)")
    
    return {"raw_comments": unique_comments}


async def quality_control_validation(state: Any) -> dict:
    """Validate and sanitize all findings through quality control gateway."""
    from app.services.quality_control import quality_control_gateway
    
    # Get raw comments and diff context
    if isinstance(state, dict):
        raw_comments = state.get("raw_comments", [])
        diff_content = state.get("diff_content", "")
    else:
        raw_comments = getattr(state, "raw_comments", [])
        diff_content = getattr(state, "diff_content", "")
    
    if not raw_comments:
        logger.info("No comments to validate")
        return {"all_comments": []}
    
    try:
        # Run quality control validation
        validation_result = await quality_control_gateway.validate_findings(
            comments=raw_comments,
            diff_context=diff_content or ""
        )
        
        validated_comments = validation_result["validated_comments"]
        dropped_count = validation_result["dropped_count"]
        
        # Sort by severity
        severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        validated_comments.sort(
            key=lambda c: (severity_order.get(c.severity.value, 4), c.file_path, c.line_number or 0)
        )
        
        logger.info(
            f"Quality control complete: {len(raw_comments)} → {len(validated_comments)} "
            f"(dropped {dropped_count} hallucinations/noise)"
        )
        
        return {"all_comments": validated_comments}
        
    except Exception as e:
        logger.error(f"Quality control failed, using raw comments: {str(e)}")
        # Fallback: use raw comments with basic filtering
        return {"all_comments": [c for c in raw_comments if c.file_path != "unknown"]}


def create_review_workflow() -> StateGraph:
    """
    Create the LangGraph workflow for PR review.
    
    Workflow:
    1. Conditional: Fetch from GitHub OR use manual diff
    2. Parse code changes
    3. Run all reviewers in parallel
    4. Aggregate results
    5. Quality control validation (NEW - prevents hallucinations)
    6. Return validated findings
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
    workflow.add_node("quality_control", quality_control_validation)  # NEW
    
    # Set entry point with conditional routing
    workflow.set_conditional_entry_point(
        should_fetch_github,
        {
            "fetch_github": "fetch_github",
            "parse_code": "parse_code"
        }
    )
    
    # GitHub fetch -> conditional check -> parse code or end
    workflow.add_conditional_edges(
        "fetch_github",
        should_continue_after_fetch,
        {
            "parse_code": "parse_code",
            "end": END
        }
    )
    
    # Parse code -> sequential reviewers (reduces quota usage by 75%)
    workflow.add_edge("parse_code", "review_logic")
    workflow.add_edge("review_logic", "review_security")
    workflow.add_edge("review_security", "review_performance")
    workflow.add_edge("review_performance", "review_readability")
    
    # Last reviewer -> aggregate
    workflow.add_edge("review_readability", "aggregate")
    
    # Aggregate -> quality control validation (CRITICAL STEP)
    workflow.add_edge("aggregate", "quality_control")
    
    # Quality control -> end
    workflow.add_edge("quality_control", END)
    
    return workflow.compile()
    
    return workflow.compile()


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
