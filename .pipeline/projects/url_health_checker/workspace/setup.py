from setuptools import setup, find_packages

setup(
    name="url_health_checker",
    version="0.1.0",
    description="A CLI tool to check the health of URLs.",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "url-health-checker=url_health_checker.cli:main",
        ],
    },
)
