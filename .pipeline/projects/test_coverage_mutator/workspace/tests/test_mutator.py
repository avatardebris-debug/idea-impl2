"""Tests for mutator."""

from test_coverage_mutator.mutator import mutate_source_code

def test_mutate_eq():
    source = "if x == 1:\n    pass"
    mutated = mutate_source_code(source)
    assert "x != 1" in mutated

def test_mutate_gt():
    source = "if a > b:\n    pass"
    mutated = mutate_source_code(source)
    assert "a <= b" in mutated

def test_no_mutation():
    source = "print('hello')"
    mutated = mutate_source_code(source)
    assert "print('hello')" in mutated
