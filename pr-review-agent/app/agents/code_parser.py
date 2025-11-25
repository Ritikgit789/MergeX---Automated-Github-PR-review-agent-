"""Code parser agent - parses diffs and extracts code changes."""
import re
from typing import List, Dict, Any
from app.models import AgentState
import logging

logger = logging.getLogger(__name__)


class CodeParserAgent:
    """Agent responsible for parsing diff content and extracting changes."""
    
    def parse_diff(self, state: AgentState) -> AgentState:
        """
        Parse unified diff format and extract changed lines.
        
        Args:
            state: Current agent state with diff_content or manual_diff
            
        Returns:
            Updated state with parsed_changes
        """
        # Use manual diff if provided, otherwise use fetched diff
        diff_content = state.manual_diff or state.diff_content
        
        if not diff_content:
            state.error = "No diff content available to parse"
            logger.error(state.error)
            return state
        
        try:
            parsed_changes = []
            current_file = None
            current_hunk = None
            
            lines = diff_content.split('\n')
            
            for i, line in enumerate(lines):
                # File header: --- a/path/to/file
                if line.startswith('--- a/'):
                    current_file = {
                        'file_path': line[6:],  # Remove '--- a/'
                        'hunks': []
                    }
                
                # New file header: +++ b/path/to/file
                elif line.startswith('+++ b/'):
                    if current_file:
                        current_file['new_path'] = line[6:]  # Remove '+++ b/'
                
                # Hunk header: @@ -start,count +start,count @@
                elif line.startswith('@@'):
                    if current_file:
                        match = re.match(r'@@ -(\d+),?\d* \+(\d+),?\d* @@(.*)', line)
                        if match:
                            current_hunk = {
                                'old_start': int(match.group(1)),
                                'new_start': int(match.group(2)),
                                'context': match.group(3).strip(),
                                'changes': []
                            }
                            current_file['hunks'].append(current_hunk)
                
                # Changed lines
                elif current_hunk is not None:
                    if line.startswith('+') and not line.startswith('+++'):
                        # Added line
                        current_hunk['changes'].append({
                            'type': 'addition',
                            'line_number': len([c for c in current_hunk['changes'] if c['type'] in ['addition', 'context']]) + current_hunk['new_start'],
                            'content': line[1:],  # Remove '+'
                            'raw_line': line
                        })
                    elif line.startswith('-') and not line.startswith('---'):
                        # Deleted line
                        current_hunk['changes'].append({
                            'type': 'deletion',
                            'line_number': len([c for c in current_hunk['changes'] if c['type'] in ['deletion', 'context']]) + current_hunk['old_start'],
                            'content': line[1:],  # Remove '-'
                            'raw_line': line
                        })
                    elif line.startswith(' '):
                        # Context line (unchanged)
                        current_hunk['changes'].append({
                            'type': 'context',
                            'content': line[1:],
                            'raw_line': line
                        })
                    elif line.strip() == '' and current_file:
                        # Empty line might indicate end of current file
                        if current_file and current_file.get('hunks'):
                            parsed_changes.append(current_file)
                            current_file = None
                            current_hunk = None
            
            # Add last file if exists
            if current_file and current_file.get('hunks'):
                parsed_changes.append(current_file)
            
            state.parsed_changes = parsed_changes
            logger.info(f"Successfully parsed {len(parsed_changes)} files with changes")
            
        except Exception as e:
            state.error = f"Error parsing diff: {str(e)}"
            logger.error(state.error)
        
        return state


# Create singleton instance
code_parser = CodeParserAgent()


def parse_code_changes(state: AgentState) -> AgentState:
    """LangGraph node function for parsing code changes."""
    return code_parser.parse_diff(state)
