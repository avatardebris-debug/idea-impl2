"""Sample Python module for end-to-end testing."""


def greet(name: str) -> str:
    """Greet a person by name.

    Args:
        name: The person's name.

    Returns:
        A greeting string.
    """
    return f"Hello, {name}!"


class Calculator:
    """A simple calculator class."""

    def __init__(self, initial_value: float = 0) -> None:
        """Initialize the calculator with an optional starting value.

        Args:
            initial_value: The initial value for the calculator.
        """
        self.value = initial_value

    def add(self, number: float) -> float:
        """Add a number to the current value.

        Args:
            number: The number to add.

        Returns:
            The new value after addition.
        """
        self.value += number
        return self.value

    def multiply(self, factor: float) -> float:
        """Multiply the current value by a factor.

        Args:
            factor: The multiplication factor.

        Returns:
            The new value after multiplication.
        """
        self.value *= factor
        return self.value


def compute_sum(numbers: list) -> float:
    """Compute the sum of a list of numbers.

    Args:
        numbers: A list of numeric values.

    Returns:
        The sum of all numbers.
    """
    return sum(numbers)
