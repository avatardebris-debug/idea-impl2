"""Comprehensive test sweep of all pipeline projects."""
import os
import subprocess
import json
import time

# Use the actual base directory on this system
base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pipeline', 'projects')

# All projects from the audit (timeout + broken + mixed categories)
projects = [
    # Previously timeout
    'consistent_character_developer',
    'consistent_scene_developer',
    'docsai_documentation_generator',
    'drop_servicing_tool',
    'financial_document_analyzer',
    'football_nfl_draft_and_recruit_optimizer',
    'forensic2',
    'market_strategy_backtester',
    'player_attribute_library',
    'sec_importer',
    'supportagent_workflow_builder',
    'tim_ferriss_learning_tool',
    'transcript_extractor',
    'video_ingestor_summary',
    'ai_movie_generation_suite_2',
    'chronovision',
    'chronovision2',
    'football_simulator',
    # Previously broken
    'financial_portfolio_simulator',
    'forensic',
    'osint_corp',
    'sec_importer2',
    'sopdata_ingestion_bridge',
    'url_health_checker',
    'scott_adams_botllm_fine_tuning',
    'video_langfake',
    'video_management',
    # Previously mixed
    'fiverr_job_automation_tool',
    'human_in_the_loop_reviewer',
    'tableau_integration_module',
    'video_babbel',
    'ai_movie_generation_suite',
    # Previously passing
    'dynamic_pricing_integrator',
    'ffo',
    'movieseries_auto_tracker',
    'multi_format_export_engine',
    'nda_contract_generator',
    'pocketknife_of_the_internet',
    'rule_based_triage_engine',
    'udemy_training_tool',
]

results = {}

for proj in projects:
    proj_dir = os.path.join(base_dir, proj, 'workspace')
    
    # Check if project exists
    if not os.path.exists(proj_dir):
        results[proj] = {'status': 'NOT_FOUND', 'detail': 'workspace dir missing'}
        continue
    
    # Check if tests/ dir exists
    tests_dir = os.path.join(proj_dir, 'tests')
    if not os.path.exists(tests_dir):
        # Some projects put tests in root
        results[proj] = {'status': 'NO_TESTS_DIR', 'detail': 'no tests/ directory'}
        continue
    
    print(f"Running: {proj}...", end=" ", flush=True)
    start = time.time()
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-q', '--tb=no', '--no-header'],
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
        
        results[proj] = {
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
        results[proj] = {'status': 'TIMEOUT', 'elapsed': round(elapsed, 1), 'detail': 'timed out after 60s'}
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
