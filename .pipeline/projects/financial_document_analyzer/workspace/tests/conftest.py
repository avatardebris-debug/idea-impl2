import sys
import pathlib

# Inject workspace into sys.path so tests can import the package
_ws = pathlib.Path(__file__).parent.parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))
