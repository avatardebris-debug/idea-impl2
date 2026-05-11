from setuptools import setup, find_packages

setup(
    name="movieseries-tracker",
    version="0.1.0",
    description="Movie/Series auto-tracker: search streaming platforms, manage watchlist, and continue watching.",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "movieseries-tracker=movieseries_tracker.cli:main",
        ],
    },
)
