import sys, pathlib
_ws = pathlib.Path(__file__).parent.parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))
