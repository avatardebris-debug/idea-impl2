"""Domain-specific profiles for deconstruction hints and emphasis."""

from __future__ import annotations

DOMAIN_PROFILES: dict[str, dict] = {
    "python": {
        "deconstruction_hints": {
            "Python Syntax & Basics": {"importance_override": 1.0, "level_override": 1},
            "Variables & Data Types": {"importance_override": 0.95, "level_override": 1},
            "Functions & Scope": {"importance_override": 0.92, "level_override": 2},
            "Data Structures (lists, dicts, sets)": {"importance_override": 0.95, "level_override": 2},
            "Object-Oriented Programming": {"importance_override": 0.88, "level_override": 3},
            "Testing with pytest": {"importance_override": 0.80, "level_override": 3},
            "Web Frameworks (Flask/FastAPI)": {"importance_override": 0.40, "level_override": 3},
        },
        "emphasis": {
            "python": {
                "Data Structures": 0.05,
                "Functions": 0.03,
                "Testing": 0.05,
            }
        },
        "recommended_tools": ["pytest", "black", "mypy", "pipenv"],
        "learning_path": "syntax → data structures → functions → OOP → testing → projects",
    },
    "data science": {
        "deconstruction_hints": {
            "NumPy Fundamentals": {"importance_override": 1.0, "level_override": 1},
            "Pandas DataFrames": {"importance_override": 1.0, "level_override": 1},
            "Data Cleaning & Preprocessing": {"importance_override": 0.95, "level_override": 2},
            "Exploratory Data Analysis": {"importance_override": 0.92, "level_override": 2},
            "Matplotlib & Seaborn Visualization": {"importance_override": 0.90, "level_override": 2},
            "Scikit-learn Basics": {"importance_override": 0.92, "level_override": 2},
            "Deep Learning Intro": {"importance_override": 0.35, "level_override": 3},
            "NLP Fundamentals": {"importance_override": 0.35, "level_override": 3},
        },
        "emphasis": {
            "data science": {
                "NumPy": 0.05,
                "Pandas": 0.05,
                "Data Cleaning": 0.05,
                "Visualization": 0.03,
            }
        },
        "recommended_tools": ["jupyter", "numpy", "pandas", "matplotlib", "scikit-learn"],
        "learning_path": "numpy → pandas → visualization → statistics → ML → projects",
    },
    "web development": {
        "deconstruction_hints": {
            "HTML5 Structure & Semantics": {"importance_override": 1.0, "level_override": 1},
            "CSS3 Styling & Layout": {"importance_override": 0.95, "level_override": 1},
            "JavaScript Fundamentals": {"importance_override": 1.0, "level_override": 1},
            "DOM Manipulation": {"importance_override": 0.90, "level_override": 2},
            "JavaScript ES6+ Features": {"importance_override": 0.92, "level_override": 2},
            "Frontend Frameworks (React/Vue)": {"importance_override": 0.80, "level_override": 3},
            "TypeScript Fundamentals": {"importance_override": 0.60, "level_override": 3},
        },
        "emphasis": {
            "web development": {
                "HTML": 0.05,
                "CSS": 0.05,
                "JavaScript": 0.05,
                "DOM": 0.03,
            }
        },
        "recommended_tools": ["vscode", "git", "npm", "webpack", "react"],
        "learning_path": "html → css → js → dom → frameworks → projects",
    },
    "machine learning": {
        "deconstruction_hints": {
            "Math Foundations": {"importance_override": 0.90, "level_override": 1},
            "Probability & Statistics": {"importance_override": 0.92, "level_override": 1},
            "Python for ML": {"importance_override": 0.95, "level_override": 1},
            "Supervised Learning: Regression": {"importance_override": 0.90, "level_override": 2},
            "Supervised Learning: Classification": {"importance_override": 0.92, "level_override": 2},
            "Model Evaluation Metrics": {"importance_override": 0.88, "level_override": 2},
            "Deep Learning Fundamentals": {"importance_override": 0.70, "level_override": 3},
            "Ethics & Fairness in ML": {"importance_override": 0.55, "level_override": 3},
        },
        "emphasis": {
            "machine learning": {
                "Math": 0.05,
                "Statistics": 0.05,
                "Supervised Learning": 0.05,
                "Evaluation": 0.03,
            }
        },
        "recommended_tools": ["numpy", "pandas", "scikit-learn", "tensorflow", "pytorch"],
        "learning_path": "math → python → stats → supervised → unsupervised → deep learning → projects",
    },
}


def get_domain_profile(domain: str) -> dict:
    """Get the domain profile for a given domain."""
    return DOMAIN_PROFILES.get(domain, {})
