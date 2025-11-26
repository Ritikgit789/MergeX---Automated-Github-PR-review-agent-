# app/agents/code_parser.py
import re
import logging
from typing import List, Dict, Any
from app.models.schemas import AgentState

logger = logging.getLogger(__name__)


class CodeParserAgent:
    """
    Parse unified Git diff to structured format:
    - file_path
    - hunks[]
      - {old_start, new_start, changes[]}
    """
    
    HUNK_HEADER_REGEX = re.compile(r'@@ -(\d+),?\d* \+(\d+),?\d* @@')

    def parse_diff(self, state: AgentState) -> AgentState:
        diff_content = state.manual_diff or state.diff_content

        if not diff_content:
            return state.with_error("No diff content available to parse")

        try:
            state.parsed_changes = self._extract_changes(diff_content)
            logger.info(f"Parsed changes for {len(state.parsed_changes)} files")
            return state
        
        except Exception as exc:
            logger.error(f"Diff parsing error: {exc}")
            return state.with_error(f"Error parsing diff: {exc}")

    def _extract_changes(self, diff: str) -> List[Dict[str, Any]]:
        """
        Core parsing logic — pure function (easy to test)
        """
        parsed = []
        lines = diff.split('\n')

        current_file = None
        current_hunk = None
        old_line_no = new_line_no = None

        for line in lines:
            # File header (start)
            if line.startswith('--- a/'):
                current_file = {
                    "file_path": line[6:],
                    "hunks": []
                }
                continue

            # File header (end side)
            if line.startswith('+++ b/'):
                if current_file:
                    current_file["new_path"] = line[6:]
                continue

            # Hunk header
            if line.startswith('@@'):
                match = self.HUNK_HEADER_REGEX.match(line)
                if match and current_file:
                    old_line_no = int(match.group(1))
                    new_line_no = int(match.group(2))
                    current_hunk = {
                        "old_start": old_line_no,
                        "new_start": new_line_no,
                        "changes": []
                    }
                    current_file["hunks"].append(current_hunk)
                continue

            if current_hunk is None:
                continue

            # Process change lines
            if line.startswith('+') and not line.startswith('+++'):
                current_hunk["changes"].append({
                    "type": "addition",
                    "line_number": new_line_no,
                    "content": line[1:]
                })
                new_line_no += 1
            elif line.startswith('-') and not line.startswith('---'):
                current_hunk["changes"].append({
                    "type": "deletion",
                    "line_number": old_line_no,
                    "content": line[1:]
                })
                old_line_no += 1
            else:
                # Context or whitespace
                if line.startswith(' '):
                    current_hunk["changes"].append({
                        "type": "context",
                        "line_number": old_line_no,
                        "content": line[1:]
                    })
                    old_line_no += 1
                    new_line_no += 1

        if current_file and current_file["hunks"]:
            parsed.append(current_file)

        return parsed


code_parser = CodeParserAgent()


def parse_code_changes(state: AgentState) -> AgentState:
    """LangGraph-compatible wrapper"""
    return code_parser.parse_diff(state)
