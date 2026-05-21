"""
Tests for json_skill.dispatcher module.
"""

from json_skill.dispatcher import FunctionDispatcher


# ---------- register / unregister ---

def test_register_and_dispatch():
    """Register a function and dispatch it."""
    disp = FunctionDispatcher()

    def add(a, b):
        return a + b

    disp.register("add", add)
    result = disp.dispatch("add", {"a": 3, "b": 4})
    assert result == 7


def test_register_lambda():
    """Register a lambda function."""
    disp = FunctionDispatcher()
    disp.register("double", lambda x: x * 2)
    result = disp.dispatch("double", {"x": 5})
    assert result == 10


def test_register_overwrite():
    """Re-registering a function name overwrites the old handler."""
    disp = FunctionDispatcher()
    disp.register("fn", lambda x: 1)
    disp.register("fn", lambda x: 2)
    result = disp.dispatch("fn", {"x": 0})
    assert result == 2


def test_unregister():
    """Unregister removes a function."""
    disp = FunctionDispatcher()
    disp.register("fn", lambda x: 1)
    disp.unregister("fn")
    assert "fn" not in disp._registry


def test_unregister_nonexistent():
    """Unregistering a nonexistent function does nothing."""
    disp = FunctionDispatcher()
    disp.unregister("nonexistent")  # should not raise


def test_dispatch_unknown_function():
    """Dispatching an unknown function returns None."""
    disp = FunctionDispatcher()
    result = disp.dispatch("unknown", {})
    assert result is None


def test_dispatch_with_no_params():
    """Dispatch a function that takes no parameters."""
    disp = FunctionDispatcher()
    disp.register("hello", lambda: "hi")
    result = disp.dispatch("hello", {})
    assert result == "hi"


def test_dispatch_with_kwargs():
    """Dispatch passes keyword arguments correctly."""
    disp = FunctionDispatcher()
    disp.register("greet", lambda name, greeting="Hello": f"{greeting}, {name}!")
    result = disp.dispatch("greet", {"name": "World", "greeting": "Hi"})
    assert result == "Hi, World!"


def test_dispatch_with_mixed_args():
    """Dispatch with positional and keyword args."""
    disp = FunctionDispatcher()
    disp.register("concat", lambda a, b: a + b)
    result = disp.dispatch("concat", {"a": "foo", "b": "bar"})
    assert result == "foobar"


def test_list_functions():
    """list_functions returns registered function names."""
    disp = FunctionDispatcher()
    disp.register("a", lambda: 1)
    disp.register("b", lambda: 2)
    names = disp.list_functions()
    assert set(names) == {"a", "b"}


def test_clear():
    """clear removes all registered functions."""
    disp = FunctionDispatcher()
    disp.register("a", lambda: 1)
    disp.register("b", lambda: 2)
    disp.clear()
    assert disp.list_functions() == []


def test_dispatch_with_exception():
    """Dispatch catches exceptions and returns None."""
    disp = FunctionDispatcher()
    disp.register("bad", lambda: 1 / 0)
    result = disp.dispatch("bad", {})
    assert result is None
