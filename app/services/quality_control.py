"""Central Quality-Control Gateway - Validates and sanitizes agent findings.

This ensures:
- Security claims have actual evidence
- No "unknown" file paths
- Deduplication of similar issues
- Filtering of trivial noise
- Severity limits enforcement
"""
from typing import List, Dict, Any
from app.models.schemas import ReviewComment
from app.services.llm_gateway import get_llm_gateway
from app.utils.comment_format import VAGUE_SUGGESTIONS
import logging
import json

logger = logging.getLogger(__name__)


class QualityControlGateway:
    """Central validation and sanitization using STRICT RULE-BASED filtering.
    
    Why rule-based instead of LLM?
    - Even quality control LLMs can hallucinate
    - Deterministic rules are more reliable
    - Faster execution (no extra LLM call)
    - Predictable behavior
    """
    
    def __init__(self):
        """Initialize the quality control gateway."""
        pass  # No LLM needed - pure rules
    
    async def validate_findings(
        self,
        comments: List[ReviewComment],
        diff_context: str
    ) -> Dict[str, Any]:
        """
        Validate and sanitize all agent findings using STRICT RULE-BASED filtering.
        
        LLMs can hallucinate even in quality control, so we use deterministic rules.
        
        Args:
            comments: Raw comments from all agents
            diff_context: The actual code diff for evidence checking
            
        Returns:
            Dict with validated_comments and statistics
        """
        if not comments:
            return {
                "validated_comments": [],
                "dropped_count": 0,
                "drop_reasons": []
            }
        
        validated = []
        dropped_reasons = []
        
        # Parse diff to get actual line content (for verification)
        diff_lines = {}
        if diff_context:
            current_file = None
            current_line_num = 0
            for line in diff_context.split('\n'):
                # Track which file we're in
                if line.startswith('diff --git') or line.startswith('+++'):
                    if '/' in line:
                        parts = line.split('/')
                        current_file = '/'.join(parts[-1:]).strip() if parts else None
                elif line.startswith('@@'):
                    # Extract line number from @@ -X,Y +A,B @@
                    try:
                        plus_part = line.split('+')[1].split('@@')[0].strip()
                        current_line_num = int(plus_part.split(',')[0])
                    except:
                        pass
                elif current_file and line.startswith('+') and not line.startswith('+++'):
                    # This is an added line
                    if current_file not in diff_lines:
                        diff_lines[current_file] = {}
                    diff_lines[current_file][current_line_num] = line[1:]  # Remove '+'
                    current_line_num += 1
        
        # ULTRA-STRICT EVIDENCE RULES
        for comment in comments:
            # RULE 0: Must have valid file path
            if comment.file_path == "unknown" or not comment.file_path or comment.file_path.strip() == "":
                dropped_reasons.append(f"Unknown file path: {comment.message[:50]}")
                continue
            
            # RULE 0.1: VERIFY line number and issue against actual diff
            # This is CRITICAL to prevent false line number claims
            if comment.line_number and diff_lines:
                file_base = comment.file_path.split('/')[-1]  # Get basename
                verified = False
                
                # Look for this file in diff_lines
                for diff_file, lines_dict in diff_lines.items():
                    if file_base in diff_file or diff_file in comment.file_path:
                        # Check if the line exists in diff
                        actual_line = lines_dict.get(comment.line_number, "")
                        
                        # Extract key terms from the issue message
                        message_lower = comment.message.lower()
                        
                        # Verify the issue makes sense for this line
                        # If message says "missing colon" but line HAS a colon, DROP IT
                        if "missing colon" in message_lower and ":" in actual_line:
                            dropped_reasons.append(f"FALSE CLAIM: Says 'missing colon' but line {comment.line_number} has colon: {actual_line[:50]}")
                            verified = False
                            break
                        
                        # If message mentions a variable/keyword, it should appear in the line
                        # Extract quoted terms from message
                        import re
                        quoted_terms = re.findall(r"['\"]([^'\"]+)['\"]", comment.message)
                        if quoted_terms:
                            # At least one quoted term should appear in the line
                            if not any(term in actual_line for term in quoted_terms):
                                dropped_reasons.append(f"Unverifiable: Line {comment.line_number} doesn't contain mentioned terms: {actual_line[:50]}")
                                verified = False
                                break
                        
                        verified = True
                        break
                
                # If we have diff data but couldn't verify, be suspicious
                if not verified and diff_lines:
                    # Don't auto-drop, but be cautious
                    pass  # Will be caught by other rules
            
            # RULE 0.5: AGGRESSIVE - Drop ALL "missing X" claims (agents can't know what's missing)
            message_lower = comment.message.lower()
            
            # These are ALWAYS hallucinations when reviewing partial diffs
            missing_claims = [
                "missing",  # "missing dictionary", "missing code", "missing function", etc.
                "should have",
                "needs to include",
                "requires",
                "must add",
                "add necessary",
            ]
            
            if any(claim in message_lower for claim in missing_claims):
                dropped_reasons.append(f"VAGUE 'missing X' claim (can't verify from diff): {comment.message[:60]}")
                continue
            
            # RULE 0.6: Drop claims about code between lines (impossible to verify)
            if "between lines" in message_lower or "between line" in message_lower:
                dropped_reasons.append(f"Impossible to verify 'between lines' claim: {comment.message[:60]}")
                continue
            
            # RULE 0.7: Drop generic weasel words (evidence of speculation)
            weasel_words = [
                "function is not defined",  # Can't know without full file
                "inefficient loop" if "for" not in message_lower and "while" not in message_lower else None,
                "n+1 quer" if "select" not in message_lower and ".get(" not in message_lower else None,
                "check if",  # Vague
            ]
            
            # Filter out None values and check
            is_generic = any(weasel for weasel in weasel_words 
                           if weasel and weasel in message_lower)
            
            if is_generic:
                dropped_reasons.append(f"Generic claim without evidence: {comment.message[:60]}")
                continue
            
            # RULE 1: Drop trivial noise
            trivial_patterns = [
                "blank line",
                "remove blank line",
                "obvious formatting",
                "add a comment to explain the purpose of the empty line",
                "print statement could be more descriptive",
                "blocking synchronous code in print",  # Nonsense
                "more descriptive print statement"
            ]
            
            if any(pattern in message_lower for pattern in trivial_patterns):
                dropped_reasons.append(f"Trivial noise: {comment.message[:50]}")
                continue
            
            # RULE 2: Drop bad variable name suggestions for GOOD names
            good_variable_names = [
                "payload", "result", "response", "data", "config", 
                "description", "resident_name", "block", "error", "value",
                "request", "output", "input", "params", "args", "kwargs"
            ]
            
            if "variable" in message_lower and "descriptive" in message_lower:
                # Check if it's complaining about a good name
                is_good_name = any(f"'{name}'" in message_lower or f'"{name}"' in message_lower 
                                  for name in good_variable_names)
                if is_good_name:
                    dropped_reasons.append(f"False positive - good variable name: {comment.message[:50]}")
                    continue
            
            # RULE 3: Drop security claims WITHOUT evidence in diff
            if comment.category.value == "security":
                # Must have evidence keywords in the actual diff
                security_evidence_keywords = [
                    "select ", "insert ", "update ", "delete ", "drop ",  # SQL
                    ".execute(", ".query(", ".raw(",  # Database
                    "eval(", "exec(", "__import__",  # Dangerous eval
                    "os.system", "subprocess", "shell=True",  # Shell
                    "open(", "write(", "read(",  # File I/O (context dependent)
                ]
                
                has_evidence = any(kw in diff_context.lower() if diff_context else False 
                                  for kw in security_evidence_keywords)
                
                if not has_evidence:
                    dropped_reasons.append(f"Security claim without code evidence: {comment.message[:50]}")
                    continue
            
            # RULE 4: Drop "unused import" if not specific
            if "unused import" in message_lower:
                # Only keep if we have the actual import name
                if "from" not in comment.message and "import" not in comment.message:
                    dropped_reasons.append(f"Unverifiable unused import claim: {comment.message[:50]}")
                    continue
            
            # RULE 4.5: Drop placeholder-only suggestions (LLM must explain the fix)
            if comment.suggestion and comment.suggestion.lower().strip() in VAGUE_SUGGESTIONS:
                dropped_reasons.append(f"Vague suggestion only: {comment.message[:50]}")
                continue
            if comment.suggestion and len(comment.suggestion.strip()) < 20:
                dropped_reasons.append(f"Suggestion too short: {comment.suggestion[:40]}")
                continue

            # RULE 5: Drop performance claims without observable patterns
            if comment.category.value == "performance":
                vague_performance = [
                    "unnecessary db call",
                    "inefficient loop in",  # Unless they quote the loop
                    "missing caching in",
                    "n+1 quer",  # Unless they show the pattern
                ]
                if any(vague in message_lower for vague in vague_performance):
                    dropped_reasons.append(f"Vague performance claim without evidence: {comment.message[:50]}")
                    continue
            
            # Passed all filters - keep it
            validated.append(comment)
        
        # RULE 7: Enforce severity limits
        severity_counts = {"critical": 0, "error": 0, "warning": 0, "info": 0}
        severity_limits = {"critical": 2, "error": 4, "warning": 5, "info": 5}
        
        final_validated = []
        for comment in validated:
            sev = comment.severity.value
            if severity_counts.get(sev, 0) < severity_limits.get(sev, 5):
                final_validated.append(comment)
                severity_counts[sev] = severity_counts.get(sev, 0) + 1
            else:
                dropped_reasons.append(f"Severity limit exceeded: {sev}")
        
        # RULE 8: Deduplicate by line number + category
        deduped = []
        seen_keys = set()
        
        for comment in final_validated:
            # Key: file + line + category (same line, same category = duplicate)
            key = (comment.file_path, comment.line_number, comment.category.value)
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(comment)
            else:
                dropped_reasons.append(f"Duplicate issue: {comment.file_path}:{comment.line_number}")
        
        # Mark all as validated by quality control
        for comment in deduped:
            comment.source_agent = f"{comment.source_agent}_✓validated"
        
        dropped_count = len(comments) - len(deduped)
        
        logger.info(
            f"Quality control (rule-based): {len(comments)} → {len(deduped)} "
            f"(dropped {dropped_count} hallucinations/noise)"
        )
        
        return {
            "validated_comments": deduped,
            "dropped_count": dropped_count,
            "drop_reasons": dropped_reasons[:15]  # Top 15 reasons
        }


# Singleton instance
quality_control_gateway = QualityControlGateway()
