import os
import subprocess
import sys

def compile_translations():
    """Compile .po files to .mo files using pybabel"""
    print("Compiling translations using pybabel...")
    try:
        # Use the current python interpreter to run pybabel if possible, 
        # or just call pybabel directly
        result = subprocess.run(
            [sys.executable, "-m", "babel.messages.frontend", "compile", "-d", "app/translations"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print("Translations compiled successfully!")
        else:
            print("Error compiling translations:")
            print(result.stderr)
            
            # Fallback to direct command if module run fails
            print("Attempting direct pybabel command...")
            subprocess.run(["pybabel", "compile", "-d", "app/translations"])
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    compile_translations()