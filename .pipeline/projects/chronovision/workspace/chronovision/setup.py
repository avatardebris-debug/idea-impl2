from setuptools import setup, find_packages

setup(
    name="chronovision",
    version="0.1.0",
    description="Financial World Model",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        "numpy>=1.21.0",
        "torch>=1.9.0",
        "scikit-learn>=0.24.0",
        "pandas>=1.3.0",
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "lxml>=4.6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "chronovision=chronovision.src.cli:main",
        ],
    },
)
