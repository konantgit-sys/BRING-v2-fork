"""Direct launcher — bypasses broken CLI serve command."""
import sys
import os

# Ensure we're in the project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from world_explorer.api import app
import uvicorn

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8098
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
