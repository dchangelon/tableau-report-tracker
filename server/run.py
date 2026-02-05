"""Simple runner script for the Flask server."""

import argparse
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.app import create_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tableau Report Tracker API Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to run on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    app = create_app()
    print(f"Starting server on http://localhost:{args.port}")
    print("Press Ctrl+C to stop")
    app.run(host="0.0.0.0", port=args.port, debug=args.debug)
