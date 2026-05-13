"""BeatGenerator — deterministic Save-the-Cat beat sheet generator."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Beat:
    """A single beat in the Save-the-Cat structure."""

    beat_number: int
    beat_name: str
    summary: str
    description: str
    phase: str = "setup"
    characters_involved: List[str] = field(default_factory=list)
    estimated_page_range: str = ""


@dataclass
class BeatSheet:
    """A complete Save-the-Cat beat sheet."""

    title: str
    genre: str
    logline: str
    beats: List[Beat] = field(default_factory=list)
    tone: str = ""

    def add_beat(self, beat: Beat) -> None:
        """Add a beat to the sheet."""
        self.beats.append(beat)

    def model_dump(self) -> dict:
        """Serialize the beat sheet to a dict."""
        return {
            "title": self.title,
            "genre": self.genre,
            "logline": self.logline,
            "tone": self.tone,
            "beats": [
                {
                    "beat_number": b.beat_number,
                    "beat_name": b.beat_name,
                    "summary": b.summary,
                    "description": b.description,
                    "phase": b.phase,
                    "characters_involved": b.characters_involved,
                    "estimated_page_range": b.estimated_page_range,
                }
                for b in self.beats
            ],
        }


# ── Save-the-Cat 15-beat structure ────────────────────────────────────────────

SAVE_THE_CAT_BEATS = [
    "Opening Image",
    "Theme Stated",
    "Setup",
    "Catalyst",
    "Debate",
    "Break into Two",
    "B Story",
    "Fun and Games",
    "Midpoint",
    "Bad Guys Close In",
    "All Is Lost",
    "Dark Night of the Soul",
    "Break into Three",
    "Finale",
    "Final Image",
]

PHASE_MAP = {
    "Opening Image": "setup",
    "Theme Stated": "setup",
    "Setup": "setup",
    "Catalyst": "setup",
    "Debate": "setup",
    "Break into Two": "setup",
    "B Story": "confrontation",
    "Fun and Games": "confrontation",
    "Midpoint": "confrontation",
    "Bad Guys Close In": "confrontation",
    "All Is Lost": "confrontation",
    "Dark Night of the Soul": "confrontation",
    "Break into Three": "resolution",
    "Finale": "resolution",
    "Final Image": "resolution",
}

PAGE_RANGES = {
    "Opening Image": "1",
    "Theme Stated": "1-2",
    "Setup": "2-12",
    "Catalyst": "12-15",
    "Debate": "15-25",
    "Break into Two": "25-28",
    "B Story": "28-30",
    "Fun and Games": "30-55",
    "Midpoint": "55-60",
    "Bad Guys Close In": "60-75",
    "All Is Lost": "75-80",
    "Dark Night of the Soul": "80-85",
    "Break into Three": "85-88",
    "Finale": "88-105",
    "Final Image": "105",
}

# ── Beat descriptions ──────────────────────────────────────────────────────────

BEAT_DESCRIPTIONS = {
    "Opening Image": "A visual snapshot that establishes the tone, setting, and protagonist's ordinary world. This image should contrast with the Final Image to show transformation.",
    "Theme Stated": "Someone states the theme of the story, often in a casual conversation. The protagonist doesn't understand it yet, but the audience picks up on it.",
    "Setup": "We see the protagonist's ordinary world, their flaws, their desires, and their relationships. We learn what they need but don't yet know what they want.",
    "Catalyst": "A major event that disrupts the protagonist's ordinary world. This is the inciting incident that sets the story in motion.",
    "Debate": "The protagonist wrestles with the decision to respond to the Catalyst. Should they take the journey? What are the risks? This creates tension and uncertainty.",
    "Break into Two": "The protagonist makes a decisive choice to enter the new world of the story. There's no turning back now.",
    "B Story": "The love story or secondary relationship begins. This is where the theme will be explored more deeply through personal connections.",
    "Fun and Games": "The promise of the premise is fulfilled. This is the best part of the movie — the trailer moments. The protagonist explores the new world.",
    "Midpoint": "A major event raises the stakes. The protagonist moves from reactive to proactive. The false victory or false defeat changes everything.",
    "Bad Guys Close In": "External pressures mount and internal doubts creep in. The antagonist's plan gains momentum. The protagonist's team may face internal conflict.",
    "All Is Lost": "The lowest point. The protagonist suffers a major defeat. Often a 'death' (literal or metaphorical) occurs. The 'whiff of death' is present.",
    "Dark Night of the Soul": "The protagonist wallows in despair. All seems lost. But in this darkness, a breakthrough comes — often through the B Story or a realization of the theme.",
    "Break into Three": "The protagonist finds the solution, often through combining everything learned. The A, B, and C stories converge. A new plan is formed.",
    "Finale": "The protagonist confronts the antagonist using the theme they've learned. The story is resolved. The protagonist proves they've changed.",
    "Final Image": "The opposite of the Opening Image. Shows how the protagonist and their world have changed. A visual confirmation of the transformation.",
}


# ── Character role mapping ─────────────────────────────────────────────────────

# Characters that should appear in specific beats based on their role
CHARACTER_BEAT_INFLUENCE = {
    "protagonist": [
        "Opening Image", "Theme Stated", "Setup", "Catalyst", "Debate",
        "Break into Two", "B Story", "Fun and Games", "Midpoint",
        "Bad Guys Close In", "All Is Lost", "Dark Night of the Soul",
        "Break into Three", "Finale", "Final Image",
    ],
    "antagonist": [
        "Catalyst", "Debate", "Fun and Games", "Midpoint",
        "Bad Guys Close In", "All Is Lost", "Finale",
    ],
    "ally": [
        "Setup", "Catalyst", "Debate", "Break into Two", "B Story",
        "Fun and Games", "Midpoint", "Bad Guys Close In",
        "Dark Night of the Soul", "Break into Three", "Finale",
    ],
    "mentor": [
        "Theme Stated", "Setup", "Catalyst", "Debate", "B Story",
        "Fun and Games", "All Is Lost", "Break into Three",
    ],
    "comic relief": [
        "Setup", "Fun and Games", "Midpoint", "Bad Guys Close In",
        "Dark Night of the Soul", "Finale",
    ],
    "mysterious stranger": [
        "Setup", "Catalyst", "Fun and Games", "Midpoint",
        "All Is Lost", "Break into Three",
    ],
}


# ── Beat summary templates ─────────────────────────────────────────────────────

BEAT_SUMMARY_TEMPLATES = {
    "Opening Image": "We meet {protagonist} in their ordinary world, showing {protagonist_trait} and the status quo that will soon be disrupted.",
    "Theme Stated": "A supporting character states the theme: '{theme_quote}'. {protagonist} dismisses it, not yet understanding its importance.",
    "Setup": "We see {protagonist}'s daily life, their {flaw}, their {desire}, and their relationships with {ally_name} and {mentor_name}.",
    "Catalyst": "{catalyst_event} shatters {protagonist}'s ordinary world. The call to adventure is clear: {call_to_action}.",
    "Debate": "{protagonist} wrestles with the decision. {ally_name} offers advice, but {protagonist} fears {fear}. The stakes feel too high.",
    "Break into Two": "{protagonist} makes a decisive choice: {decision}. There's no turning back — {protagonist} enters the new world.",
    "B Story": "{b_story_character} enters {protagonist}'s life. Their relationship becomes the emotional core where the theme is explored.",
    "Fun and Games": "{protagonist} explores the new world, experiencing {fun_moments}. The promise of the premise is fulfilled with {highlight_moment}.",
    "Midpoint": "{midpoint_event} raises the stakes dramatically. {protagonist} shifts from reactive to proactive, claiming {false_victory_or_defeat}.",
    "Bad Guys Close In": "{antagonist} strikes back with {antagonist_action}. {protagonist}'s team faces {internal_conflict} while external pressures mount.",
    "All Is Lost": "Everything collapses. {loss_event} leaves {protagonist} devastated. The 'whiff of death' hangs heavy — all seems truly lost.",
    "Dark Night of the Soul": "{protagonist} wallows in despair. But {breakthrough_moment} brings a glimmer of hope. The theme finally clicks: {theme_realization}.",
    "Break into Three": "{protagonist} combines all lessons learned. {new_plan} emerges. {protagonist} realizes {key_insight} and prepares for the final confrontation.",
    "Finale": "{protagonist} confronts {antagonist} using the theme. {final_battle} resolves the story. {protagonist} proves they've changed by {proof_of_change}.",
    "Final Image": "The opposite of the Opening Image. {protagonist} is now {transformed_trait}, showing the complete transformation from the story's start.",
}


# ── Template values ────────────────────────────────────────────────────────────

THEME_QUOTES = [
    "You can't run from who you are.",
    "Family comes first, always.",
    "Sometimes you have to lose everything to find yourself.",
    "Trust is earned, not given.",
    "The truth will set you free, but first it will make you miserable.",
    "Love requires courage.",
    "We are what we choose to be.",
    "No one fights alone.",
    "Change starts with a single step.",
    "What matters isn't where you start, but where you finish.",
]

PROTAGONIST_TRAITS = [
    "their stubborn independence",
    "their fear of commitment",
    "their hidden vulnerability",
    "their relentless determination",
    "their tendency to push people away",
    "their inability to ask for help",
    "their stubborn optimism",
    "their fear of failure",
    "their tendency to take on too much",
    "their emotional walls",
]

FLAWS = [
    "stubbornness",
    "fear of vulnerability",
    "inability to trust",
    "perfectionism",
    "self-sacrifice to a fault",
    "avoidance of conflict",
    "overconfidence",
    "emotional detachment",
    "people-pleasing",
    "fear of abandonment",
]

DESIRES = [
    "deep desire for connection",
    "need for control",
    "longing for freedom",
    "desire for recognition",
    "need for security",
    "yearning for belonging",
    "desire for justice",
    "need for independence",
    "longing for peace",
    "desire for redemption",
]

CATALYST_EVENTS = [
    "A mysterious letter arrives",
    "An old friend reappears",
    "A sudden crisis forces action",
    "A shocking revelation changes everything",
    "An unexpected opportunity presents itself",
    "A threat to someone they love",
    "A discovery that challenges their worldview",
    "A chance encounter with a stranger",
    "A failure that forces reflection",
    "A promise made long ago resurfaces",
]

CALLS_TO_ACTION = [
    "to face the unknown",
    "to seek the truth",
    "to protect what matters",
    "to confront their past",
    "to find themselves",
    "to make things right",
    "to discover who they really are",
    "to break free from their past",
    "to save those they love",
    "to prove their worth",
]

FEARS = [
    "failing those who depend on them",
    "losing control of their life",
    "being hurt again",
    "facing their own weaknesses",
    "abandoning their principles",
    "disappointing their family",
    "becoming like their worst fear",
    "losing their identity",
    "failing to live up to expectations",
    "being alone forever",
]

DECISIONS = [
    "to leave everything behind",
    "to accept the challenge",
    "to confront the truth",
    "to take the leap of faith",
    "to stop running and face what's coming",
    "to trust someone for the first time",
    "to fight for what's right",
    "to embrace the unknown",
    "to seek redemption",
    "to finally speak their truth",
]

FUN_MOMENTS = [
    "unexpected alliances and humorous mishaps",
    "the thrill of discovery and new possibilities",
    "learning new skills with mixed results",
    "bonding with unlikely companions",
    "navigating the rules of this new world",
    "experiencing the full promise of the premise",
    "testing boundaries and discovering strengths",
    "forming connections that surprise them",
    "exploring the full range of what's possible",
    "finding joy in unexpected places",
]

HIGHLIGHT_MOMENTS = [
    "a daring rescue that showcases {protagonist}'s courage",
    "a clever scheme that turns the tables",
    "an unexpected ally who changes the game",
    "a moment of pure triumph against the odds",
    "a discovery that reveals the true scope of the challenge",
    "a confrontation that proves {protagonist}'s growth",
    "a celebration that shows what's at stake",
    "a display of {protagonist}'s unique skills",
    "a moment that captures the spirit of the premise",
    "a showcase of the story's unique world",
]

MIDPOINT_EVENTS = [
    "A major victory reveals the true scope of the conflict",
    "A betrayal shifts the balance of power",
    "A discovery changes everything {protagonist} thought they knew",
    "A confrontation with the antagonist raises the stakes",
    "A moment of clarity reveals the path forward",
    "A sacrifice reveals what truly matters",
    "A revelation about the antagonist's plan",
    "A test that proves {protagonist}'s readiness",
    "A turning point that changes the direction of the story",
    "A moment that separates the real threat from the surface problem",
]

FALSE_VICTORIES = [
    "a temporary victory that masks deeper problems",
    "a false sense of security before the real storm",
    "an apparent success that reveals a larger conspiracy",
    "a victory that comes at a hidden cost",
    "a breakthrough that exposes new vulnerabilities",
    "a triumph that reveals the true enemy",
    "a success that shows how far {protagonist} has come",
    "a win that proves {protagonist} is ready for more",
    "a moment of clarity that changes the mission",
    "a victory that reveals the stakes are even higher",
]

ANTAGONIST_ACTIONS = [
    "a devastating counterattack",
    "manipulating {protagonist}'s allies",
    "closing the trap with ruthless efficiency",
    "exploiting {protagonist}'s greatest weakness",
    "revealing a shocking truth about the situation",
    "cutting off {protagonist}'s resources",
    "turning {protagonist}'s allies against them",
    "accelerating their own plan with terrifying speed",
    "demonstrating their superior power",
    "making a move that seems unbeatable",
]

INTERNAL_CONFLICTS = [
    "distrust and conflicting agendas",
    "fear of the unknown pulling them apart",
    "disagreement on the best course of action",
    "past grievances resurfacing under pressure",
    "doubts about {protagonist}'s leadership",
    "competing priorities threatening the mission",
    "fear of failure creating tension",
    "moral disagreements about the cost of success",
    "loyalty tested by impossible choices",
    "the weight of responsibility fracturing the group",
]

LOSS_EVENTS = [
    "{protagonist} loses their most trusted ally",
    "Everything {protagonist} fought for is destroyed",
    "{protagonist} is betrayed by someone they trusted",
    "The plan fails catastrophically",
    "{protagonist} loses hope and everything they believed in",
    "A sacrifice {protagonist} couldn't prevent",
    "The truth is worse than {protagonist} imagined",
    "{protagonist} is isolated and alone",
    "All resources are gone and the enemy is winning",
    "{protagonist}'s greatest fear has come true",
]

BREAKTHROUGH_MOMENTS = [
    "A memory of {mentor_name}'s wisdom surfaces",
    "{ally_name} sends a message of hope",
    "A small act of kindness reveals the path forward",
    "{protagonist} realizes the theme was right all along",
    "A conversation with {b_story_character} changes everything",
    "A moment of clarity in the darkness",
    "Remembering why {protagonist} started this journey",
    "A realization that {protagonist} isn't alone",
    "Understanding that the real battle is internal",
    "A flashback reveals the key to success",
]

THEME_REALIZATIONS = [
    "that courage isn't the absence of fear",
    "that true strength comes from vulnerability",
    "that they can't do this alone",
    "that the journey matters more than the destination",
    "that love requires letting go",
    "that they must become who they need to be",
    "that the truth is the only way forward",
    "that sacrifice is the price of growth",
    "that they are enough as they are",
    "that the theme was the answer all along",
]

NEW_PLANS = [
    "{protagonist} devises a bold new strategy",
    "A plan emerges from combining old lessons with new insights",
    "{protagonist} realizes the only way is through",
    "An unexpected approach reveals the path to victory",
    "{protagonist} turns their weakness into strength",
    "A new understanding creates a new possibility",
    "{protagonist} embraces the theme as a weapon",
    "The solution was hidden in plain sight all along",
    "{protagonist} finds the courage to try what no one else would",
    "A final piece of the puzzle falls into place",
]

KEY_INSIGHTS = [
    "that the real enemy was never what they thought",
    "that they've been fighting the wrong battle",
    "that the theme isn't just words — it's a way of life",
    "that they have everything they need inside them",
    "that the journey has changed them more than the destination",
    "that the answer was in the B Story all along",
    "that they must trust themselves and others",
    "that the cost of not trying is greater than the risk of trying",
    "that they are the hero they've been waiting for",
    "that the only way out is through",
]

FINAL_BATTLES = [
    "A climactic confrontation tests everything {protagonist} has learned",
    "{protagonist} uses the theme to overcome the impossible",
    "The final showdown reveals the true nature of the conflict",
    "{protagonist} faces {antagonist} with newfound wisdom",
    "A battle that tests both physical and emotional strength",
    "{protagonist} proves their growth through action, not words",
    "The climax resolves both the external and internal conflicts",
    "{protagonist} uses everything they've learned in the final moment",
    "A confrontation that proves {protagonist} has truly changed",
    "The final test that separates the hero from the legend",
]

PROOFS_OF_CHANGE = [
    "choosing selflessness over self-preservation",
    "embracing vulnerability as strength",
    "trusting others with their life",
    "facing their greatest fear without hesitation",
    "putting the team before themselves",
    "speaking truth to power",
    "letting go of control and trusting the process",
    "accepting help and giving it in return",
    "choosing love over fear",
    "standing up for what's right despite the cost",
]

TRANSFORMED_TRAITS = [
    "no longer the person who started this journey",
    "someone who has found their true purpose",
    "stronger, wiser, and more connected than before",
    "someone who understands what truly matters",
    "a person who has faced their darkness and emerged brighter",
    "someone who has learned to trust and be trusted",
    "a hero who proves that change is possible",
    "someone who has found peace with who they are",
    "a person who has transformed fear into courage",
    "someone who has become the person they needed to be",
]


class BeatGenerator:
    """Generates a Save-the-Cat 15-beat sheet deterministically.

    Uses template-based generation with configurable randomness for variety.
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize the generator.

        Args:
            seed: Optional random seed for reproducibility.
        """
        self._rng = random.Random(seed)

    def generate_beat_sheet(
        self,
        title: str,
        genre: str,
        logline: str,
        characters: Optional[List[dict]] = None,
        tone: str = "",
    ) -> BeatSheet:
        """Generate a complete Save-the-Cat beat sheet.

        Args:
            title: The movie title.
            genre: The movie genre.
            logline: The movie logline.
            characters: List of character dicts with 'name', 'role', 'description'.
            tone: The tone of the story.

        Returns:
            A BeatSheet with all 15 beats populated.
        """
        beat_sheet = BeatSheet(title=title, genre=genre, logline=logline, tone=tone)

        # Extract character info
        protagonist = None
        antagonist = None
        ally = None
        mentor = None
        b_story_character = None
        comic_relief = None
        mysterious_stranger = None

        if characters:
            for char in characters:
                role = char.get("role", "")
                name = char.get("name", "Unknown")
                if role == "protagonist":
                    protagonist = name
                elif role == "antagonist":
                    antagonist = name
                elif role == "ally":
                    ally = name
                elif role == "mentor":
                    mentor = name
                elif role == "comic relief":
                    comic_relief = name
                elif role == "mysterious stranger":
                    mysterious_stranger = name

        # Default B story character is the ally if no specific one
        if not b_story_character:
            b_story_character = ally or protagonist

        # Generate template values
        theme_quote = self._rng.choice(THEME_QUOTES)
        protagonist_trait = self._rng.choice(PROTAGONIST_TRAITS)
        flaw = self._rng.choice(FLAWS)
        desire = self._rng.choice(DESIRES)
        catalyst_event = self._rng.choice(CATALYST_EVENTS)
        call_to_action = self._rng.choice(CALLS_TO_ACTION)
        fear = self._rng.choice(FEARS)
        decision = self._rng.choice(DECISIONS)
        fun_moments = self._rng.choice(FUN_MOMENTS)
        highlight_moment = self._rng.choice(HIGHLIGHT_MOMENTS)
        midpoint_event = self._rng.choice(MIDPOINT_EVENTS)
        false_victory = self._rng.choice(FALSE_VICTORIES)
        antagonist_action = self._rng.choice(ANTAGONIST_ACTIONS)
        internal_conflict = self._rng.choice(INTERNAL_CONFLICTS)
        loss_event = self._rng.choice(LOSS_EVENTS)
        breakthrough = self._rng.choice(BREAKTHROUGH_MOMENTS)
        theme_realization = self._rng.choice(THEME_REALIZATIONS)
        new_plan = self._rng.choice(NEW_PLANS)
        key_insight = self._rng.choice(KEY_INSIGHTS)
        final_battle = self._rng.choice(FINAL_BATTLES)
        proof_of_change = self._rng.choice(PROOFS_OF_CHANGE)
        transformed_trait = self._rng.choice(TRANSFORMED_TRAITS)

        # Fill in template values with character names
        template_values = {
            "protagonist": protagonist or "our hero",
            "protagonist_trait": protagonist_trait,
            "theme_quote": theme_quote,
            "flaw": flaw,
            "desire": desire,
            "ally_name": ally or "an ally",
            "mentor_name": mentor or "a mentor",
            "catalyst_event": catalyst_event,
            "call_to_action": call_to_action,
            "fear": fear,
            "decision": decision,
            "b_story_character": b_story_character or "a new companion",
            "fun_moments": fun_moments,
            "highlight_moment": highlight_moment,
            "midpoint_event": midpoint_event,
            "false_victory_or_defeat": false_victory,
            "antagonist": antagonist or "the antagonist",
            "antagonist_action": antagonist_action,
            "internal_conflict": internal_conflict,
            "loss_event": loss_event,
            "breakthrough_moment": breakthrough,
            "theme_realization": theme_realization,
            "new_plan": new_plan,
            "key_insight": key_insight,
            "final_battle": final_battle,
            "proof_of_change": proof_of_change,
            "transformed_trait": transformed_trait,
        }

        # Generate each beat
        for i, beat_name in enumerate(SAVE_THE_CAT_BEATS, start=1):
            phase = PHASE_MAP.get(beat_name, "setup")
            page_range = PAGE_RANGES.get(beat_name, "")
            description = BEAT_DESCRIPTIONS.get(beat_name, "")

            # Generate summary using template
            template = BEAT_SUMMARY_TEMPLATES.get(beat_name, "")
            if template:
                try:
                    summary = template.format(**template_values)
                except KeyError:
                    summary = f"The {beat_name.lower()} — a pivotal moment in the story."
            else:
                summary = f"The {beat_name.lower()} — a pivotal moment in the story."

            # Determine characters involved
            characters_involved = []
            if characters:
                for char in characters:
                    role = char.get("role", "")
                    name = char.get("name", "Unknown")
                    if role in CHARACTER_BEAT_INFLUENCE:
                        if beat_name in CHARACTER_BEAT_INFLUENCE[role]:
                            characters_involved.append(name)

            beat = Beat(
                beat_number=i,
                beat_name=beat_name,
                summary=summary,
                description=description,
                phase=phase,
                characters_involved=characters_involved,
                estimated_page_range=page_range,
            )
            beat_sheet.add_beat(beat)

        return beat_sheet
