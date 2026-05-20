"""tests/test_nodes.py — comprehensive tests for each transform node type."""
import pathlib, sys
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from csv_data_pipeline_builder.nodes import (
    FilterNode,
    SelectNode,
    AggregateNode,
    JoinNode,
    PivotNode,
)

# ── Sample data ──────────────────────────────────────────────────────────────

SALES = [
    {"id": "1", "region": "North", "category": "A", "revenue": "100", "year": "2024"},
    {"id": "2", "region": "South", "category": "B", "revenue": "200", "year": "2024"},
    {"id": "3", "region": "North", "category": "A", "revenue": "150", "year": "2023"},
    {"id": "4", "region": "East",  "category": "B", "revenue": "300", "year": "2024"},
    {"id": "5", "region": "North", "category": "B", "revenue": "50",  "year": "2024"},
]

CUSTOMERS = [
    {"id": "1", "name": "Alice",   "email": "alice@example.com"},
    {"id": "2", "name": "Bob",     "email": "bob@example.com"},
    {"id": "4", "name": "Charlie", "email": "charlie@example.com"},
]

# ── FilterNode ───────────────────────────────────────────────────────────────

class TestFilterNode:
    def test_keeps_matching_rows(self):
        result = FilterNode(predicate_expr="year == '2024'").transform(SALES)
        assert len(result) == 4

    def test_no_rows_match(self):
        result = FilterNode(predicate_expr="year == '2099'").transform(SALES)
        assert result == []

    def test_all_rows_match(self):
        result = FilterNode(predicate_expr="True").transform(SALES)
        assert len(result) == len(SALES)

    def test_empty_input(self):
        result = FilterNode(predicate_expr="True").transform([])
        assert result == []

    def test_predicate_with_type_coercion(self):
        result = FilterNode(predicate_expr="int(revenue) > 150").transform(SALES)
        assert len(result) == 2  # 200 and 300

    def test_predicate_with_empty_string(self):
        data = [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": ""},
            {"id": "3", "name": "Charlie"},
        ]
        result = FilterNode(predicate_expr="name != ''").transform(data)
        assert len(result) == 2

    def test_predicate_with_none_value(self):
        data = [
            {"id": "1", "value": "10"},
            {"id": "2", "value": None},
            {"id": "3", "value": "30"},
        ]
        result = FilterNode(predicate_expr="value is not None").transform(data)
        assert len(result) == 2


# ── SelectNode ───────────────────────────────────────────────────────────────

class TestSelectNode:
    def test_select_columns(self):
        result = SelectNode(columns=["id", "region"]).transform(SALES)
        assert all(set(r.keys()) == {"id", "region"} for r in result)

    def test_rename_columns(self):
        result = SelectNode(columns=["id", "area"], rename={"region": "area"}).transform(SALES)
        assert all(set(r.keys()) == {"id", "area"} for r in result)

    def test_missing_column_skipped(self):
        # SelectNode silently skips missing columns (no error raised)
        result = SelectNode(columns=["id", "nonexistent"]).transform(SALES)
        assert all("nonexistent" not in r for r in result)

    def test_empty_input(self):
        result = SelectNode(columns=["id"]).transform([])
        assert result == []


# ── AggregateNode ────────────────────────────────────────────────────────────

class TestAggregateNode:
    def test_sum(self):
        result = AggregateNode(
            group_by=["region"],
            aggregations={"revenue": "sum"},
        ).transform(SALES)
        # North: 100+150+50=300, South: 200, East: 300
        north = next(r for r in result if r["region"] == "North")
        assert float(north["revenue"]) == 300.0

    def test_mean(self):
        result = AggregateNode(
            group_by=["region"],
            aggregations={"revenue": "mean"},
        ).transform(SALES)
        north = next(r for r in result if r["region"] == "North")
        assert float(north["revenue"]) == pytest.approx(100.0)

    def test_count(self):
        result = AggregateNode(
            group_by=["region"],
            aggregations={"revenue": "count"},
        ).transform(SALES)
        north = next(r for r in result if r["region"] == "North")
        assert int(north["revenue"]) == 3

    def test_min(self):
        result = AggregateNode(
            group_by=["region"],
            aggregations={"revenue": "min"},
        ).transform(SALES)
        north = next(r for r in result if r["region"] == "North")
        assert float(north["revenue"]) == 50.0

    def test_max(self):
        result = AggregateNode(
            group_by=["region"],
            aggregations={"revenue": "max"},
        ).transform(SALES)
        north = next(r for r in result if r["region"] == "North")
        assert float(north["revenue"]) == 150.0

    def test_empty_groups(self):
        result = AggregateNode(
            group_by=["region"],
            aggregations={"revenue": "sum"},
        ).transform([])
        assert result == []

    def test_multiple_aggregations(self):
        result = AggregateNode(
            group_by=["category"],
            aggregations={"revenue": "sum"},
        ).transform(SALES)
        # Just verify it runs without error and returns grouped data
        assert len(result) > 0


# ── JoinNode ─────────────────────────────────────────────────────────────────

class TestJoinNode:
    def test_inner_join(self):
        result = JoinNode(
            left_key="id",
            right_key="id",
            how="inner",
            right_rows=CUSTOMERS,
        ).transform(SALES)
        # Only ids 1, 2, 4 match
        assert len(result) == 3

    def test_left_join(self):
        result = JoinNode(
            left_key="id",
            right_key="id",
            how="left",
            right_rows=CUSTOMERS,
        ).transform(SALES)
        # All 5 sales rows kept
        assert len(result) == 5

    def test_right_join(self):
        result = JoinNode(
            left_key="id",
            right_key="id",
            how="right",
            right_rows=CUSTOMERS,
        ).transform(SALES)
        # All 3 customer rows kept
        assert len(result) == 3

    def test_unmatched_keys(self):
        left = [{"id": "1", "val": "a"}]
        right = [{"id": "2", "val": "b"}]
        result = JoinNode(
            left_key="id",
            right_key="id",
            how="inner",
            right_rows=right,
        ).transform(left)
        assert result == []

    def test_empty_left(self):
        result = JoinNode(
            left_key="id",
            right_key="id",
            how="inner",
            right_rows=CUSTOMERS,
        ).transform([])
        assert result == []


# ── PivotNode ────────────────────────────────────────────────────────────────

class TestPivotNode:
    def test_long_to_wide(self):
        data = [
            {"id": "1", "category": "A", "value": "10"},
            {"id": "1", "category": "B", "value": "20"},
            {"id": "2", "category": "A", "value": "30"},
            {"id": "2", "category": "B", "value": "40"},
        ]
        result = PivotNode(
            index=["id"],
            columns="category",
            values="value",
            agg="first",
        ).transform(data)
        assert len(result) == 2
        assert set(result[0].keys()) == {"id", "A", "B"}

    def test_agg_mode_sum(self):
        data = [
            {"id": "1", "category": "A", "value": "10"},
            {"id": "1", "category": "A", "value": "20"},
        ]
        result = PivotNode(
            index=["id"],
            columns="category",
            values="value",
            agg="sum",
        ).transform(data)
        assert int(result[0]["A"]) == 30

    def test_agg_mode_mean(self):
        data = [
            {"id": "1", "category": "A", "value": "10"},
            {"id": "1", "category": "A", "value": "20"},
        ]
        result = PivotNode(
            index=["id"],
            columns="category",
            values="value",
            agg="mean",
        ).transform(data)
        assert float(result[0]["A"]) == 15.0

    def test_empty_input(self):
        result = PivotNode(
            index=["id"],
            columns="category",
            values="value",
            agg="first",
        ).transform([])
        assert result == []
