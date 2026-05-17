"""Setup script for dfs_arb package."""

from setuptools import setup, find_packages

setup(
    name="dfs_arb",
    version="0.1.0",
    description="Daily Fantasy Sports Arbitrage and Mispriced Lines Detector",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0",
    ],
    entry_points={
        "console_scripts": [
            "dfs-arb=dfs_arb.cli:main",
        ],
    },
)
