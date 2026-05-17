"""Task type detection — heuristic-based classifier for video content."""

import os
from pathlib import Path


# Keyword-to-task-type mappings
_KEYWORD_MAP = {
    "cooking": [
        "cook", "recipe", "food", "kitchen", "ingredient", "chop", "stir",
        "bake", "boil", "fry", "grill", "oven", "mix", "season", "plate",
        "dish", "meal", "eat", "taste", "spice", "herb", "sauce", "soup",
        "salad", "bread", "cake", "pizza", "pasta", "rice", "meat", "fish",
        "vegetable", "fruit", "dessert", "breakfast", "lunch", "dinner",
        "dining", "culinary", "gourmet", "chef", "nutrition", "diet",
    ],
    "repair": [
        "fix", "repair", "tool", "wrench", "screw", "drill", "hammer",
        "mechanic", "engine", "motor", "part", "replace", "assemble",
        "disassemble", "install", "remove", "tighten", "loosen", "adjust",
        "diagnose", "troubleshoot", "maintenance", "workshop", "garage",
        "hardware", "plumbing", "electrical", "carpentry", "welding",
        "solder", "pipe", "wire", "circuit", "component",
    ],
    "craft": [
        "craft", "art", "paint", "draw", "sculpt", "carve", "knit", "sew",
        "weave", "pottery", "ceramic", "wood", "paper", "glue", "cut",
        "fold", "design", "create", "decorate", "pattern", "texture",
        "color", "canvas", "brush", "clay", "thread", "fabric", "textile",
        "origami", "embroidery", "crochet", "beading", "jewelry", "mural",
        "sculpture", "installation", "mixed media", "collage",
    ],
    "fitness": [
        "exercise", "workout", "gym", "fitness", "train", "run", "walk",
        "stretch", "yoga", "pilates", "cardio", "strength", "muscle",
        "weight", "rep", "set", "warmup", "cooldown", "stretch", "flexibility",
        "endurance", "agility", "balance", "core", "abs", "legs", "arms",
        "chest", "back", "shoulder", "squat", "lunge", "pushup", "plank",
        "meditation", "breathing", "wellness", "health",
    ],
    "diy": [
        "diy", "build", "make", "project", "hack", "improve", "upgrade",
        "renovate", "remodel", "transform", "convert", "customize", "personalize",
        "repurpose", "upcycle", "restore", "refurbish", "furniture", "shelf",
        "table", "desk", "cabinet", "drawer", "door", "wall", "floor",
        "ceiling", "lighting", "decor", "home improvement", "renovation",
    ],
    "gardening": [
        "garden", "plant", "grow", "soil", "seed", "water", "prune", "trim",
        "harvest", "compost", "fertilize", "mulch", "flower", "tree", "bush",
        "shrub", "lawn", "grass", "weed", "pest", "organic", "greenhouse",
        "hydroponic", "vertical", "container", "pot", "bed", "plot", "farm",
        "botanical", "horticulture", "landscape", "irrigation",
    ],
    "technology": [
        "code", "program", "software", "hardware", "computer", "laptop",
        "phone", "smartphone", "tablet", "device", "app", "website", "web",
        "internet", "network", "server", "database", "api", "cloud", "data",
        "algorithm", "debug", "compile", "deploy", "version", "git", "python",
        "javascript", "react", "node", "docker", "kubernetes", "linux", "windows",
        "macos", "android", "ios", "tech", "digital", "automation", "robot",
        "ai", "machine learning", "deep learning", "neural", "sensor", "drone",
    ],
    "beauty": [
        "beauty", "makeup", "skincare", "hair", "nail", "cosmetic", "cream",
        "lotion", "serum", "mask", "spa", "massage", "facial", "moisturizer",
        "foundation", "concealer", "blush", "eyeshadow", "mascara", "lipstick",
        "contour", "highlight", "bronzer", "primer", "toner", "cleanser",
        "exfoliate", "shampoo", "conditioner", "styling", "curl", "straighten",
        "dye", "bleach", "manicure", "pedicure", "gel", "acrylic",
    ],
    "music": [
        "music", "song", "guitar", "piano", "drum", "bass", "violin", "flute",
        "trumpet", "saxophone", "voice", "singing", "vocal", "chord", "scale",
        "melody", "rhythm", "beat", "tempo", "note", "lyric", "album", "track",
        "mix", "record", "studio", "amplifier", "speaker", "microphone", "headphone",
        "instrument", "band", "orchestra", "choir", "concert", "performance",
        "composition", "arrangement", "harmony", "jazz", "rock", "pop", "classical",
        "blues", "country", "hip hop", "rap", "electronic", "ambient",
    ],
    "travel": [
        "travel", "trip", "tour", "visit", "explore", "destination", "hotel",
        "flight", "train", "bus", "car", "drive", "hike", "camp", "beach",
        "mountain", "city", "country", "culture", "food", "local", "adventure",
        "backpack", "luggage", "passport", "visa", "itinerary", "guide",
        "landmark", "museum", "gallery", "park", "street", "market", "restaurant",
        "cuisine", "souvenir", "photography", "sightseeing", "journey", "voyage",
    ],
    "education": [
        "learn", "teach", "class", "lesson", "course", "tutorial", "lecture",
        "study", "exam", "test", "homework", "assignment", "project", "research",
        "university", "college", "school", "student", "teacher", "professor",
        "book", "textbook", "note", "notebook", "pen", "pencil", "paper",
        "whiteboard", "blackboard", "presentation", "slide", "quiz", "grade",
        "degree", "diploma", "certificate", "training", "workshop", "seminar",
        "webinar", "online", "distance", "e-learning", "mooc",
    ],
}


def detect_task_type(filename: str) -> str | None:
    """Detect task type from filename or content keywords.

    Args:
        filename: Filename string to analyze.

    Returns:
        Detected task type string, or None if no match.
    """
    filename_lower = filename.lower()

    # Check each task type's keywords against the filename
    for task_type, keywords in _KEYWORD_MAP.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return task_type

    return None


def detect_task_type_from_content(content: str) -> str | None:
    """Detect task type from text content (e.g., transcript).

    Args:
        content: Text content to analyze.

    Returns:
        Detected task type string, or None if no match.
    """
    content_lower = content.lower()

    for task_type, keywords in _KEYWORD_MAP.items():
        for keyword in keywords:
            if keyword in content_lower:
                return task_type

    return None
