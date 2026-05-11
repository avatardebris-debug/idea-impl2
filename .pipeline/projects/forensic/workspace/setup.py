"""Setup script for Forensic Suite."""

from setuptools import setup, find_packages

setup(
    name="forensic-suite",
    version="0.1.0",
    author="Forensic Suite",
    description="SEC Filing Analysis and Fraud Detection",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.9",
    install_requires=[
        "flask>=2.0.0",
        "requests>=2.25.0",
        "pandas>=1.3.0",
        "numpy>=1.21.0",
        "scikit-learn>=0.24.0",
        "matplotlib>=3.4.0",
        "plotly>=5.0.0",
        "beautifulsoup4>=4.9.0",
        "lxml>=4.6.0",
        "tqdm>=4.60.0",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.0.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.900",
        ],
    },
    entry_points={
        "console_scripts": [
            "forensic=forensic.__main__:main",
        ],
    },
)
