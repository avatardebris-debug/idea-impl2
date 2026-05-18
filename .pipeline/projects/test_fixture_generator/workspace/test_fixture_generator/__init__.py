"""
Test Fixture Generator — Real-Data & Edge-Case Engine
======================================================

Three complementary modules:

  sampler.py    — scans real pipeline workspace files and extracts actual data
                  rows/objects as fixtures (what the code actually touches)
  edge_cases.py — takes a valid fixture and mutates it into boundary conditions
                  designed to break code (nulls, type flips, encoding bombs,
                  out-of-range values, missing keys)
  recorder.py   — VCR-style HTTP record/replay so tests use captured network
                  responses, not imaginary ones

  __init__.py   — re-exports public API
"""
