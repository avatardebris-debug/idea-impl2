"""
pipeline/ollama_health.py
Ollama pre-flight and periodic heartbeat checks.
"""

from __future__ import annotations

import json
import os
import sys
import time

def _check_ollama_model(model: str) -> str:
    """Pre-flight check: verify Ollama is reachable and the model is available.

    Catches common misconfigurations (wrong model name, Ollama not running,
    model not on GPU) BEFORE starting agents, preventing silent hour-long
    failures.
    """
    import urllib.request
    import urllib.error
    base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    # Normalize: add http:// if missing, replace bind address with localhost
    if not base_url.startswith("http"):
        base_url = f"http://{base_url}"
    base_url = base_url.replace("://0.0.0.0", "://localhost")

    # 1. Check Ollama is running
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/tags", timeout=5)
        data = json.loads(resp.read())
    except Exception as e:
        print(f"\n  ❌ Ollama not reachable at {base_url}: {e}")
        print(f"     Start Ollama first: ollama serve &")
        sys.exit(1)
    # 2. Check model exists — resolve the EXACT canonical name from the API.
    # Ollama may normalize case (q4_K_M → q4_k_m) internally.
    # IMPORTANT: We do NOT do loose partial matching — "qwen3.6" must not
    # accidentally match "qwen3.5". Match must include both base AND tag.
    available = [m.get("name", "") for m in data.get("models", [])]

    # Try exact match first (case-insensitive)
    canonical = next((m for m in available if m.lower() == model.lower()), None)
    if canonical is None:
        # Case-insensitive match on full name including tag
        model_lower = model.lower()
        canonical = next(
            (m for m in available if m.lower() == model_lower),
            None,
        )

    if canonical is None:
        print(f"\n  ❌ Model '{model}' not found in Ollama.")
        print(f"     Available: {', '.join(available) or '(none)'}")
        print(f"     Pull it:   ollama pull {model}")
        sys.exit(1)

    if canonical != model:
        print(f"  Model name resolved: '{model}' -> '{canonical}' (using API canonical name)")
        model = canonical  # Use the exact name the API knows about

    # Also check and resolve PIPELINE_LIGHT_MODEL if set
    _light_model_env = os.environ.get("PIPELINE_LIGHT_MODEL", "").strip()
    if _light_model_env:
        _light_canonical = next((m for m in available if m.lower() == _light_model_env.lower()), None)
        if _light_canonical is None:
            _light_canonical = next((m for m in available if _light_model_env.lower() in m.lower()), None)
        
        if _light_canonical is None:
            print(f"  ⚠️  Light-tier model '{_light_model_env}' not found in Ollama. Unsetting PIPELINE_LIGHT_MODEL to fallback to primary model '{model}'.")
            if "PIPELINE_LIGHT_MODEL" in os.environ:
                del os.environ["PIPELINE_LIGHT_MODEL"]
        else:
            if _light_canonical != _light_model_env:
                print(f"  Light model name resolved: '{_light_model_env}' -> '{_light_canonical}'")
                os.environ["PIPELINE_LIGHT_MODEL"] = _light_canonical

    # Prevent Ollama from auto-pulling models during the pipeline run.
    # Without this, if any agent accidentally uses a wrong model name,
    # Ollama silently downloads it (23GB+) instead of erroring.
    os.environ.setdefault("OLLAMA_NO_PULL", "1")

    # 3. Warm up: trigger a tiny inference to load model into VRAM.
    # Check if the model is already loaded via /api/ps first.
    already_loaded = False
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/ps", timeout=5)
        ps_data = json.loads(resp.read())
        models_loaded = ps_data.get("models", [])
        for m in models_loaded:
            loaded_name = m.get("name", "")
            if loaded_name.lower() == model.lower() or model.lower() in loaded_name.lower() or loaded_name.lower() in model.lower():
                already_loaded = True
                break
    except Exception:
        pass

    if already_loaded:
        print(f"  Model:    {model} (already loaded in VRAM) ✅")
    else:
        # Use /api/chat with think:false — /api/generate with num_predict:5 returns
        # empty for thinking models because all tokens go to the <think> block.
        print(f"  Model:    {model} (warming up...)", end="", flush=True)
        try:
            req = urllib.request.Request(
                f"{base_url}/api/chat",
                data=json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": "/no_think say OK"}],
                    "stream": False,
                    "think": False,             # disable chain-of-thought for warmup
                    "keep_alive": -1,           # pin model in VRAM after warmup
                    "options": {"num_predict": 30},
                }).encode(),
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=300)  # 5 min — large models take time
            result = json.loads(resp.read())
            # Accept response from either message.content or thinking field
            content = (
                result.get("message", {}).get("content", "")
                or result.get("message", {}).get("thinking", "")
                or result.get("response", "")
            )
            if content.strip():
                print(" ✅")
            else:
                print(" ⚠️  (empty response — model may need restart)")
        except Exception as e:
            print(f" ⚠️  warmup failed: {e}")

    # 4. Check GPU allocation
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/ps", timeout=5)
        ps_data = json.loads(resp.read())
        models_loaded = ps_data.get("models", [])
        if models_loaded:
            for m in models_loaded:
                vram_gb = m.get("size_vram", 0) / 1e9
                total_gb = m.get("size", 0) / 1e9
                name = m.get("name", "?")
                if vram_gb > 0.5:
                    print(f"  GPU:      {name} — {vram_gb:.1f}GB VRAM ✅")
                elif total_gb > 0:
                    print(f"  ⚠️  GPU:   {name} — {vram_gb:.1f}GB VRAM / {total_gb:.1f}GB total — RUNNING ON CPU!")
                    print(f"             Pipeline will be ~10-20x slower than GPU.")
        else:
            print(f"  ⚠️  GPU:   No models loaded after warmup — check Ollama GPU config")
    except Exception:
        pass  # Non-critical

    # Evict any other models installed on this instance.
    # Vast.ai and RunPod templates often pre-load qwen3.5 or other models.
    # Removing them frees VRAM and prevents background processes from
    # accidentally triggering a load (which shows as "modified" in ollama list).
    # PIPELINE_LIGHT_MODEL is whitelisted so the 2B light-tier model coexists
    # with the primary heavy model without being evicted.
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/tags", timeout=5)
        tags = json.loads(resp.read()).get("models", [])
        model_base = model.split(":")[0].lower()

        # Build whitelist: primary model + optional light-tier model
        _light_model = os.environ.get("PIPELINE_LIGHT_MODEL", "").strip().lower()
        _light_base  = _light_model.split(":")[0] if _light_model else ""
        allowed_bases = {model_base}
        if _light_base:
            allowed_bases.add(_light_base)

        for m in tags:
            name = m.get("name", "")
            name_base = name.split(":")[0].lower()
            is_primary = name.lower() == model.lower()
            is_allowed = name_base in allowed_bases
            if not is_primary and not is_allowed:
                print(f"  Removing unintended model: {name}")
                import subprocess
                subprocess.run(["ollama", "rm", name], capture_output=True)
    except Exception:
        pass  # Non-critical — best effort cleanup


    return model  # Return canonical model name for caller to use


def _check_ollama_heartbeat(model: str, _last_ok: list = [0.0]) -> str:
    """Quick Ollama liveness check + keepalive ping. Returns status string.

    Only pings once every 5 minutes (tracked via _last_ok mutable default).
    If the model is IDLE (evicted from VRAM), sends a keepalive request to
    reload it so agents don't run on CPU.
    """
    now = time.time()
    if now - _last_ok[0] < 300:  # Only check every 5 min
        return ""
    _last_ok[0] = now

    import urllib.request
    base_url = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    if not base_url.startswith("http"):
        base_url = f"http://{base_url}"
    base_url = base_url.replace("://0.0.0.0", "://localhost")
    try:
        resp = urllib.request.urlopen(f"{base_url}/api/ps", timeout=5)
        ps_data = json.loads(resp.read())
        models = ps_data.get("models", [])
        if models:
            vram = models[0].get("size_vram", 0) / 1e9
            return f"gpu={vram:.0f}GB"
        else:
            # Model was evicted — send a keepalive ping to reload into VRAM
            try:
                import json as _json
                payload = _json.dumps({
                    "model": model,
                    "prompt": "",
                    "keep_alive": -1,   # never auto-evict
                    "stream": False,
                }).encode()
                req = urllib.request.Request(
                    f"{base_url}/api/generate",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=180)  # 3 min for 23GB model reload
                return "gpu=RELOADING"
            except Exception:
                return "gpu=IDLE"
    except Exception:
        return "gpu=ERR"
