## Phase 1 — Character Reference Sheet Generation (MVP)

### Description

Build the foundational data model and generation logic for character reference sheets. This phase creates a `ConsistentCharacterStage` that generates a **single reference image per character** using a text-to-image API, and stores it alongside the project data. No scene-level consistency yet — just one clean reference per character.

### Deliverables

| Artifact | Location | Depends On |
|---|---|---|
| `models.py` extensions | `consistent_character_developer/ai_consistent_char/models.py` | `ai_movie_gen_suite.models` |
| `image_provider.py` | `consistent_character_developer/ai_consistent_char/image_provider.py` | — |
| `reference_sheet_generator.py` | `consistent_character_developer/ai_consistent_char/reference_sheet_generator.py` | image_provider, models |
| `consistent_character_stage.py` | `consistent_character_developer/ai_consistent_char/stages/consistent_character_stage.py` | orchestrator, reference_sheet_generator |
| CLI extension | `consistent_character_developer/ai_consistent_char/cli.py` | main pipeline |
| Unit tests | `consistent_character_developer/tests/test_reference_sheet.py` | reference_sheet_generator |

### Dependencies (from existing projects)

| Import | Source Module | Usage |
|---|---|---|
| `Character`, `CharacterRegistry` | `ai_movie_gen_suite.models` | Input — iterate characters to generate refs |
| `SceneDescriptionCollection` | `ai_movie_gen_suite.models` | Pass-through to downstream stages |
| `PipelineConfig` | `ai_movie_gen_suite.pipeline.orchestrator` | Extend with `character_image_provider` field |
| `MovieGenerationPipeline` | `ai_movie_gen_suite.pipeline.orchestrator` | Insert new stage into pipeline |
| `LLMConfig` | `ai_movie_gen_suite.config` | Optional: use LLM to refine visual_anchor text |

### API Surface

```python
# models.py
class CharacterVisualProfile(BaseModel):
    character_id: str
    reference_image_path: str  # path to PNG
    visual_anchor_text: str    # textual description used for generation
    prompt: str                # full prompt sent to image provider
    status: str                # "pending" | "generated" | "failed"
    seed: Optional[int] = None

# image_provider.py
class CharacterImageProvider(ABC):
    @abstractmethod
    def generate_reference_image(
        self,
        character: Character,
        visual_anchor_text: str,
        output_path: Path,
        seed: Optional[int] = None,
    ) -> str:
        """Generate a character reference image. Returns the output path."""
        ...

class KlingImageProvider(CharacterImageProvider):
    """Kling AI image generation provider."""
    ...

# reference_sheet_generator.py
class ReferenceSheetGenerator:
    def __init__(self, provider: CharacterImageProvider, output_dir: Path):
        ...

    def generate_for_registry(self, registry: CharacterRegistry) -> Dict[str, str]:
        """Generate reference images for all characters. Returns {char_id: image_path}."""
        ...

# consistent_character_stage.py
class ConsistentCharacterStage:
    def __init__(self, registry: CharacterRegistry, output_dir: Path, provider: CharacterImageProvider):
        ...

    def execute(self) -> CharacterRegistry:
        """Generate reference images and augment the registry. Returns augmented registry."""
        ...
```

### Test Plan

| Test | Type | What It Validates |
|---|---|---|
| `test_reference_sheet_generator_initialization` | Unit | Generator accepts provider and output dir |
| `test_generate_for_registry_empty` | Unit | Empty registry returns empty dict |
| `test_generate_for_registry_single_char` | Unit | Single character produces one image file |
| `test_generate_for_registry_multiple_chars` | Unit | Multiple characters produce distinct images |
| `test_image_path_is_valid_file` | Unit | Generated file exists and is valid PNG |
| `test_registry_augmented_with_visual_data` | Unit | Registry characters have `visual_anchor_image_path` set |
| `test_consistent_character_stage_integration` | Integration | Stage can be inserted into pipeline and returns augmented registry |
| `test_kling_provider_validation` | Unit | Provider validates API key presence |

#