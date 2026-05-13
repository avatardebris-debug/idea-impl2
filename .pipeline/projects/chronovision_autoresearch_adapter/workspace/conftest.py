import sys, pathlib
# Injected by pipeline validator — ensures local imports work in pytest
_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))
