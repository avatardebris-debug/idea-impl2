import sys, pathlib
# Injected by pipeline validator — ensures local imports work in pytest
_ws = pathlib.Path(__file__).parent
# Add src/ to path so `import sec_importer` works
_src = _ws / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
