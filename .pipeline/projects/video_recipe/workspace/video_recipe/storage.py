"""In-memory store for recipes and annotations."""

import uuid
from typing import Optional

from video_recipe.models import Recipe, Video


class RecipeStore:
    """In-memory store for recipes and annotations."""

    def __init__(self):
        self._videos: dict[str, Video] = {}
        self._recipes: dict[str, Recipe] = {}
        self._annotations: dict[str, list[dict]] = {}

    def add_video(self, video: Video) -> str:
        """Add a video to the store.

        Args:
            video: Video object to add.

        Returns:
            The video_id of the added video.
        """
        self._videos[video.video_id] = video
        return video.video_id

    def add_recipe(self, video_id: str, recipe: Recipe) -> str:
        """Add a recipe to the store.

        Args:
            video_id: The video_id this recipe belongs to.
            recipe: Recipe object to add.

        Returns:
            The recipe_id of the added recipe.
        """
        recipe_id = str(uuid.uuid4())
        self._recipes[recipe_id] = recipe
        # Ensure the video exists in the store with task_type from recipe
        if video_id not in self._videos:
            self._videos[video_id] = Video(
                video_id=video_id,
                filename="",
                task_type=getattr(recipe, 'task_type', None) or recipe.task_type,
                duration=None,
            )
        return recipe_id

    def get_recipe(self, recipe_id: str) -> Optional[dict]:
        """Get a recipe by ID.

        Args:
            recipe_id: The recipe_id to look up.

        Returns:
            Recipe dict or None if not found.
        """
        recipe = self._recipes.get(recipe_id)
        if recipe is None:
            return None
        return self._recipe_to_dict(recipe)

    def get_all_videos(self) -> list[dict]:
        """Get all videos as dicts.

        Returns:
            List of video dicts.
        """
        return [self._video_to_dict(v) for v in self._videos.values()]

    def search_by_task_type(self, task_type: str) -> list[dict]:
        """Search recipes by task type.

        Args:
            task_type: The task type to search for.

        Returns:
            List of matching recipe dicts.
        """
        results = []
        for recipe_id, recipe in self._recipes.items():
            # Check if video exists and matches task_type
            video = self._videos.get(recipe.video_id)
            if video and video.task_type == task_type:
                results.append(self._recipe_to_dict(recipe))
            elif not video:
                # If no video exists, check if recipe has task_type attribute
                if hasattr(recipe, 'task_type') and recipe.task_type == task_type:
                    results.append(self._recipe_to_dict(recipe))
        return results

    def get_annotations(self, recipe_id: str) -> list[dict]:
        """Get annotations for a recipe.

        Args:
            recipe_id: The recipe_id to look up.

        Returns:
            List of annotation dicts.
        """
        return self._annotations.get(recipe_id, [])

    def add_annotation(self, recipe_id: str, step_index: int, user_note: str) -> None:
        """Add an annotation to a recipe.

        Args:
            recipe_id: The recipe_id to annotate.
            step_index: The step index to annotate.
            user_note: The annotation text.
        """
        if recipe_id not in self._annotations:
            self._annotations[recipe_id] = []
        self._annotations[recipe_id].append({
            "step_index": step_index,
            "user_note": user_note,
        })

    def clear(self) -> None:
        """Clear all data from the store."""
        self._videos.clear()
        self._recipes.clear()
        self._annotations.clear()

    def _video_to_dict(self, video: Video) -> dict:
        """Convert a Video object to a dict."""
        return {
            "video_id": video.video_id,
            "filename": video.filename,
            "task_type": video.task_type,
            "duration": video.duration,
        }

    def _recipe_to_dict(self, recipe: Recipe) -> dict:
        """Convert a Recipe object to a dict."""
        # Try to get task_type from video if available
        task_type = None
        video = self._videos.get(recipe.video_id)
        if video:
            task_type = video.task_type
        elif hasattr(recipe, 'task_type'):
            task_type = recipe.task_type

        return {
            "recipe_id": next(
                rid for rid, r in self._recipes.items() if r is recipe
            ),
            "video_id": recipe.video_id,
            "title": recipe.title,
            "summary": recipe.summary,
            "task_type": task_type,
            "steps": [
                {
                    "step_index": step.step_index,
                    "description": step.description,
                    "timestamp": step.timestamp,
                    "inferred_tools": step.inferred_tools,
                    "inferred_materials": step.inferred_materials,
                }
                for step in recipe.steps
            ],
        }
