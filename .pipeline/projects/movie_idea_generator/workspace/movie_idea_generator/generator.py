"""Core movie idea generation engine using templates and randomization."""

import random
from typing import Optional


# ── Data pools ────────────────────────────────────────────────────────────────

GENRES = [
    "Action", "Comedy", "Drama", "Horror", "Sci-Fi",
    "Romance", "Thriller", "Fantasy", "Mystery", "Adventure",
]

TITLE_PREFIXES = [
    "The Last", "The Secret", "The Final", "The Hidden", "The Lost",
    "The Eternal", "The Silent", "The Dark", "The Golden", "The Broken",
    "The Forgotten", "The Unseen", "The Wild", "The Crimson", "The Iron",
]

TITLE_NOUNS = [
    "Horizon", "Shadow", "Kingdom", "Legacy", "Promise",
    "Requiem", "Odyssey", "Chronicle", "Prophecy", "Voyage",
    "Enigma", "Mirage", "Sanctuary", "Rebellion", "Covenant",
]

CONFLICTS = [
    "their past", "their identity", "a terrible secret", "the loss of everything",
    "a moral dilemma", "a broken promise", "a painful truth",
]

GENRE_TEMPLATES = {
    "Action": [
        "{prefix} {noun}: A {occupation} must {goal} before {deadline}.",
        "{prefix} {noun}: When {antagonist} threatens the city, a lone {occupation} rises to fight back.",
    ],
    "Comedy": [
        "{prefix} {noun}: A {occupation} accidentally becomes the {role_placeholder} of a {setting}.",
        "{prefix} {noun}: Three {occupations} team up for the most {adjective} plan ever.",
    ],
    "Drama": [
        "{prefix} {noun}: A {occupation} struggles with {conflict} while searching for {goal}.",
        "{prefix} {noun}: After {event}, a {occupation} must choose between {choice_a} and {choice_b}.",
    ],
    "Horror": [
        "{prefix} {noun}: A {occupation} discovers {horror_element} in an abandoned {setting}.",
        "{prefix} {noun}: Every night at midnight, {horror_element} returns to {setting}.",
    ],
    "Sci-Fi": [
        "{prefix} {noun}: In {year}, a {occupation} discovers {sci_fi_element} that changes everything.",
        "{prefix} {noun}: Humanity's last hope lies with a {occupation} who can {goal}.",
    ],
    "Romance": [
        "{prefix} {noun}: Two {occupations} from different worlds find love in the most {adjective} way.",
        "{prefix} {noun}: A {occupation} falls for someone they were sworn to {goal}.",
    ],
    "Thriller": [
        "{prefix} {noun}: A {occupation} uncovers a {adjective} conspiracy that reaches the highest levels.",
        "{prefix} {noun}: With only {deadline}, a {occupation} must {goal} to stop {antagonist}.",
    ],
    "Fantasy": [
        "{prefix} {noun}: A young {occupation} discovers they are the last of a {adjective} bloodline.",
        "{prefix} {noun}: In a world where {fantasy_element}, a {occupation} must {goal}.",
    ],
    "Mystery": [
        "{prefix} {noun}: When {victim} disappears, a {occupation} must solve the {adjective} puzzle.",
        "{prefix} {noun}: Every clue leads deeper into a {adjective} web of lies.",
    ],
    "Adventure": [
        "{prefix} {noun}: A {occupation} embarks on a {adjective} journey across {setting} to find {goal}.",
        "{prefix} {noun}: When {event} destroys everything, a {occupation} must {goal}.",
    ],
}

OCCUPATIONS = [
    "detective", "astronaut", "chef", "teacher", "doctor",
    "journalist", "musician", "soldier", "scientist", "artist",
    "lawyer", "firefighter", "pilot", "nurse", "engineer",
]

ADJECTIVES = [
    "dangerous", "impossible", "crazy", "brilliant", "desperate",
    "unbelievable", "shocking", "heartbreaking", "epic", "twisted",
]

GOALS = [
    "save the world", "find the truth", "stop a killer", "save their family",
    "expose the truth", "find redemption", "stop a war", "save their career",
    "find love", "prevent a disaster", "clear their name", "stop a heist",
]

DEADLINES = [
    "time runs out", "the clock strikes midnight", "the bomb detonates",
    "the eclipse ends", "the deadline passes", "the storm hits",
]

ANTAGONISTS = [
    "a ruthless crime lord", "a rogue AI", "a corrupt politician",
    "a mysterious stranger", "a powerful corporation", "a vengeful spirit",
]

VICTIMS = [
    "the mayor", "a famous scientist", "the last witness",
    "a young girl", "the town's sheriff", "a whistleblower",
]

FANTASY_ELEMENTS = [
    "magic is real", "dragons rule the skies", "the gods have returned",
    "a portal to another world opens", "enchanted forests come alive",
]

SCI_FI_ELEMENTS = [
    "a wormhole to another dimension", "an alien signal from deep space",
    "a time machine that works", "a virus that grants superpowers",
    "a parallel universe where everything is reversed",
]

HORROR_ELEMENTS = [
    "a cursed artifact", "a ghostly presence", "a hidden room full of secrets",
    "a creature that hunts in the dark", "a ritual that should never be performed",
]

SETTINGS = [
    "a small coastal town", "a sprawling metropolis", "an abandoned asylum",
    "a remote island", "a futuristic space station", "a hidden underground city",
    "a war-torn country", "a magical kingdom", "a dystopian future",
]

CHOICES = [
    ("duty", "love"), ("honor", "survival"), ("truth", "peace"),
    ("family", "justice"), ("freedom", "security"), ("faith", "reason"),
]

EVENTS = [
    "a devastating earthquake", "a mysterious fire", "a political scandal",
    "a sudden pandemic", "a devastating flood", "a terrorist attack",
]

CHARACTER_NAMES = [
    "Alex Mercer", "Jordan Blake", "Sam Rivera", "Casey Quinn", "Morgan Hayes",
    "Taylor Brooks", "Riley Carter", "Drew Simmons", "Jamie Walsh", "Avery Cole",
    "Logan Pierce", "Quinn Harper", "Sage Monroe", "Reese Donovan", "Blake Sutton",
]


# ── Helper functions ──────────────────────────────────────────────────────────

def _fill_template(template: str, rng: random.Random) -> str:
    """Fill a template string with random values."""
    return template.format(
        prefix=rng.choice(TITLE_PREFIXES),
        noun=rng.choice(TITLE_NOUNS),
        occupation=rng.choice(OCCUPATIONS),
        occupations=rng.choice(OCCUPATIONS),
        goal=rng.choice(GOALS),
        deadline=rng.choice(DEADLINES),
        antagonist=rng.choice(ANTAGONISTS),
        adjective=rng.choice(ADJECTIVES),
        victim=rng.choice(VICTIMS),
        conflict=rng.choice(CONFLICTS),
        fantasy_element=rng.choice(FANTASY_ELEMENTS),
        sci_fi_element=rng.choice(SCI_FI_ELEMENTS),
        horror_element=rng.choice(HORROR_ELEMENTS),
        setting=rng.choice(SETTINGS),
        choice_a=rng.choice(CHOICES)[0],
        choice_b=rng.choice(CHOICES)[1],
        event=rng.choice(EVENTS),
        year=rng.randint(2024, 2150),
        role_placeholder=rng.choice(OCCUPATIONS),
    )


def _generate_characters(count: int = 3, rng: random.Random = None) -> list[dict]:
    """Generate a list of character dicts."""
    if rng is None:
        rng = random.Random()
    characters = []
    used_names = set()
    available_names = list(CHARACTER_NAMES)
    for _ in range(count):
        if len(used_names) >= len(available_names):
            # All names exhausted, allow reuse
            name = rng.choice(available_names)
        else:
            name = rng.choice([n for n in available_names if n not in used_names])
        used_names.add(name)
        role = rng.choice(["protagonist", "antagonist", "ally", "mentor", "comic relief", "mysterious stranger"])
        description = f"A {rng.choice(ADJECTIVES)} {rng.choice(OCCUPATIONS)} who is {rng.choice(GOALS).replace('to ', '')}."
        characters.append({"name": name, "description": description, "role": role})
    return characters


# ── Main class ────────────────────────────────────────────────────────────────

class MovieIdeaGenerator:
    """Rule-based movie idea generator using templates and randomization."""

    VALID_GENRES = set(GENRES)

    def __init__(self, seed: Optional[int] = None):
        """Initialize the generator.

        Args:
            seed: Optional random seed for reproducibility.
        """
        self._rng = random.Random(seed)

    def _validate_genre(self, genre: Optional[str]) -> str:
        """Validate and return a genre string.

        Args:
            genre: Genre string to validate.

        Returns:
            The validated genre string.

        Raises:
            ValueError: If genre is not None and not in the valid genres list.
        """
        if genre is not None and genre not in self.VALID_GENRES:
            raise ValueError(
                f"Invalid genre: '{genre}'. Must be one of: {', '.join(sorted(self.VALID_GENRES))}"
            )
        return genre

    def generate(self, genre: Optional[str] = None) -> dict:
        """Generate a single movie idea.

        Args:
            genre: Optional genre to constrain the idea. If None, a random genre is chosen.

        Returns:
            A dict with keys: title, genre, logline, characters.

        Raises:
            ValueError: If genre is provided but not in the valid genres list.
        """
        self._validate_genre(genre)
        chosen_genre = genre or self._rng.choice(GENRES)
        templates = GENRE_TEMPLATES[chosen_genre]
        template = self._rng.choice(templates)
        logline = _fill_template(template, self._rng)
        title = f"{self._rng.choice(TITLE_PREFIXES)} {self._rng.choice(TITLE_NOUNS)}"
        characters = _generate_characters(3, self._rng)
        return {
            "title": title,
            "genre": chosen_genre,
            "logline": logline,
            "characters": characters,
        }

    def generate_batch(self, count: int = 1, genre: Optional[str] = None) -> list[dict]:
        """Generate multiple movie ideas.

        Args:
            count: Number of ideas to generate. Must be >= 0.
            genre: Optional genre to constrain all ideas.

        Returns:
            A list of movie idea dicts.

        Raises:
            ValueError: If count < 0.
        """
        if count < 0:
            raise ValueError(f"count must be >= 0, got {count}")
        if count == 0:
            return []
        return [self.generate(genre=genre) for _ in range(count)]
