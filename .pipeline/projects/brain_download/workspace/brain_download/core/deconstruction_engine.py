"""Deconstruction engine — breaks any topic into a hierarchical skill tree."""

from __future__ import annotations

import random
from typing import Any

from brain_download.config.domain_profiles import get_domain_profile
from brain_download.config.learning_models import DESSCConfig, get_dessc_config
from brain_download.core.models import SkillNode, SkillTree, Topic


# ── Built-in deconstruction knowledge (deterministic fallback) ──────────────

_TOPIC_KNOWLEDGE: dict[str, list[dict[str, Any]]] = {
    "python": [
        {"name": "Python Syntax & Basics", "level": 1, "importance": 0.95, "minutes": 45, "tags": ["syntax", "basics"]},
        {"name": "Variables & Data Types", "level": 1, "importance": 0.92, "minutes": 30, "tags": ["syntax", "types"]},
        {"name": "Control Flow (if/else, loops)", "level": 1, "importance": 0.90, "minutes": 40, "tags": ["control", "flow"]},
        {"name": "Functions & Scope", "level": 2, "importance": 0.88, "minutes": 50, "tags": ["functions", "scope"]},
        {"name": "Data Structures (lists, dicts, sets)", "level": 2, "importance": 0.93, "minutes": 60, "tags": ["data", "structures"]},
        {"name": "File I/O & Path Handling", "level": 2, "importance": 0.70, "minutes": 30, "tags": ["io", "files"]},
        {"name": "Error Handling & Exceptions", "level": 2, "importance": 0.80, "minutes": 35, "tags": ["errors", "exceptions"]},
        {"name": "Modules & Packages", "level": 2, "importance": 0.75, "minutes": 40, "tags": ["modules", "packages"]},
        {"name": "Object-Oriented Programming", "level": 3, "importance": 0.85, "minutes": 70, "tags": ["oop", "classes"]},
        {"name": "List Comprehensions & Generators", "level": 3, "importance": 0.78, "minutes": 35, "tags": ["comprehensions", "generators"]},
        {"name": "Decorators & Metaprogramming", "level": 3, "importance": 0.60, "minutes": 45, "tags": ["decorators", "meta"]},
        {"name": "Virtual Environments & pip", "level": 2, "importance": 0.72, "minutes": 25, "tags": ["env", "pip"]},
        {"name": "Testing with pytest", "level": 3, "importance": 0.76, "minutes": 50, "tags": ["testing", "pytest"]},
        {"name": "Standard Library Essentials", "level": 2, "importance": 0.68, "minutes": 40, "tags": ["stdlib", "essentials"]},
        {"name": "Debugging Techniques", "level": 3, "importance": 0.74, "minutes": 35, "tags": ["debugging", "tools"]},
        {"name": "Type Hints & Mypy", "level": 3, "importance": 0.55, "minutes": 30, "tags": ["typing", "mypy"]},
        {"name": "Async Programming", "level": 3, "importance": 0.50, "minutes": 55, "tags": ["async", "concurrency"]},
        {"name": "Web Frameworks (Flask/FastAPI)", "level": 3, "importance": 0.45, "minutes": 60, "tags": ["web", "frameworks"]},
    ],
    "data science": [
        {"name": "NumPy Fundamentals", "level": 1, "importance": 0.97, "minutes": 60, "tags": ["numpy", "arrays"]},
        {"name": "Pandas DataFrames", "level": 1, "importance": 0.96, "minutes": 70, "tags": ["pandas", "dataframes"]},
        {"name": "Data Cleaning & Preprocessing", "level": 2, "importance": 0.94, "minutes": 65, "tags": ["cleaning", "preprocessing"]},
        {"name": "Exploratory Data Analysis", "level": 2, "importance": 0.90, "minutes": 55, "tags": ["eda", "analysis"]},
        {"name": "Matplotlib & Seaborn Visualization", "level": 2, "importance": 0.88, "minutes": 60, "tags": ["visualization", "plotting"]},
        {"name": "Statistical Foundations", "level": 2, "importance": 0.85, "minutes": 50, "tags": ["statistics", "probability"]},
        {"name": "Feature Engineering", "level": 3, "importance": 0.82, "minutes": 55, "tags": ["features", "engineering"]},
        {"name": "Scikit-learn Basics", "level": 2, "importance": 0.91, "minutes": 65, "tags": ["sklearn", "ml-basics"]},
        {"name": "Supervised Learning (Regression)", "level": 3, "importance": 0.80, "minutes": 60, "tags": ["regression", "supervised"]},
        {"name": "Supervised Learning (Classification)", "level": 3, "importance": 0.82, "minutes": 65, "tags": ["classification", "supervised"]},
        {"name": "Model Evaluation & Validation", "level": 3, "importance": 0.84, "minutes": 50, "tags": ["evaluation", "validation"]},
        {"name": "Unsupervised Learning", "level": 3, "importance": 0.65, "minutes": 55, "tags": ["unsupervised", "clustering"]},
        {"name": "Feature Selection & Dimensionality Reduction", "level": 3, "importance": 0.60, "minutes": 45, "tags": ["selection", "reduction"]},
        {"name": "Pipelines & Cross-Validation", "level": 3, "importance": 0.70, "minutes": 40, "tags": ["pipelines", "cv"]},
        {"name": "Hyperparameter Tuning", "level": 3, "importance": 0.68, "minutes": 50, "tags": ["hyperparams", "tuning"]},
        {"name": "Model Deployment Basics", "level": 3, "importance": 0.55, "minutes": 45, "tags": ["deployment", "production"]},
        {"name": "Deep Learning Intro (TensorFlow/PyTorch)", "level": 3, "importance": 0.50, "minutes": 70, "tags": ["deep-learning", "neural-nets"]},
        {"name": "NLP Fundamentals", "level": 3, "importance": 0.45, "minutes": 55, "tags": ["nlp", "text"]},
    ],
    "web development": [
        {"name": "HTML5 Structure & Semantics", "level": 1, "importance": 0.95, "minutes": 45, "tags": ["html", "structure"]},
        {"name": "CSS3 Styling & Layout", "level": 1, "importance": 0.93, "minutes": 60, "tags": ["css", "layout"]},
        {"name": "JavaScript Fundamentals", "level": 1, "importance": 0.96, "minutes": 70, "tags": ["js", "basics"]},
        {"name": "DOM Manipulation", "level": 2, "importance": 0.88, "minutes": 50, "tags": ["dom", "manipulation"]},
        {"name": "Responsive Design & Media Queries", "level": 2, "importance": 0.85, "minutes": 45, "tags": ["responsive", "media"]},
        {"name": "CSS Frameworks (Tailwind/Bootstrap)", "level": 2, "importance": 0.72, "minutes": 50, "tags": ["frameworks", "css"]},
        {"name": "JavaScript ES6+ Features", "level": 2, "importance": 0.90, "minutes": 55, "tags": ["es6", "modern-js"]},
        {"name": "Async JavaScript (Promises, async/await)", "level": 2, "importance": 0.82, "minutes": 45, "tags": ["async", "promises"]},
        {"name": "REST API Design & Consumption", "level": 3, "importance": 0.80, "minutes": 50, "tags": ["api", "rest"]},
        {"name": "Frontend Frameworks (React/Vue)", "level": 3, "importance": 0.78, "minutes": 80, "tags": ["react", "vue"]},
        {"name": "State Management", "level": 3, "importance": 0.65, "minutes": 45, "tags": ["state", "management"]},
        {"name": "Build Tools & Bundlers", "level": 3, "importance": 0.60, "minutes": 40, "tags": ["build", "bundlers"]},
        {"name": "Version Control with Git", "level": 2, "importance": 0.85, "minutes": 35, "tags": ["git", "vcs"]},
        {"name": "Testing (Jest, Cypress)", "level": 3, "importance": 0.68, "minutes": 50, "tags": ["testing", "jest"]},
        {"name": "Performance Optimization", "level": 3, "importance": 0.55, "minutes": 40, "tags": ["performance", "optimization"]},
        {"name": "Security Best Practices", "level": 3, "importance": 0.70, "minutes": 45, "tags": ["security", "best-practices"]},
        {"name": "Deployment & CI/CD", "level": 3, "importance": 0.58, "minutes": 50, "tags": ["deployment", "cicd"]},
        {"name": "TypeScript Fundamentals", "level": 3, "importance": 0.62, "minutes": 55, "tags": ["typescript", "types"]},
    ],
    "machine learning": [
        {"name": "Math Foundations (Linear Algebra, Calculus)", "level": 1, "importance": 0.85, "minutes": 70, "tags": ["math", "foundations"]},
        {"name": "Probability & Statistics", "level": 1, "importance": 0.88, "minutes": 60, "tags": ["probability", "stats"]},
        {"name": "Python for ML (NumPy, Pandas)", "level": 1, "importance": 0.92, "minutes": 65, "tags": ["python", "numpy"]},
        {"name": "Data Preprocessing & Feature Engineering", "level": 2, "importance": 0.90, "minutes": 55, "tags": ["preprocessing", "features"]},
        {"name": "Supervised Learning: Regression", "level": 2, "importance": 0.88, "minutes": 60, "tags": ["regression", "supervised"]},
        {"name": "Supervised Learning: Classification", "level": 2, "importance": 0.90, "minutes": 65, "tags": ["classification", "supervised"]},
        {"name": "Model Evaluation Metrics", "level": 2, "importance": 0.85, "minutes": 45, "tags": ["evaluation", "metrics"]},
        {"name": "Cross-Validation & Bias-Variance", "level": 2, "importance": 0.80, "minutes": 40, "tags": ["cv", "bias-variance"]},
        {"name": "Ensemble Methods (RF, GBM, XGBoost)", "level": 3, "importance": 0.78, "minutes": 55, "tags": ["ensembles", "boosting"]},
        {"name": "Unsupervised Learning (Clustering, PCA)", "level": 3, "importance": 0.70, "minutes": 50, "tags": ["unsupervised", "clustering"]},
        {"name": "Feature Selection & Dimensionality Reduction", "level": 3, "importance": 0.68, "minutes": 45, "tags": ["selection", "reduction"]},
        {"name": "Hyperparameter Optimization", "level": 3, "importance": 0.72, "minutes": 50, "tags": ["hyperparams", "optimization"]},
        {"name": "Deep Learning Fundamentals", "level": 3, "importance": 0.75, "minutes": 70, "tags": ["deep-learning", "nn"]},
        {"name": "Neural Network Architectures (CNN, RNN)", "level": 3, "importance": 0.65, "minutes": 65, "tags": ["cnn", "rnn"]},
        {"name": "Transfer Learning & Fine-tuning", "level": 3, "importance": 0.58, "minutes": 50, "tags": ["transfer", "fine-tuning"]},
        {"name": "MLOps & Model Deployment", "level": 3, "importance": 0.55, "minutes": 45, "tags": ["mlops", "deployment"]},
        {"name": "Ethics & Fairness in ML", "level": 3, "importance": 0.50, "minutes": 35, "tags": ["ethics", "fairness"]},
        {"name": "Time Series Analysis", "level": 3, "importance": 0.48, "minutes": 50, "tags": ["timeseries", "forecasting"]},
    ],
    "general": [
        {"name": "Foundational Concepts", "level": 1, "importance": 0.95, "minutes": 60, "tags": ["foundations", "basics"]},
        {"name": "Core Terminology & Vocabulary", "level": 1, "importance": 0.90, "minutes": 40, "tags": ["terminology", "vocab"]},
        {"name": "Key Principles & Frameworks", "level": 1, "importance": 0.88, "minutes": 50, "tags": ["principles", "frameworks"]},
        {"name": "Tools & Technologies", "level": 2, "importance": 0.85, "minutes": 55, "tags": ["tools", "tech"]},
        {"name": "Practical Applications", "level": 2, "importance": 0.82, "minutes": 60, "tags": ["practical", "applications"]},
        {"name": "Common Patterns & Best Practices", "level": 2, "importance": 0.80, "minutes": 45, "tags": ["patterns", "best-practices"]},
        {"name": "Intermediate Techniques", "level": 2, "importance": 0.78, "minutes": 50, "tags": ["intermediate", "techniques"]},
        {"name": "Problem-Solving Strategies", "level": 2, "importance": 0.75, "minutes": 40, "tags": ["problem-solving", "strategies"]},
        {"name": "Advanced Methodologies", "level": 3, "importance": 0.70, "minutes": 55, "tags": ["advanced", "methodologies"]},
        {"name": "Integration & Workflow", "level": 3, "importance": 0.68, "minutes": 45, "tags": ["integration", "workflow"]},
        {"name": "Performance Optimization", "level": 3, "importance": 0.65, "minutes": 40, "tags": ["performance", "optimization"]},
        {"name": "Troubleshooting & Debugging", "level": 3, "importance": 0.62, "minutes": 35, "tags": ["troubleshooting", "debugging"]},
        {"name": "Community & Resources", "level": 3, "importance": 0.55, "minutes": 30, "tags": ["community", "resources"]},
        {"name": "Certification & Career Paths", "level": 3, "importance": 0.50, "minutes": 25, "tags": ["career", "certification"]},
        {"name": "Future Trends & Emerging Topics", "level": 3, "importance": 0.45, "minutes": 30, "tags": ["trends", "emerging"]},
    ],
}


def _detect_domain(topic_name: str) -> str:
    """Detect the domain from the topic name."""
    lower = topic_name.lower()
    for domain in ["python", "data science", "web development", "machine learning"]:
        if domain in lower:
            return domain
    return "general"


def _build_skill_nodes(
    topic: Topic,
    domain: str,
    config: DESSCConfig,
) -> list[SkillNode]:
    """Build skill nodes from knowledge base + domain profile overrides."""
    # Get base knowledge
    base_knowledge = _TOPIC_KNOWLEDGE.get(domain, _TOPIC_KNOWLEDGE["general"])

    # Get domain profile overrides
    profile = get_domain_profile(domain)
    overrides = profile.get("emphasis", {})
    deconstruction_hints = profile.get("deconstruction_hints", {})

    nodes: list[SkillNode] = []
    node_id = 0

    for idx, skill_info in enumerate(base_knowledge):
        name = skill_info["name"]
        level = skill_info["level"]
        importance = skill_info["importance"]
        minutes = skill_info["minutes"]
        tags = skill_info.get("tags", [])

        # Apply domain emphasis overrides
        if domain in overrides:
            for emphasis_skill, emphasis_boost in overrides[domain].items():
                if emphasis_skill.lower() in name.lower():
                    importance = min(1.0, importance + emphasis_boost)

        # Apply deconstruction hints
        if name in deconstruction_hints:
            hint = deconstruction_hints[name]
            if "importance_override" in hint:
                importance = hint["importance_override"]
            if "level_override" in hint:
                level = hint["level_override"]
            if "minutes_override" in hint:
                minutes = hint["minutes_override"]

        # Add domain-specific tags
        if domain != "general":
            tags = list(set(tags + [domain]))

        node = SkillNode(
            id=f"skill_{node_id:03d}",
            name=name,
            description=f"Master {name} for {topic.name}",
            importance=round(importance, 2),
            level=level,
            estimated_minutes=minutes,
            tags=tags,
        )
        nodes.append(node)
        node_id += 1

    # If we have fewer than 15 nodes, add generic ones
    generic_skills = [
        {"name": "Practical Project: Build Something Real", "level": 3, "importance": 0.90, "minutes": 90, "tags": ["project", "practice"]},
        {"name": "Code Review & Feedback Loops", "level": 3, "importance": 0.70, "minutes": 30, "tags": ["review", "feedback"]},
        {"name": "Documentation & Knowledge Sharing", "level": 3, "importance": 0.60, "minutes": 25, "tags": ["docs", "sharing"]},
        {"name": "Peer Learning & Study Groups", "level": 3, "importance": 0.55, "minutes": 40, "tags": ["peer", "group"]},
        {"name": "Self-Assessment & Progress Tracking", "level": 3, "importance": 0.65, "minutes": 20, "tags": ["assessment", "tracking"]},
    ]
    for skill_info in generic_skills:
        if len(nodes) >= 25:
            break
        node = SkillNode(
            id=f"skill_{node_id:03d}",
            name=skill_info["name"],
            description=f"Develop {skill_info['name']} skills",
            importance=skill_info["importance"],
            level=skill_info["level"],
            estimated_minutes=skill_info["minutes"],
            tags=skill_info["tags"],
        )
        nodes.append(node)
        node_id += 1

    # Set prerequisites based on level
    for node in nodes:
        if node.level == 2:
            # Prerequisites: any level-1 node
            prereqs = [n.id for n in nodes if n.level == 1]
            node.prerequisites = prereqs[:3]  # top 3 level-1 prereqs
        elif node.level == 3:
            # Prerequisites: some level-2 nodes
            level2_nodes = [n for n in nodes if n.level == 2]
            node.prerequisites = [n.id for n in level2_nodes[:3]]

    return nodes


def deconstruct_topic(
    topic_name: str,
    domain: str | None = None,
    config: DESSCConfig | None = None,
    topic_description: str = "",
    target_audience: str = "beginner",
    desired_outcome: str = "",
) -> SkillTree:
    """Deconstruct a topic into a hierarchical skill tree.

    Uses the DESSC framework:
    - Deconstruction: Break topic into skill components
    - Selection: Apply Pareto filtering (handled by selection_matrix)
    - Sequencing: Order by prerequisites (handled by sequencing_engine)

    Args:
        topic_name: The name of the topic to deconstruct.
        domain: Optional domain override (e.g., 'python', 'data science').
        config: DESSC configuration. Defaults to get_dessc_config().
        topic_description: Optional description of the topic.
        target_audience: Target audience level.
        desired_outcome: Desired learning outcome.

    Returns:
        A SkillTree with root_nodes and all_nodes populated.
    """
    if config is None:
        config = get_dessc_config()

    if domain is None:
        domain = _detect_domain(topic_name)

    topic = Topic(
        name=topic_name,
        domain=domain,
        description=topic_description,
        target_audience=target_audience,
        desired_outcome=desired_outcome,
    )

    all_nodes = _build_skill_nodes(topic, domain, config)

    # Identify root nodes (level 1)
    root_nodes = [n for n in all_nodes if n.level == 1]

    # Ensure at least 15 nodes across 3+ levels
    assert len(all_nodes) >= 15, f"Expected at least 15 nodes, got {len(all_nodes)}"
    levels = {n.level for n in all_nodes}
    assert len(levels) >= 3, f"Expected at least 3 levels, got {levels}"

    tree = SkillTree(
        topic=topic,
        root_nodes=root_nodes,
        all_nodes=all_nodes,
        metadata={
            "domain": domain,
            "total_skills": len(all_nodes),
            "deconstruction_method": "knowledge_base_with_domain_profile",
            "config_version": config.version,
        },
    )

    return tree
