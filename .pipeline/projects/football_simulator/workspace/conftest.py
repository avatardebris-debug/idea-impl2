import sys, pathlib

# CRITICAL: Fix sys.path BEFORE anything else is imported.
# The path '/workspace/idea impl' causes 'workspace' to be treated as a package,
# which breaks conftest.py import. Remove it immediately.
sys.path = [p for p in sys.path if p != '/workspace/idea impl']
sys.path = [p for p in sys.path if p != '/workspace/idea impl/.pipeline/projects/forensic/workspace/src']

# Injected by pipeline validator — ensures local imports work in pytest
_ws = pathlib.Path(__file__).parent
# Remove parent paths that cause 'workspace.' prefix issues
sys.path = [p for p in sys.path if str(_ws) not in p and p != str(_ws.parent)]
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))
