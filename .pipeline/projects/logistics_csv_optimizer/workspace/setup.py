from setuptools import setup, find_packages

setup(
    name="logistics_csv_optimizer",
    version="0.1.0",
    description="CLI tool for importing shipment manifests, calculating routing costs, "
                "and generating optimized delivery schedules.",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=7.0"],
    },
    entry_points={
        "console_scripts": [
            "logistics_csv_optimizer=logistics_csv_optimizer.cli:main",
        ],
    },
)
