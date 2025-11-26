"""Unit tests for individual agents."""
import pytest
from app.models.schemas import AgentState, ReviewCategory, ReviewSeverity
from app.agents.code_parser import code_parser


class TestCodeParser:
    """Tests for code parser agent."""
    
    def test_parse_simple_diff(self):
        """Test parsing a simple diff."""
        diff = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("Hello")
+    print("Hello, World!")
+    return True
"""
        state = AgentState(manual_diff=diff)
        result = code_parser.parse_diff(state)
        
        assert result.parsed_changes is not None
        assert len(result.parsed_changes) > 0
        assert result.error is None
    
    def test_parse_empty_diff(self):
        """Test parsing empty diff."""
        state = AgentState(manual_diff="")
        result = code_parser.parse_diff(state)
        
        assert result.error is not None


class TestAgentState:
    """Tests for agent state model."""
    
    def test_agent_state_creation(self):
        """Test creating agent state."""
        state = AgentState(
            pr_url="https://github.com/abhishekgit03/civicPulse/pull/5",
            language="python"
        )
        
        assert state.pr_url == "https://github.com/abhishekgit03/civicPulse/pull/5"
        assert state.language == "python"
        assert state.logic_comments == []
        assert state.error is None
    
    def test_agent_state_with_manual_diff(self):
        """Test agent state with manual diff."""
        state = AgentState(
            manual_diff="test diff",
            language="javascript",
            context="Testing context"
        )
        
        assert state.manual_diff == "test diff"
        assert state.language == "javascript"
        assert state.context == "Testing context"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
