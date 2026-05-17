from setuptools import setup, find_packages

setup(
    name="babble",
    version="0.1.0",
    description="Duolingo-style language learning with memory palace techniques",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "babble=babble.cli:main",
        ],
    },
)
