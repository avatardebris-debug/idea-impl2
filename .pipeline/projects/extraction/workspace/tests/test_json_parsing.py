"""
test_json_parsing.py — Unit tests for _parse_json_from_response edge cases.

Covers: valid JSON object, valid JSON array, no braces, partial/malformed JSON,
        JSON with extra text before/after, nested JSON.
"""
import pytest
from extraction.extractor import _parse_json_from_response


# ---------------------------------------------------------------------------
# Test: valid JSON object
# ---------------------------------------------------------------------------

class TestValidJsonObject:
    def test_simple_object(self):
        text = '{"name": "test", "value": 42}'
        result = _parse_json_from_response(text)
        assert result == {"name": "test", "value": 42}

    def test_object_with_nested_structure(self):
        text = '{"a": {"b": {"c": 1}}, "d": [1, 2, 3]}'
        result = _parse_json_from_response(text)
        assert result == {"a": {"b": {"c": 1}}, "d": [1, 2, 3]}

    def test_object_with_empty_values(self):
        text = '{"title": "", "steps": [], "tips": []}'
        result = _parse_json_from_response(text)
        assert result == {"title": "", "steps": [], "tips": []}

    def test_object_with_special_characters(self):
        text = '{"action": "Mix flour & water", "detail": "Use a large bowl (5L)"}'
        result = _parse_json_from_response(text)
        assert result["action"] == "Mix flour & water"
        assert result["detail"] == "Use a large bowl (5L)"


# ---------------------------------------------------------------------------
# Test: valid JSON array
# ---------------------------------------------------------------------------

class TestValidJsonArray:
    def test_simple_array(self):
        text = '[1, 2, 3]'
        result = _parse_json_from_response(text)
        assert result == [1, 2, 3]

    def test_array_of_objects(self):
        text = '[{"name": "a"}, {"name": "b"}]'
        result = _parse_json_from_response(text)
        assert result == [{"name": "a"}, {"name": "b"}]

    def test_nested_array(self):
        text = '[[1, 2], [3, 4]]'
        result = _parse_json_from_response(text)
        assert result == [[1, 2], [3, 4]]


# ---------------------------------------------------------------------------
# Test: no braces / no JSON
# ---------------------------------------------------------------------------

class TestNoBraces:
    def test_no_braces_returns_empty_dict(self):
        text = "This is just plain text with no JSON"
        result = _parse_json_from_response(text)
        assert result == {}

    def test_empty_string_returns_empty_dict(self):
        result = _parse_json_from_response("")
        assert result == {}

    def test_whitespace_only_returns_empty_dict(self):
        result = _parse_json_from_response("   \n  ")
        assert result == {}


# ---------------------------------------------------------------------------
# Test: partial / malformed JSON
# ---------------------------------------------------------------------------

class TestMalformedJson:
    def test_unclosed_brace(self):
        text = '{"name": "test"'
        result = _parse_json_from_response(text)
        # Should return empty dict since JSON is invalid
        assert result == {}

    def test_missing_quotes(self):
        text = '{name: "test"}'
        result = _parse_json_from_response(text)
        assert result == {}

    def test_trailing_comma(self):
        text = '{"name": "test",}'
        result = _parse_json_from_response(text)
        assert result == {}

    def test_single_quote_strings(self):
        text = "{'name': 'test'}"
        result = _parse_json_from_response(text)
        assert result == {}

    def test_mixed_valid_invalid(self):
        text = '{"valid": true} {"invalid": }'
        result = _parse_json_from_response(text)
        # Should parse the first valid JSON object
        assert result == {"valid": True}


# ---------------------------------------------------------------------------
# Test: JSON with extra text before/after
# ---------------------------------------------------------------------------

class TestExtraText:
    def test_text_before_json(self):
        text = 'Here is the result: {"name": "test"}'
        result = _parse_json_from_response(text)
        assert result == {"name": "test"}

    def test_text_after_json(self):
        text = '{"name": "test"} End of response.'
        result = _parse_json_from_response(text)
        assert result == {"name": "test"}

    def test_text_before_and_after(self):
        text = 'Sure, here is the JSON: {"key": "value"} Hope that helps!'
        result = _parse_json_from_response(text)
        assert result == {"key": "value"}

    def test_multiline_with_extra_text(self):
        text = (
            "Here's the extraction:\n"
            '{\n'
            '  "title": "Test",\n'
            '  "steps": [1, 2, 3]\n'
            '}\n'
            "Hope this works!"
        )
        result = _parse_json_from_response(text)
        assert result == {"title": "Test", "steps": [1, 2, 3]}

    def test_markdown_code_block(self):
        text = '```json\n{"name": "test"}\n```'
        result = _parse_json_from_response(text)
        assert result == {"name": "test"}


# ---------------------------------------------------------------------------
# Test: nested JSON structures
# ---------------------------------------------------------------------------

class TestNestedJson:
    def test_deeply_nested_object(self):
        text = '{"a": {"b": {"c": {"d": {"e": "deep"}}}}}'
        result = _parse_json_from_response(text)
        assert result["a"]["b"]["c"]["d"]["e"] == "deep"

    def test_complex_extraction_schema(self):
        text = (
            '{"title": "Sourdough Guide", "topic": "baking", "format": "recipe", '
            '"description": "How to make sourdough", '
            '"components": [{"name": "flour", "quantity": "500", "unit": "g", "notes": "bread flour"}], '
            '"steps": [{"step_number": 1, "action": "Mix", "detail": "Mix flour and water", '
            '"duration": "5 min", "tools": ["bowl"], "warnings": ["use fresh flour"]}], '
            '"tips": ["keep warm"], '
            '"metadata": {"source_length": 100, "model": "qwen3:6b"}}'
        )
        result = _parse_json_from_response(text)
        assert result["title"] == "Sourdough Guide"
        assert result["format"] == "recipe"
        assert len(result["components"]) == 1
        assert result["components"][0]["name"] == "flour"
        assert len(result["steps"]) == 1
        assert result["steps"][0]["step_number"] == 1
        assert result["metadata"]["model"] == "qwen3:6b"

    def test_array_of_nested_objects(self):
        text = (
            '[{"step_number": 1, "action": "A"}, '
            '{"step_number": 2, "action": "B"}, '
            '{"step_number": 3, "action": "C"}]'
        )
        result = _parse_json_from_response(text)
        assert len(result) == 3
        assert result[1]["action"] == "B"


# ---------------------------------------------------------------------------
# Test: edge cases with JSON content
# ---------------------------------------------------------------------------

class TestJsonEdgeCases:
    def test_json_with_unicode(self):
        text = '{"emoji": "🍞", "name": "日本語テスト"}'
        result = _parse_json_from_response(text)
        assert result["emoji"] == "🍞"
        assert result["name"] == "日本語テスト"

    def test_json_with_numbers(self):
        text = '{"int": 42, "float": 3.14, "neg": -10, "zero": 0}'
        result = _parse_json_from_response(text)
        assert result["int"] == 42
        assert result["float"] == 3.14
        assert result["neg"] == -10
        assert result["zero"] == 0

    def test_json_with_booleans(self):
        text = '{"yes": true, "no": false, "null_val": null}'
        result = _parse_json_from_response(text)
        assert result["yes"] is True
        assert result["no"] is False
        assert result["null_val"] is None

    def test_multiple_json_objects_returns_first(self):
        text = '{"first": 1} {"second": 2}'
        result = _parse_json_from_response(text)
        assert result == {"first": 1}

    def test_json_array_in_object(self):
        text = '{"items": [1, 2, {"nested": true}]}'
        result = _parse_json_from_response(text)
        assert result["items"][2]["nested"] is True
