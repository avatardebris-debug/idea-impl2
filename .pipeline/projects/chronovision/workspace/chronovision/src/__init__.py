"""Chronovision — Financial World Model.

Chronovision builds a dynamic state-space representation of the financial world,
propagates states through a graph of entities, and uses ML to predict future movements.

Usage:
    python -m chronovision run --tickers AAPL MSFT GOOGL
    python -m chronovision predict --ticker AAPL
    python -m chronovision status
"""

__version__ = "0.1.0"
