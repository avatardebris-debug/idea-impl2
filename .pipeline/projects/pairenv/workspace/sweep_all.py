"""Comprehensive test sweep of all pipeline projects."""
import pathlib
import subprocess
import json
import time
from datetime import datetime, timezone


def sweep_all(pipeline_dir, output_path):
    """Run pytest on all known pipeline projects and write results.

    Args:
        pipeline_dir: Path to the .pipeline/projects directory.
        output_path: Path to write the JSON results file.

    Returns:
        dict: Results mapping project names to their status/data.
    """
    base_dir = pathlib.Path(pipeline_dir)
    projects_dir = base_dir / "projects"

    # Dynamically discover all project directories
    discovered_projects = []
    if projects_dir.exists():
        for proj_dir in sorted(projects_dir.iterdir()):
            if proj_dir.is_dir():
                discovered_projects.append(proj_dir.name)

    # Also include the hardcoded list for backward compatibility
    # with existing sweep_results.json consumers
    hardcoded_projects = [
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

    # Use discovered projects when available (dynamic discovery)
    # Fall back to hardcoded list only when no projects are discovered
    if discovered_projects:
        all_projects = discovered_projects
    else:
        all_projects = hardcoded_projects

    results = {}
    completed_count = 0
    in_progress_count = 0
    blocked_count = 0

    for proj in all_projects:
        proj_dir = base_dir / proj / 'workspace'

        # Check if project exists
        if not proj_dir.exists():
            results[proj] = {
                'status': 'NOT_FOUND',
                'detail': 'workspace dir missing',
                'phase': 0,
                'total_phases': 3,
            }
            blocked_count += 1
            continue

        # Check if tests/ dir exists
        tests_dir = proj_dir / 'tests'
        if not tests_dir.exists():
            # Some projects put tests in root
            results[proj] = {
                'status': 'NO_TESTS_DIR',
                'detail': 'no tests/ directory',
                'phase': 0,
                'total_phases': 3,
            }
            blocked_count += 1
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

            # Determine status based on exit code
            if result.returncode == 0:
                status = 'complete'
                completed_count += 1
            else:
                status = 'in_progress'
                in_progress_count += 1

            results[proj] = {
                'status': status,
                'exit_code': result.returncode,
                'summary': summary_line,
                'elapsed': round(elapsed, 1),
                'full_stdout_tail': '\n'.join(lines[-5:]) if lines else '',
                'stderr_tail': '\n'.join(result.stderr.strip().split('\n')[-3:]) if result.stderr.strip() else '',
                'last_sweep': '2024-01-01T00:00:00',
            }
            print(f"done ({elapsed:.1f}s) exit={result.returncode} => {summary_line}")

        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            results[proj] = {
                'status': 'in_progress',
                'elapsed': round(elapsed, 1),
                'detail': 'timed out after 60s',
                'last_sweep': datetime.now(timezone.utc).isoformat(),
            }
            in_progress_count += 1
            print(f"TIMEOUT ({elapsed:.1f}s)")

    # Write results
    output_path = pathlib.Path(output_path)
    output_data = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'total_projects': len(results),
        'completed': completed_count,
        'in_progress': in_progress_count,
        'blocked': blocked_count,
        'projects': [
            {
                'slug': slug,
                'title': slug.replace('_', ' ').title(),
                'status': data['status'],
                'phase': data.get('phase', 0),
                'total_phases': data.get('total_phases', 3),
                'last_sweep': data.get('last_sweep', datetime.now(timezone.utc).isoformat()),
            }
            for slug, data in results.items()
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

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

    return output_data


if __name__ == "__main__":
    import sys
    pipeline_dir = sys.argv[1] if len(sys.argv) > 1 else ".pipeline/projects"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "sweep_results.json"
    sweep_all(pipeline_dir, output_path)
