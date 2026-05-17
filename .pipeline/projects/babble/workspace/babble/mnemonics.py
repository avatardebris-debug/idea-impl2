"""
Mnemonic generation engine for memory palace technique.

Converts phrases into vivid mental images using keyword extraction,
association generation, and location assignment.
"""

import re
import random
from typing import List, Dict, Optional

from babble.models import Phrase


# Common stop words to filter out during keyword extraction
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "shall", "i", "he",
    "she", "it", "we", "they", "me", "him", "her", "us", "them", "my",
    "your", "his", "its", "our", "their", "am", "this", "that", "these",
    "those", "as", "if", "when", "where", "what", "who", "whom",
    "which", "why", "not", "no", "nor", "so", "yet", "both", "either",
    "neither", "each", "every", "all", "any", "few", "more", "most",
    "other", "some", "such", "than", "too", "very", "just", "about",
    "above", "after", "again", "against", "among", "around", "before",
    "below", "between", "into", "through", "during", "until", "up", "down",
    "out", "off", "over", "under", "here", "there", "then", "now", "only",
    "own", "same", "also", "back", "even", "still", "way", "like",
}


def _extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text, filtering out stop words.
    
    Args:
        text: The phrase text to extract keywords from.
        
    Returns:
        List of lowercase keywords, excluding stop words but including numbers.
    """
    if not text or not text.strip():
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation but keep spaces and alphanumeric characters (including accented)
    # Split into words, keeping numbers
    words = re.findall(r'[a-záéíóúñü0-9]+', text)
    
    # Filter out stop words, keep numbers and meaningful words
    keywords = [word for word in words if word not in STOP_WORDS]
    
    return keywords


def _get_keyword_association(keyword: str) -> str:
    """Generate a vivid association for a keyword.
    
    Uses a deterministic approach based on the keyword to generate
    consistent associations.
    
    Args:
        keyword: The keyword to generate an association for.
        
    Returns:
        A vivid association string for the keyword.
    """
    if not keyword:
        keyword = "thing"
    
    # Use a hash-based approach for deterministic but varied associations
    hash_val = sum(ord(c) for c in keyword)
    
    # Predefined association pools
    associations = {
        "action": ["running", "jumping", "throwing", "catching", "kicking", "hitting", "pushing", "pulling"],
        "object": ["giant", "tiny", "glowing", "smoking", "floating", "crushing", "melting", "exploding"],
        "color": ["bright red", "neon green", "deep blue", "golden yellow", "purple", "silver", "black", "white"],
        "sound": ["loud", "silent", "screaming", "whispering", "thundering", "ringing", "buzzing", "crashing"],
        "emotion": ["happy", "scared", "angry", "confused", "excited", "terrified", "joyful", "furious"],
        "size": ["massive", "microscopic", "enormous", "pocket-sized", "towering", "flat", "round", "spiky"],
    }
    
    # Pick a category based on the hash
    category_idx = hash_val % len(list(associations.keys()))
    categories = list(associations.keys())
    category = categories[category_idx]
    
    # Pick an association from the category
    assoc_idx = hash_val % len(associations[category])
    base_assoc = associations[category][assoc_idx]
    
    # Combine with the keyword for a vivid image
    return f"{base_assoc} {keyword}"


def _generate_palace_location(index: int) -> str:
    """Generate a memory palace location for a given index.
    
    Uses a deterministic approach based on the index to generate
    consistent locations.
    
    Args:
        index: The index to generate a location for.
        
    Returns:
        A descriptive location string.
    """
    # Predefined location pools
    rooms = [
        "entrance hall", "living room", "kitchen", "bedroom", "bathroom",
        "study", "library", "attic", "basement", "garden", "balcony",
        "dining room", "hallway", "closet", "garage", "porch", "patio",
        "office", "nursery", "laundry room", "pantry", "cellar",
    ]
    
    specific_locations = [
        "on the floor", "on the ceiling", "in the corner", "under the rug",
        "behind the door", "on the shelf", "in the drawer", "on the table",
        "near the window", "by the fireplace", "under the bed", "on the chair",
        "in the mirror", "behind the painting", "on the mantelpiece", "in the cabinet",
        "on the stairs", "at the top of the stairs", "at the bottom of the stairs",
        "in the doorway", "on the windowsill", "on the bookshelf", "on the desk",
    ]
    
    # Use index to pick a room and specific location
    room_idx = index % len(rooms)
    location_idx = index % len(specific_locations)
    
    # Add some variation based on the index
    modifier_idx = (index // len(rooms)) % 3
    modifiers = ["", "slightly ", "very "]
    
    return f"{modifiers[modifier_idx]}{rooms[room_idx]} {specific_locations[location_idx]}"


def generate_mnemonic(phrase: Phrase) -> str:
    """Generate a mnemonic for a phrase.
    
    Args:
        phrase: The Phrase object to generate a mnemonic for.
        
    Returns:
        A string containing the mnemonic.
    """
    if not phrase.text:
        return "Imagine a mysterious object floating in a dark void"
    
    # Extract keywords
    keywords = _extract_keywords(phrase.text)
    
    if not keywords:
        # If no keywords extracted, use the whole phrase
        keywords = [phrase.text.lower()]
    
    # Generate associations for each keyword
    associations = [_get_keyword_association(kw) for kw in keywords]
    
    # Create a vivid image combining the phrase and associations
    if len(keywords) == 1:
        mnemonic = f"See a {associations[0]} version of '{phrase.text}'"
    else:
        # Create a chain of associations
        parts = []
        for i, (kw, assoc) in enumerate(zip(keywords, associations)):
            if i == 0:
                parts.append(f"See a {assoc} '{kw}'")
            else:
                parts.append(f"which transforms into a {assoc} '{kw}'")
        mnemonic = " ".join(parts)
    
    return mnemonic


def assign_phrase_to_palace(phrase: Phrase) -> Dict:
    """Assign a phrase to a memory palace location and generate a mnemonic.
    
    Args:
        phrase: The Phrase object to assign.
        
    Returns:
        A dictionary containing the mnemonic, location, and phrase.
    """
    # Generate a mnemonic
    mnemonic = generate_mnemonic(phrase)
    
    # Generate a palace location based on the phrase's frequency rank
    # Use frequency_rank as the index for deterministic location assignment
    palace_id = phrase.frequency_rank if phrase.frequency_rank else 0
    location = _generate_palace_location(palace_id)
    
    return {
        "mnemonic": mnemonic,
        "location": location,
        "palace_id": palace_id,
        "phrase": phrase,
        "phrase_text": phrase.text,
        "phrase_language": phrase.language,
    }
