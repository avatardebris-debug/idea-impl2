"""CLIP embedding wrapper for computing image similarity."""

import torch
import clip as openai_clip
import numpy as np
from PIL import Image
import torchvision.transforms.functional as TF


# Cache the loaded model
_model = None
_device = None


def _get_model():
    """Lazy-load the CLIP model."""
    global _model, _device
    if _model is None:
        _device = torch.device("cpu")
        _model, _ = openai_clip.load("ViT-B/32", device=_device)
        _model.eval()
    return _model, _device


def _image_to_tensor(img: Image.Image) -> torch.Tensor:
    """Convert a PIL Image to a CLIP-compatible tensor."""
    model, device = _get_model()
    # CLIP expects 224x224 RGB images
    img_resized = img.resize((224, 224))
    tensor = TF.to_tensor(img_resized).unsqueeze(0).to(device)
    return tensor


def compute_clip_similarity(img_a: Image.Image, img_b: Image.Image) -> float:
    """Compute CLIP cosine similarity between two PIL Images.

    Args:
        img_a: First PIL Image.
        img_b: Second PIL Image.

    Returns:
        Cosine similarity in [0, 1]. 1.0 means identical embeddings.
    """
    model, device = _get_model()

    tensor_a = _image_to_tensor(img_a)
    tensor_b = _image_to_tensor(img_b)

    with torch.no_grad():
        embedding_a = model.encode_image(tensor_a)
        embedding_b = model.encode_image(tensor_b)

    # Normalize embeddings
    embedding_a = embedding_a / embedding_a.norm(p=2, dim=-1, keepdim=True)
    embedding_b = embedding_b / embedding_b.norm(p=2, dim=-1, keepdim=True)

    # Cosine similarity
    similarity = torch.dot(embedding_a.flatten(), embedding_b.flatten()).item()

    # Clamp to [0, 1]
    similarity = max(0.0, min(1.0, similarity))
    return similarity
