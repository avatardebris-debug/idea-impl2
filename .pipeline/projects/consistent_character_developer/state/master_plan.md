# Consistent Character Developer — Master Plan

## Idea Summary

**Consistent Character Developer** extends the existing `ai_movie_generation_suite` pipeline to produce and maintain **visually consistent character reference images** across all scenes of a generated screenplay. It integrates with Kling AI (or similar image-generation APIs) to generate character reference sheets and per-scene character renders, ensuring that every character retains the same visual identity (face, body type, clothing style, color palette) throughout the entire production.

### Core Deliverable

A pipeline extension that:
1. Generates a **character reference sheet** for each character at character-creation time.
2. Stores and version-controls **visual anchor images** (reference photos) per character.
3. Produces **per-scene consistent character renders** by injecting reference images into the image-generation prompt.
4. Integrates cleanly into the existing `MovieGenerationPipeline` as a new stage (between character generation and script writing).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MovieGenerationPipeline                   │
│  (ai_movie_gen_suite.pipeline.orchestrator)                 │
│                                                             │
│  Step 1: BeatGenerator  ──→  BeatSheet                     │
│  Step 2: CharacterGenerator ──→  CharacterRegistry         │
│  Step 3: ┌──────────────────────────────────────────────┐  │
│           │  NEW: ConsistentCharacterStage               │  │
│           │  - Generates reference images per character  │  │
│           │  - Stores visual anchor data in project dir  │  │
│           │  - Injects visual_anchor into scene prompts  │  │
│           └──────────────────────────────────────────────┘  │
│  Step 4: ScriptWriter  ──→  Script                         │
│  Step 5: SceneDescriptionEngine ──→  SceneDescriptionColl  │
│  Step 6: Formatter (JSON / FDX / YAML)                     │
└─────────────────────────────────────────────────────────────┘

Dependency imports:
  - ai_movie_gen_suite.models: Character, CharacterRegistry, Scene, Script, etc.
  - ai_movie_gen_suite.pipeline.orchestrator: MovieGenerationPipeline, PipelineConfig
  - ai_movie_gen_suite.stages.character_generator: CharacterGenerator
  - ai_movie_gen_suite.config: LLMConfig, SuiteConfig
  - ai_movie_gen_suite.formatters.json_formatter: JSONFormatter
```

### Key Design Decisions

- **Character ID as the primary key**: We use the existing `Character.id` field (UUID) as the immutable identifier for all visual assets. This ensures consistency across pipeline stages.
- **Visual anchor field**: The existing `Character.visual_anchor` field is repurposed as a *textual* description, while a new `visual_anchor_image_path` field on the character model tracks the actual image file.
- **Reference image format**: PNG with transparent background for maximum flexibility in downstream compositing.
- **API abstraction**: A `CharacterImageProvider` interface allows swapping between Kling AI, Stable Diffusion, and other providers.

---

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

### Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Kling AI API rate limits or downtime | Implement retry logic with exponential backoff; fallback to placeholder image |
| Image generation takes 30+ seconds per character | Add async/parallel generation; progress logging |
| Character descriptions are too vague for good images | Add an LLM-powered "visual anchor refinement" step before image generation |
| Breaking changes in existing `Character` model | Use Pydantic's `model_copy` or explicit field mapping; never mutate original |

---

## Phase 2 — Per-Scene Consistent Character Renders

### Description

Extend the pipeline to generate **per-scene character renders** that maintain visual consistency. Each scene's character appearances are generated by injecting the character's reference image as a control input (img2img / reference-only mode) into the image-generation API. This ensures that the same character looks identical across different scenes, even when the scene's lighting, pose, and background change.

### Deliverables

| Artifact | Location | Depends On |
|---|---|---|
| `scene_character_renderer.py` | `consistent_character_developer/ai_consistent_char/scene_character_renderer.py` | reference_sheet_generator, image_provider |
| `scene_description_engine_extension.py` | `consistent_character_developer/ai_consistent_char/stages/scene_description_engine_extension.py` | scene_description_engine, scene_character_renderer |
| `pipeline_extension.py` | `consistent_character_developer/ai_consistent_char/pipeline_extension.py` | orchestrator, consistent_character_stage |
| CLI extension | `consistent_character_developer/ai_consistent_char/cli.py` (updated) | pipeline_extension |
| Unit tests | `consistent_character_developer/tests/test_scene_renderer.py` | scene_character_renderer |
| Integration tests | `consistent_character_developer/tests/test_full_pipeline.py` | pipeline_extension |

### Dependencies (from existing projects)

| Import | Source Module | Usage |
|---|---|---|
| `SceneDescription`, `SceneDescriptionCollection` | `ai_movie_gen_suite.models` | Input — iterate scenes to generate character renders |
| `SceneDescriptionEngine` | `ai_movie_gen_suite.stages.scene_description_engine` | Wrap/extend to add image generation |
| `Script` | `ai_movie_gen_suite.models` | Access scene list and character references |
| `MovieGenerationPipeline` | `ai_movie_gen_suite.pipeline.orchestrator` | Insert scene renderer stage |

### API Surface

```python
# scene_character_renderer.py
class SceneCharacterRenderer:
    def __init__(
        self,
        provider: CharacterImageProvider,
        reference_images: Dict[str, str],  # {char_id: ref_image_path}
        output_dir: Path,
    ):
        ...

    def render_scene(
        self,
        scene: Scene,
        character_registry: CharacterRegistry,
    ) -> List[SceneCharacterRender]:
        """Generate consistent character renders for a single scene."""
        ...

    def render_all_scenes(
        self,
        script: Script,
        character_registry: CharacterRegistry,
    ) -> SceneCharacterRenderCollection:
        """Generate renders for all scenes."""
        ...

# scene_description_engine_extension.py
class SceneDescriptionEngineExtension:
    def __init__(
        self,
        base_engine: SceneDescriptionEngine,
        renderer: SceneCharacterRenderer,
    ):
        ...

    def generate_descriptions(self) -> SceneDescriptionCollection:
        """Generate descriptions + character renders for all scenes."""
        ...
```

### Test Plan

| Test | Type | What It Validates |
|---|---|---|
| `test_scene_renderer_initialization` | Unit | Renderer accepts provider, ref images, output dir |
| `test_render_scene_single_character` | Unit | Single character in scene produces one render |
| `test_render_scene_multiple_characters` | Unit | Multiple characters in scene produce multiple renders |
| `test_reference_image_injected` | Mock | Verify reference image path is passed to provider |
| `test_render_all_scenes` | Unit | All scenes in script are processed |
| `test_collection_contains_all_renders` | Unit | Output collection has correct scene-to-renders mapping |
| `test_full_pipeline_with_scene_renders` | Integration | End-to-end: logline → beat sheet → characters → refs → scenes → renders |

### Risks & Mitigations

| Risk | Mitigation |
|---|---|
| img2img reference mode not supported by all providers | Provider abstraction allows per-provider implementation; document supported providers |
| Scene renders significantly increase pipeline runtime | Add `--skip-scene-renders` CLI flag; make it opt-in |
| Character renders may drift from reference over multiple scenes | Use high reference strength (0.8–1.0); add a "refresh reference" mechanism every N scenes |

---

## Phase 3 — Visual Anchor Refinement & Quality Control

### Description

Add an **LLM-powered visual anchor refinement** step that improves the textual descriptions used for image generation, and a **quality control** mechanism that validates generated reference images for consistency. This phase also adds a **character comparison tool** that can detect drift between reference and scene renders.

### Deliverables

| Artifact | Location | Depends On |
|---|---|---|
| `visual_anchor_refiner.py` | `consistent_character_developer/ai_consistent_char/visual_anchor_refiner.py` | LLM integration |
| `quality_checker.py` | `consistent_character_developer/ai_consistent_char/quality_checker.py` | image_provider, models |
| `character_comparator.py` | `consistent_character_developer/ai_consistent_char/character_comparator.py` | quality_checker |
| CLI extension | `consistent_character_developer/ai_consistent_char/cli.py` (updated) | all above |
| Unit tests | `consistent_character_developer/tests/test_quality_checker.py` | quality_checker |
| CLI tests | `consistent_character_developer/tests/test_cli.py` | cli |

### Dependencies (from existing projects)

| Import | Source Module | Usage |
|---|---|---|
| `LLMConfig` | `ai_movie_gen_suite.config` | Pass LLM config to refiner |
| `Character` | `ai_movie_gen_suite.models` | Input for visual anchor refinement |
| `CharacterRegistry` | `ai_movie_gen_suite.models` | Batch process all characters |

### API Surface

```python
# visual_anchor_refiner.py
class VisualAnchorRefiner:
    def __init__(self, llm_client: Any, llm_config: LLMConfig):
        ...

    def refine(self, character: Character) -> str:
        """Refine the visual_anchor text using LLM for better image generation."""
        ...

    def refine_registry(self, registry: CharacterRegistry) -> CharacterRegistry:
        """Refine all characters' visual anchors. Returns augmented registry."""
        ...

# quality_checker.py
class QualityChecker:
    def __init__(self, provider: CharacterImageProvider):
        ...

    def check_reference_consistency(
        self,
        character_id: str,
        reference_image_path: Path,
        scene_render_path: Path,
        threshold: float = 0.85,
    ) -> bool:
        """Check if scene render is visually consistent with reference."""
        ...

    def check_registry_quality(
        self,
        registry: CharacterRegistry,
        renders: SceneCharacterRenderCollection,
    ) -> QualityReport:
        """Check all characters' quality. Returns report."""
        ...

# character_comparator.py
class CharacterComparator:
    def compare(
        self,
        ref_image_path: Path,
        render_image_path: Path,
    ) -> ComparisonResult:
        """Compare two character images. Returns similarity score and details."""
        ...
```

### Test Plan

| Test | Type | What It Validates |
|---|---|---|
| `test_visual_anchor_refiner_initialization` | Unit | Refiner accepts LLM client and config |
| `test_refine_single_character` | Mock | LLM is called with correct prompt; returns improved text |
| `test_refine_registry` | Mock | All characters are refined; registry updated |
| `test_quality_checker_initialization` | Unit | Checker accepts provider |
| `test_check_reference_consistency_high_similarity` | Unit | High similarity returns True |
| `test_check_reference_consistency_low_similarity` | Unit | Low similarity returns False |
| `test_character_comparator` | Unit | Comparator returns valid similarity score |
| `test_cli_quality_check_command` | CLI | CLI `--quality-check` flag works end-to-end |

### Risks & Mitigations

| Risk | Mitigation |
|---|---|
| LLM refinement adds cost and latency | Make it opt-in via `--refine-visual-anchors` flag |
| Image similarity metrics may not correlate with human perception | Use multiple metrics (SSIM + LPIPS); allow configurable thresholds |
| CLI complexity grows with new flags | Group related flags under subcommands (e.g., `ai-consistent-char ref`, `ai-consistent-char quality`) |

---

## File Structure

```
consistent_character_developer/
├── ai_consistent_char/
│   ├── __init__.py
│   ├── models.py                    # Phase 1
│   ├── image_provider.py            # Phase 1
│   ├── reference_sheet_generator.py # Phase 1
│   ├── scene_character_renderer.py  # Phase 2
│   ├── visual_anchor_refiner.py     # Phase 3
│   ├── quality_checker.py           # Phase 3
│   ├── character_comparator.py      # Phase 3
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── consistent_character_stage.py   # Phase 1
│   │   └── scene_description_engine_extension.py  # Phase 2
│   ├── pipeline_extension.py        # Phase 2
│   └── cli.py                       # All phases
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_reference_sheet.py      # Phase 1
│   ├── test_scene_renderer.py       # Phase 2
│   ├── test_quality_checker.py      # Phase 3
│   ├── test_cli.py                  # Phase 3
│   └── test_full_pipeline.py        # Phase 2
├── pyproject.toml
├── README.md
└── state/
    └── master_plan.md               # This file
```

---

## Integration with Existing Pipeline

### PipelineConfig Extension

```python
# In ai_movie_gen_suite.config (extended by this project)
class PipelineConfig(BaseModel):
    # ... existing fields ...
    character_image_provider: str = "kling"  # "kling" | "stable_diffusion"
    generate_reference_images: bool = True
    generate_scene_renders: bool = False
    refine_visual_anchors: bool = False
    quality_threshold: float = 0.85
```

### Pipeline Insertion Point

```python
# In ai_movie_gen_suite.pipeline.orchestrator (extended by this project)
class MovieGenerationPipeline:
    def run(self) -> PipelineResult:
        # ... existing steps ...
        beat_sheet = self._generate_beat_sheet()
        registry = self._generate_characters(beat_sheet)

        # ── NEW: Consistent Character Stage ──
        if self.config.generate_reference_images:
            registry = self._generate_character_references(registry)

        script = self._write_script(beat_sheet, registry)

        # ── NEW: Scene Character Renderer ──
        if self.config.generate_scene_renders:
            scene_descriptions = self._generate_scene_descriptions_with_renders(
                script, registry
            )
        else:
            scene_descriptions = self._generate_scene_descriptions(script)

        return self._format_output(script, beat_sheet, registry, scene_descriptions)
```

---

## Success Criteria

| Criterion | Measurement |
|---|---|
| Reference images generated for all characters | 100% of characters in registry have `visual_anchor_image_path` |
| Visual consistency maintained across scenes | Quality checker reports ≥ 85% similarity for all character renders |
| Pipeline runs without breaking existing functionality | All existing pipeline tests pass; new pipeline produces identical output when `generate_reference_images=False` |
| CLI works end-to-end | `ai-consistent-char run --title "..." --logline "..."` completes successfully |
| Provider abstraction works | Can swap between Kling and Stable Diffusion providers without code changes |

---

## Open Questions

1. **Kling API authentication**: Does Kling AI use API keys, OAuth, or another mechanism? Need to confirm before implementing `KlingImageProvider`.
2. **Reference image format**: Should we support multiple formats (PNG, JPEG, WebP) or standardize on PNG?
3. **Scene render resolution**: What resolution should per-scene renders be? (Suggested: 1024x1024 for web, 2048x2048 for print)
4. **Batch vs. individual generation**: Should we batch character reference images (one prompt, multiple characters) or generate individually? Individual is simpler but slower.
5. **Fallback strategy**: If image generation fails for one character, should the pipeline abort or continue with a placeholder?
