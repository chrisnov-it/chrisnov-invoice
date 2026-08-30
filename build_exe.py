import PyInstaller.__main__
import os
import sys

def build():
    # Application name
    app_name = "ChrisnovInvoice"
    
    # Path to the main script
    script_path = "run_desktop.py"
    
    # Determine search path for dependencies (venv)
    # Check for common venv folder names
    venv_path = None
    for folder in ['venv', '.venv', 'env']:
        path = os.path.join(os.getcwd(), folder, 'Lib', 'site-packages')
        if os.path.exists(path):
            venv_path = path
            break
    
    # Folders to include (format: 'source_path;destination_path')
    add_data = [
        ("app/templates;app/templates"),
        ("app/static;app/static"),
        ("app/translations;app/translations"),
    ]
    
    # PyInstaller arguments
    args = [
        script_path,
        "--name=" + app_name,
        "--onefile",
        "--windowed",
        "--clean",
        # Explicitly include these to prevent missing module errors
        "--hidden-import=flask",
        "--hidden-import=flask_sqlalchemy",
        "--hidden-import=flask_migrate",
        "--hidden-import=flask_babel",
        "--hidden-import=flask_mail",
        "--hidden-import=flask_session",
        "--hidden-import=reportlab",
        "--hidden-import=flaskwebgui",
        "--hidden-import=jinja2.ext",
    ]
    
    # Add venv site-packages to path if found
    if venv_path:
        print(f"Adding venv path to build: {venv_path}")
        args.append(f"--paths={venv_path}")
    
    for item in add_data:
        args.append(f"--add-data={item}")

    print(f"Building {app_name} desktop application...")
    PyInstaller.__main__.run(args)
    
    print("\nBuild complete! You can find the executable in the 'dist' folder.")

if __name__ == "__main__":
    build()
