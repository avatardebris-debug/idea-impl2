"""Comprehensive test sweep of all pipeline and extras projects."""
import os
import subprocess
import json
import time
import sys

base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline', 'projects')
extras_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'extras')

# Dynamically discover all projects that actually exist on disk
projects = []

# 1. Discover pipeline/projects/<name>/workspace directories
if os.path.isdir(base_dir):
    for entry in sorted(os.listdir(base_dir)):
        proj_dir = os.path.join(base_dir, entry, 'workspace')
        if os.path.isdir(proj_dir):
            projects.append((entry, proj_dir, 'pipeline'))

# 2. Discover extras/<name> directories (skip files and non-project dirs)
if os.path.isdir(extras_dir):
    for entry in sorted(os.listdir(extras_dir)):
        extras_path = os.path.join(extras_dir, entry)
        if os.path.isdir(extras_path) and not entry.startswith('.'):
            projects.append((entry, extras_path, 'extras'))

results = {}

for proj_name, proj_dir, source in projects:
    # Check if tests/ dir exists in project
    tests_dir = os.path.join(proj_dir, 'tests')
    
    # If not in project, check for shared extras/tests
    if not os.path.exists(tests_dir):
        shared_tests = os.path.join(extras_dir, 'tests')
        if os.path.exists(shared_tests):
            tests_dir = shared_tests
            # For shared tests, we need to run from the project dir but point to shared tests
            # We'll handle this specially below
        else:
            results[proj_name] = {'status': 'NO_TESTS_DIR', 'detail': 'no tests/ directory'}
            continue
    
    # Normalize tests_dir for comparison
    tests_dir = os.path.normpath(tests_dir)
    
    print(f"Running: {proj_name}...", end=" ", flush=True)
    start = time.time()
    try:
        # Determine test path
        if tests_dir == os.path.join(extras_dir, 'tests'):
            # Shared tests - run from project dir but specify test path
            test_path = os.path.join('..', 'extras', 'tests')
        else:
            test_path = 'tests/'
        
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', test_path, '-q', '--tb=no', '--no-header'],
            cwd=proj_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        elapsed = time.time() - start
        stdout = result.stdout.strip()
        # Get last line which has the summary
        lines = [l for l in stdout.split('\n') if l.strip()]
        summary_line = lines[-1] if lines else "no output"
        
        results[proj_name] = {
            'status': 'COMPLETED',
            'exit_code': result.returncode,
            'summary': summary_line,
            'elapsed': round(elapsed, 1),
            'full_stdout_tail': '\n'.join(lines[-5:]) if lines else '',
            'stderr_tail': '\n'.join(result.stderr.strip().split('\n')[-3:]) if result.stderr.strip() else ''
        }
        print(f"done ({elapsed:.1f}s) exit={result.returncode} => {summary_line}")
        
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        results[proj_name] = {'status': 'TIMEOUT', 'elapsed': round(elapsed, 1), 'detail': 'timed out after 60s'}
        print(f"TIMEOUT ({elapsed:.1f}s)")

# Write results
sweep_results_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sweep_results.json')
with open(sweep_results_path, 'w') as f:
    json.dump(results, f, indent=2)

# Print summary table
print("\n" + "="*80)
print(f"{'Project':<45} {'Status':<12} {'Result'}")
print("="*80)

for proj, data in results.items():
    status = data['status']
    if status == 'COMPLETED':
        print(f"{proj:<45} {'OK' if data['exit_code']==0 else 'FAIL':<12} {data['summary']}")
    elif status == 'TIMEOUT':
        print(f"{proj:<45} {'TIMEOUT':<12} hung after 60s")
    elif status == 'NO_TESTS_DIR':
        print(f"{proj:<45} {'SKIP':<12} no tests/ directory")
    else:
        print(f"{proj:<45} {status:<12} {data.get('detail','')}")

# Count summary
total = len(results)
not_found = sum(1 for d in results.values() if d['status'] == 'NOT_FOUND')
no_tests = sum(1 for d in results.values() if d['status'] == 'NO_TESTS_DIR')
completed = sum(1 for d in results.values() if d['status'] == 'COMPLETED')
timed_out = sum(1 for d in results.values() if d['status'] == 'TIMEOUT')
passed = sum(1 for d in results.values() if d.get('status') == 'COMPLETED' and d.get('exit_code') == 0)
failed = sum(1 for d in results.values() if d.get('status') == 'COMPLETED' and d.get('exit_code') != 0)

print("\n" + "-"*80)
print(f"Total projects: {total} | Found: {total - not_found} | Not found: {not_found}")
print(f"Tests dir missing: {no_tests} | Completed: {completed} | Passed: {passed} | Failed: {failed} | Timeout: {timed_out}")
