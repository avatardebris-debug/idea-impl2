import os
import subprocess

projects = [
    'consistent_character_developer',
    'consistent_scene_developer',
    'docsai_documentation_generator',
    'drop_servicing_tool',
    'financial_document_analyzer',
    'financial_portfolio_simulator',
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

base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.pipeline', 'projects')
all_reqs = []

for proj in projects:
    req_path = os.path.join(base_dir, proj, 'workspace', 'requirements.txt')
    if os.path.exists(req_path):
        all_reqs.append(req_path)
        print(f'Found {req_path}')
        
with open('master_reqs.txt', 'w') as f:
    for req in all_reqs:
        f.write(f'-r \"{req}\"\n')

print(f'Generated master_reqs.txt with {len(all_reqs)} files.')
subprocess.run(['pip', 'install', '-r', 'master_reqs.txt'])
