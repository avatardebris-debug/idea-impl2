"""tests/test_pipeline.py — unit tests for csv_data_pipeline_builder"""
import pathlib, sys, csv, json
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from csv_data_pipeline_builder.nodes import FilterNode, SelectNode, AggregateNode, JoinNode, PivotNode
from csv_data_pipeline_builder.pipeline import Pipeline, CsvSink, JsonSink, SqliteSink

SALES = [
    {"id": "1", "region": "North", "category": "A", "revenue": "100", "year": "2024"},
    {"id": "2", "region": "South", "category": "B", "revenue": "200", "year": "2024"},
    {"id": "3", "region": "North", "category": "A", "revenue": "150", "year": "2023"},
    {"id": "4", "region": "East",  "category": "B", "revenue": "300", "year": "2024"},
    {"id": "5", "region": "North", "category": "B", "revenue": "50",  "year": "2024"},
]
CUSTOMERS = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}, {"id": "4", "name": "Charlie"}]


# --- FilterNode ---
def test_filter_keeps_matching():
    result = FilterNode(predicate_expr="year == '2024'").transform(SALES)
    assert len(result) == 4

def test_filter_none_matching():
    assert FilterNode(predicate_expr="year == '2099'").transform(SALES) == []


# --- SelectNode ---
def test_select_projects():
    result = SelectNode(columns=["id", "region"]).transform(SALES)
    assert all(set(r.keys()) == {"id", "region"} for r in result)

def test_select_rename():
    node = SelectNode(columns=["order_id", "area"], rename={"order_id": "id", "area": "region"})
    result = node.transform(SALES)
    assert all("order_id" in r for r in result)


# --- AggregateNode ---
def test_aggregate_sum():
    result = AggregateNode(group_by=["region"], aggregations={"revenue": "sum"}).transform(SALES)
    north = next(r for r in result if r["region"] == "North")
    assert north["revenue"] == pytest.approx(300.0)

def test_aggregate_count():
    result = AggregateNode(group_by=["category"], aggregations={"id": "count"}).transform(SALES)
    cat_a = next(r for r in result if r["category"] == "A")
    assert cat_a["id"] == 2


# --- JoinNode ---
def test_join_inner():
    result = JoinNode(left_key="id", right_key="id", how="inner", right_rows=CUSTOMERS).transform(SALES)
    assert len(result) == 3
    assert all("name" in r for r in result)

def test_join_left():
    result = JoinNode(left_key="id", right_key="id", how="left", right_rows=CUSTOMERS).transform(SALES)
    assert len(result) == 5


# --- PivotNode ---
def test_pivot():
    long = [
        {"product": "A", "metric": "sales", "value": "100"},
        {"product": "A", "metric": "returns", "value": "5"},
        {"product": "B", "metric": "sales", "value": "200"},
    ]
    result = PivotNode(index=["product"], columns="metric", values="value", agg="first").transform(long)
    assert len(result) == 2
    a = next(r for r in result if r["product"] == "A")
    assert a["sales"] == "100"


# --- Pipeline integration ---
def test_pipeline_chain():
    p = Pipeline()
    p.add_node(FilterNode(predicate_expr="year == '2024'"))
    p.add_node(SelectNode(columns=["id", "region"]))
    rows, reports = p.execute(SALES)
    assert len(rows) == 4
    assert all("year" not in r for r in rows)
    assert len(reports) == 2

def test_pipeline_json_sink(tmp_path):
    out = str(tmp_path / "out.json")
    p = Pipeline()
    p.add_sink(JsonSink(path=out))
    p.execute(SALES)
    assert len(json.loads(pathlib.Path(out).read_text())) == len(SALES)

def test_pipeline_sqlite_sink(tmp_path):
    import sqlite3
    out = str(tmp_path / "out.db")
    Pipeline().add_sink(SqliteSink(path=out, table="t")).execute(SALES)
    conn = sqlite3.connect(out)
    rows = conn.execute("SELECT * FROM t").fetchall()
    conn.close()
    assert len(rows) == len(SALES)

def test_dry_run_schema():
    p = Pipeline()
    p.add_node(SelectNode(columns=["id", "region"]))
    assert p.dry_run_schema(SALES[:3]) == ["id", "region"]
