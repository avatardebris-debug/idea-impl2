"""Tests for the IntentParser."""

import pytest
from agentflow_drophip.workflow.intent_parser import IntentParser, IntentType


class TestIntentParser:
    """Tests for IntentParser."""

    def test_parser_creation(self):
        """Test creating an IntentParser."""
        parser = IntentParser()
        assert parser is not None

    def test_parse_simple_command(self):
        """Test parsing a simple command."""
        parser = IntentParser()
        intent = parser.parse("create a new workflow")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_execute_command(self):
        """Test parsing an execute command."""
        parser = IntentParser()
        intent = parser.parse("execute workflow")
        assert intent.type == IntentType.EXECUTE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_status_command(self):
        """Test parsing a status command."""
        parser = IntentParser()
        intent = parser.parse("get workflow status")
        assert intent.type == IntentType.GET_STATUS
        assert intent.parameters is not None

    def test_parse_reset_command(self):
        """Test parsing a reset command."""
        parser = IntentParser()
        intent = parser.parse("reset workflow")
        assert intent.type == IntentType.RESET_WORKFLOW
        assert intent.parameters is not None

    def test_parse_invalid_command(self):
        """Test parsing an invalid command."""
        parser = IntentParser()
        intent = parser.parse("invalid command xyz")
        assert intent.type == IntentType.UNKNOWN
        assert intent.parameters is not None

    def test_parse_with_parameters(self):
        """Test parsing with parameters."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'test' with agent 'gpt4'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None
        assert "name" in intent.parameters or "agent" in intent.parameters

    def test_parse_multiple_commands(self):
        """Test parsing multiple commands."""
        parser = IntentParser()
        intents = parser.parse("create workflow, execute it, get status")
        assert len(intents) == 3
        assert intents[0].type == IntentType.CREATE_WORKFLOW
        assert intents[1].type == IntentType.EXECUTE_WORKFLOW
        assert intents[2].type == IntentType.GET_STATUS

    def test_parse_empty_string(self):
        """Test parsing an empty string."""
        parser = IntentParser()
        intents = parser.parse("")
        assert len(intents) == 0

    def test_parse_whitespace_only(self):
        """Test parsing whitespace only."""
        parser = IntentParser()
        intents = parser.parse("   ")
        assert len(intents) == 0

    def test_parse_special_characters(self):
        """Test parsing special characters."""
        parser = IntentParser()
        intent = parser.parse("create workflow with special chars: @#$%")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_numbers(self):
        """Test parsing numbers."""
        parser = IntentParser()
        intent = parser.parse("create workflow with 5 tasks")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_case_insensitive(self):
        """Test parsing is case insensitive."""
        parser = IntentParser()
        intent1 = parser.parse("CREATE WORKFLOW")
        intent2 = parser.parse("create workflow")
        intent3 = parser.parse("Create Workflow")
        assert intent1.type == intent2.type == intent3.type == IntentType.CREATE_WORKFLOW

    def test_parse_with_quotes(self):
        """Test parsing with quoted strings."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'my workflow'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_commas(self):
        """Test parsing with commas."""
        parser = IntentParser()
        intent = parser.parse("create workflow, named 'test', with agent 'gpt4'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_newlines(self):
        """Test parsing with newlines."""
        parser = IntentParser()
        intent = parser.parse("create workflow\nnamed 'test'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_tabs(self):
        """Test parsing with tabs."""
        parser = IntentParser()
        intent = parser.parse("create workflow\tnamed 'test'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_multiple_spaces(self):
        """Test parsing with multiple spaces."""
        parser = IntentParser()
        intent = parser.parse("create    workflow")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_unicode(self):
        """Test parsing with unicode characters."""
        parser = IntentParser()
        intent = parser.parse("create workflow with unicode: café")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_emoji(self):
        """Test parsing with emoji."""
        parser = IntentParser()
        intent = parser.parse("create workflow 🚀")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_long_string(self):
        """Test parsing with a long string."""
        parser = IntentParser()
        long_string = "create workflow " + "task " * 100
        intent = parser.parse(long_string)
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_special_keywords(self):
        """Test parsing with special keywords."""
        parser = IntentParser()
        intent = parser.parse("create workflow with dependencies")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_numbers_in_name(self):
        """Test parsing with numbers in name."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow123'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_hyphens(self):
        """Test parsing with hyphens."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'my-workflow'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_underscores(self):
        """Test parsing with underscores."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'my_workflow'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_dots(self):
        """Test parsing with dots."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'my.workflow'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_at_sign(self):
        """Test parsing with at sign."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow@test'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_hash(self):
        """Test parsing with hash."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow#1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_dollar(self):
        """Test parsing with dollar sign."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow$1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_percent(self):
        """Test parsing with percent."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow%1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_caret(self):
        """Test parsing with caret."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow^1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_asterisk(self):
        """Test parsing with asterisk."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow*1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_plus(self):
        """Test parsing with plus."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow+1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_equals(self):
        """Test parsing with equals."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow=1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_less_than(self):
        """Test parsing with less than."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow<1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_greater_than(self):
        """Test parsing with greater than."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow>1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_pipe(self):
        """Test parsing with pipe."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow|1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_backslash(self):
        """Test parsing with backslash."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow\\1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_question_mark(self):
        """Test parsing with question mark."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow?1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_exclamation(self):
        """Test parsing with exclamation."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow!1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_exclamation_and_question(self):
        """Test parsing with exclamation and question."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow!?1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_multiple_exclamations(self):
        """Test parsing with multiple exclamations."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow!!1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_multiple_questions(self):
        """Test parsing with multiple questions."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow??1'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_mixed_special_chars(self):
        """Test parsing with mixed special characters."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow!@#$%^&*()'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_numbers_and_special_chars(self):
        """Test parsing with numbers and special characters."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'workflow123!@#'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_unicode_and_special_chars(self):
        """Test parsing with unicode and special characters."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'café!@#'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_emoji_and_special_chars(self):
        """Test parsing with emoji and special characters."""
        parser = IntentParser()
        intent = parser.parse("create workflow named '🚀!@#'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_long_special_chars(self):
        """Test parsing with long special character string."""
        parser = IntentParser()
        long_string = "create workflow named '" + "!@#$%^&*()" * 10 + "'"
        intent = parser.parse(long_string)
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_unicode_and_emoji(self):
        """Test parsing with unicode and emoji."""
        parser = IntentParser()
        intent = parser.parse("create workflow named 'café🚀'")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_mixed_case(self):
        """Test parsing with mixed case."""
        parser = IntentParser()
        intent = parser.parse("CrEaTe WoRkFlOw")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_leading_trailing_spaces(self):
        """Test parsing with leading and trailing spaces."""
        parser = IntentParser()
        intent = parser.parse("   create workflow   ")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_multiple_leading_spaces(self):
        """Test parsing with multiple leading spaces."""
        parser = IntentParser()
        intent = parser.parse("       create workflow")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_multiple_trailing_spaces(self):
        """Test parsing with multiple trailing spaces."""
        parser = IntentParser()
        intent = parser.parse("create workflow       ")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_newlines_and_spaces(self):
        """Test parsing with newlines and spaces."""
        parser = IntentParser()
        intent = parser.parse("   \n\n   create workflow   \n\n   ")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_tabs_and_spaces(self):
        """Test parsing with tabs and spaces."""
        parser = IntentParser()
        intent = parser.parse("   \t\t   create workflow   \t\t   ")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_mixed_whitespace(self):
        """Test parsing with mixed whitespace."""
        parser = IntentParser()
        intent = parser.parse("   \t\n   create workflow   \n\t   ")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_only_whitespace(self):
        """Test parsing with only whitespace."""
        parser = IntentParser()
        intents = parser.parse("   \t\n   ")
        assert len(intents) == 0

    def test_parse_with_only_newlines(self):
        """Test parsing with only newlines."""
        parser = IntentParser()
        intents = parser.parse("\n\n\n")
        assert len(intents) == 0

    def test_parse_with_only_tabs(self):
        """Test parsing with only tabs."""
        parser = IntentParser()
        intents = parser.parse("\t\t\t")
        assert len(intents) == 0

    def test_parse_with_only_spaces(self):
        """Test parsing with only spaces."""
        parser = IntentParser()
        intents = parser.parse("       ")
        assert len(intents) == 0

    def test_parse_with_single_character(self):
        """Test parsing with a single character."""
        parser = IntentParser()
        intent = parser.parse("a")
        assert intent.type == IntentType.UNKNOWN
        assert intent.parameters is not None

    def test_parse_with_single_word(self):
        """Test parsing with a single word."""
        parser = IntentParser()
        intent = parser.parse("workflow")
        assert intent.type == IntentType.UNKNOWN
        assert intent.parameters is not None

    def test_parse_with_two_words(self):
        """Test parsing with two words."""
        parser = IntentParser()
        intent = parser.parse("create workflow")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_three_words(self):
        """Test parsing with three words."""
        parser = IntentParser()
        intent = parser.parse("create a workflow")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_four_words(self):
        """Test parsing with four words."""
        parser = IntentParser()
        intent = parser.parse("create a new workflow")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_five_words(self):
        """Test parsing with five words."""
        parser = IntentParser()
        intent = parser.parse("create a new workflow now")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_six_words(self):
        """Test parsing with six words."""
        parser = IntentParser()
        intent = parser.parse("create a new workflow now please")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_seven_words(self):
        """Test parsing with seven words."""
        parser = IntentParser()
        intent = parser.parse("create a new workflow now please do it")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_eight_words(self):
        """Test parsing with eight words."""
        parser = IntentParser()
        intent = parser.parse("create a new workflow now please do it now")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_nine_words(self):
        """Test parsing with nine words."""
        parser = IntentParser()
        intent = parser.parse("create a new workflow now please do it now go")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None

    def test_parse_with_ten_words(self):
        """Test parsing with ten words."""
        parser = IntentParser()
        intent = parser.parse("create a new workflow now please do it now go ahead")
        assert intent.type == IntentType.CREATE_WORKFLOW
        assert intent.parameters is not None
