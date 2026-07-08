import os
import sys
sys.path.append(r"C:\Users\LLM-Test\Documents\agentsong")
from readers.opencode import list_sessions

# Check if the opencode.db file exists
db_path = r"C:\Users\LLM-Test\.local\share\opencode\opencode.db"
if os.path.exists(db_path):
    sessions = list_sessions(db_path, 20)
    print("Available opencode sessions:")
    for i, session in enumerate(sessions, 1):
        print(f"{i}. {session['id']}")
else:
    print(f"SQLite file not found: {db_path}")
    # Check what files are in the directory
    if os.path.exists(r"C:\Users\LLM-Test\.local\share\opencode"):
        files = os.listdir(r"C:\Users\LLM-Test\.local\share\opencode")
        print("Files in directory:")
        for file in files:
            print(f" - {file}")
