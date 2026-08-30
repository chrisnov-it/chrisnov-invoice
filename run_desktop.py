from flaskwebgui import FlaskUI
from app import create_app
import os
import sys

# Initialize the Flask app
app = create_app()

if __name__ == "__main__":
    # Determine if we're running as a bundled executable
    if getattr(sys, 'frozen', False):
        # If running as .exe, use the path of the .exe
        base_dir = sys._MEIPASS
    else:
        # If running as .py, use the current directory
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # Configure FlaskUI
    # width and height can be adjusted as needed
    ui = FlaskUI(
        app=app,
        server="flask",
        width=1200,
        height=800,
        port=5005 # Use a different port to avoid conflicts
    )

    # Start the desktop application
    ui.run()
