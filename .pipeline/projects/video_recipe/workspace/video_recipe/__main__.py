"""Entry point for running the Video Recipe Browser."""

import sys
from video_recipe.cli import main

if __name__ == "__main__":
    # If CLI arguments are provided, run the CLI
    if len(sys.argv) > 1:
        sys.exit(main(sys.argv[1:]))
    # Otherwise, start the web server
    import uvicorn
    from video_recipe.app import app
    uvicorn.run(app, host="0.0.0.0", port=8000)
