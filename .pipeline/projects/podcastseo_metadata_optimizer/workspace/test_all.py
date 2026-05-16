import os
import subprocess

projects = [
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
    'football_simulator'
]

base_dir = r'c:\Users\avata\aicompete\idea impl\.pipeline\projects'

for proj in projects:
    proj_dir = os.path.join(base_dir, proj, 'workspace')
    if os.path.exists(proj_dir):
        print(f"\n================ Running tests for {proj} ================")
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', 'tests/'], 
                cwd=proj_dir, 
                capture_output=True, 
                text=True,
                timeout=15
            )
            print(f"Exit code: {result.returncode}")
            lines = result.stdout.strip().split('\n')
            for line in lines[-5:]:
                print(line)
            if result.stderr:
                print("STDERR snippet:")
                print("\n".join(result.stderr.strip().split('\n')[-5:]))
        except subprocess.TimeoutExpired:
            print("==> Process timed out after 15 seconds! This test hangs.")
    else:
        print(f"\n================ Project not found: {proj} ================")

