# config.py

import os

def load_token(file_path: str) -> str:
    """Load the bot token from a text file or fall back to an environment variable."""
    try:
        # Attempt to read the token from the file
        with open(file_path, 'r') as file:
            token = file.read().strip()
        return token
    except FileNotFoundError:
        print(f"Token file not found: {file_path}")
        return ""
    except Exception as e:
        print(f"An error occurred while reading the token file: {e}")
        return ""

# Path to your token file
TOKEN_FILE_PATH = '.token.txt'
TOKEN = load_token(TOKEN_FILE_PATH)

# If TOKEN is empty, fallback to the environment variable
if not TOKEN:
    TOKEN = os.getenv('TOKEN')
    if TOKEN:
        print("Token loaded from environment variable.")
    else:
        print("Bot token not found. Please ensure the TOKEN environment variable is set.")
