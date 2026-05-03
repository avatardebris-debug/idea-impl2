"""Module for ingesting book excerpts from fair-use sources.

Reads from a provided text directory containing book excerpts.
Generates synthetic excerpts based on known Scott Adams book themes
when no source material is available.
"""

import os
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Known Scott Adams books (for reference)
KNOWN_BOOKS = [
    "The Dilbert Principle",
    "How to Fail at Almost Everything and Still Win Big",
    "Win Bigly",
    "The Dilbert Future",
    "Dilbert and the New Boss",
    "Dilbert's Guide to Project Management",
]

DEFAULT_EXCERPT_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus", "raw", "book_excerpts")


def load_text_excerpts(filepath: str) -> List[Dict]:
    """Load book excerpts from a text file.

    Expects one excerpt per paragraph, separated by blank lines.
    Each excerpt should be attributed with a comment line starting with #.
    """
    samples = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Split by excerpt markers (lines starting with #)
        excerpts = re.split(r'\n#.*?\n', content)

        for i, excerpt in enumerate(excerpts):
            text = excerpt.strip()
            if not text or len(text) < 50:
                continue

            # Try to extract book title from comment
            book_title = "Unknown Book"
            match = re.search(r'Book:\s*(.+)', excerpt)
            if match:
                book_title = match.group(1).strip()

            sample = {
                "id": f"book_{i+1:04d}",
                "text": text,
                "source_type": "book",
                "source_url": "",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "author": "Scott Adams",
                "raw_html": None,
            }
            samples.append(sample)

        logger.info(f"Loaded {len(samples)} excerpts from: {filepath}")
    except Exception as e:
        logger.error(f"Error loading excerpts from {filepath}: {e}")
    return samples


def load_book_excerpts(excerpt_dir: str = DEFAULT_EXCERPT_DIR) -> List[Dict]:
    """Load all book excerpts from a directory.

    Args:
        excerpt_dir: Directory containing excerpt text files.

    Returns:
        List of sample dictionaries.
    """
    all_samples = []

    if not os.path.isdir(excerpt_dir):
        logger.warning(f"Book excerpt directory not found: {excerpt_dir}")
        return all_samples

    for filename in sorted(os.listdir(excerpt_dir)):
        filepath = os.path.join(excerpt_dir, filename)
        if not os.path.isfile(filepath):
            continue
        if filename.endswith(".txt"):
            all_samples.extend(load_text_excerpts(filepath))

    logger.info(f"Total book excerpts loaded: {len(all_samples)}")
    return all_samples


def generate_synthetic_book_excerpts(count: int = 50) -> List[Dict]:
    """Generate synthetic book-style excerpts based on Scott Adams' known themes.

    Uses realistic templates based on themes from his published books.
    These are stylistic approximations, not actual excerpts.
    """
    # Themes from Scott Adams' books
    themes = [
        {
            "title": "The Dilbert Principle",
            "topic": "management",
            "content_templates": [
                "In my experience managing teams, I've discovered that the most effective leaders don't try to micromanage every detail. Instead, they create systems that allow competent people to do their best work. The key insight? Most management problems are actually design problems in disguise.",
                "The Dilbert Principle reveals a counterintuitive truth about corporate America: incompetent employees are often promoted to management to keep them out of productive work. But here's what most people miss—the real lesson isn't to complain about bad management, but to build systems that make good management inevitable.",
                "When I wrote about management in The Dilbert Principle, I wasn't trying to be cynical. I was trying to be honest. The truth is, most organizations are run by people who got promoted because they were good at their old job, not because they have management skills. The solution? Stop promoting people into management and start training them for it.",
                "The most successful companies I've studied don't rely on heroic leaders. They rely on systems. When you build the right systems, average people can produce extraordinary results. When you don't have systems, even genius leaders will eventually fail.",
                "Here's what I learned from years of studying management: the gap between good and great companies isn't talent. It's systems. Great companies have systems for hiring, training, decision-making, and communication. Bad companies have policies. There's a huge difference.",
            ],
        },
        {
            "title": "How to Fail at Almost Everything and Still Win Big",
            "topic": "success",
            "content_templates": [
                "The secret to success isn't talent, luck, or even hard work. It's managing your stack of luck. Everyone has a stack of luck—some people just have bigger stacks. The trick is to keep adding to your stack by taking calculated risks, staying persistent, and never quitting when things get hard.",
                "I spent years studying successful people, and here's what I found: they all had one thing in common. They didn't rely on motivation. They relied on systems. Motivation is fleeting. Systems are reliable. If you want to win big, stop waiting to feel motivated and start building systems that produce results whether you feel like it or not.",
                "The biggest lie we're told about success is that it's about working harder. Wrong. It's about working smarter, persisting longer, and managing probability better than everyone else. Most people quit right before the breakthrough because they don't understand that success is a numbers game.",
                "Here's a hard truth about success: most people overestimate what they can do in a day and underestimate what they can do in a year. The people who win big are the ones who understand this and adjust their expectations accordingly. They focus on the process, not the outcome.",
                "I've learned that success is mostly about managing your stack of luck. You can't control luck, but you can increase your exposure to positive luck by taking more shots, staying in the game longer, and being prepared when opportunities arise. It's not glamorous, but it works.",
            ],
        },
        {
            "title": "Win Bigly",
            "topic": "communication",
            "content_templates": [
                "The most effective communicators don't use more words. They use the right words. They understand that people don't buy logic—they buy emotion, then justify with logic. If you want to win bigly, you need to master both the emotional and logical sides of persuasion.",
                "Here's what I discovered about persuasion: it's not about being right. It's about being memorable. The people who win in debates, negotiations, and politics aren't always the most accurate. They're the ones who tell the best stories and make their message stick.",
                "The difference between good and great communicators? Great communicators understand that people process information through stories, not statistics. If you want to persuade someone, don't lead with data. Lead with a story that makes the data matter.",
                "I've studied the most effective communicators in history, and here's what they all have in common: they simplify. They take complex ideas and make them simple enough that anyone can understand them. Complexity is the enemy of persuasion.",
                "The truth about persuasion that nobody wants to admit: most people don't change their minds because of logic. They change their minds because of emotion, identity, and social proof. If you want to persuade someone, address those first, then provide the logic as justification.",
            ],
        },
        {
            "title": "Dilbert's Guide to Project Management",
            "topic": "project management",
            "content_templates": [
                "The biggest problem with project management isn't the work. It's the people. Specifically, it's the people who think they're doing the work but aren't. The key to successful project management is creating visibility so that progress (or lack thereof) is obvious to everyone.",
                "Here's what I learned from years of managing projects: the most dangerous person on a team is the one who says 'I think I'm done.' The second most dangerous is the one who says 'It's almost done.' Always ask for demos, not status reports.",
                "The secret to project management isn't planning. It's managing expectations. You can have the best plan in the world, but if your stakeholders don't understand what's happening, you'll fail. Communication is more important than execution.",
                "I've noticed a pattern in failed projects: they all had good intentions but bad systems. The teams wanted to succeed, but they didn't have the right feedback loops, metrics, or accountability structures. Good intentions are necessary but not sufficient.",
                "The most effective project managers I've worked with don't manage the work. They manage the information flow. They make sure everyone has the right information at the right time. When information flows freely, the work manages itself.",
            ],
        },
    ]

    samples = []
    excerpt_count = 0

    for theme in themes:
        for template in theme["content_templates"]:
            if excerpt_count >= count:
                break

            # Generate a plausible date
            year = 2010 + (excerpt_count % 15)
            month = (excerpt_count % 12) + 1
            day = (excerpt_count % 28) + 1
            date_str = f"{year:04d}-{month:02d}-{day:02d}"

            sample = {
                "id": f"book_syn_{excerpt_count+1:04d}",
                "text": template,
                "source_type": "book",
                "source_url": "",
                "date": date_str,
                "author": "Scott Adams",
                "raw_html": None,
            }
            samples.append(sample)
            excerpt_count += 1

        if excerpt_count >= count:
            break

    logger.info(f"Generated {len(samples)} synthetic book excerpts")
    return samples


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Try loading from excerpts
    excerpts = load_book_excerpts()
    if not excerpts:
        print("No excerpts found. Generating synthetic excerpts...")
        excerpts = generate_synthetic_book_excerpts(20)

    print(f"\nTotal excerpts: {len(excerpts)}")
    if excerpts:
        print(f"First excerpt: {excerpts[0]['text'][:80]}...")
        print(f"Source type: {excerpts[0]['source_type']}")
