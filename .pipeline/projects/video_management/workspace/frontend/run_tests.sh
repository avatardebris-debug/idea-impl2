#!/bin/bash

# Test runner script for Video Management Platform
# Usage: ./run_tests.sh [unit|e2e|all]

set -e

cd "$(dirname "$0")"

echo "=========================================="
echo "Video Management Platform - Test Runner"
echo "=========================================="

case "${1:-all}" in
  unit)
    echo "Running unit tests..."
    npx vitest run
    ;;
  e2e)
    echo "Running E2E tests..."
    npx playwright test
    ;;
  all)
    echo "Running all tests..."
    echo ""
    echo "=== Unit Tests ==="
    npx vitest run
    echo ""
    echo "=== E2E Tests ==="
    npx playwright test
    ;;
  coverage)
    echo "Running tests with coverage..."
    npx vitest run --coverage
    ;;
  *)
    echo "Usage: $0 [unit|e2e|all|coverage]"
    echo ""
    echo "  unit     - Run unit tests only"
    echo "  e2e      - Run E2E tests only"
    echo "  all      - Run all tests"
    echo "  coverage - Run tests with coverage report"
    exit 1
    ;;
esac

echo ""
echo "=========================================="
echo "Tests completed successfully!"
echo "=========================================="
