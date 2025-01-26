import os
import requests
import json
import urllib3
from gtts import gTTS
import base64
import io
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pathlib import Path
import re
import uuid

# Load environment variables from .env file
load_dotenv()
# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.NotOpenSSLWarning)

def invoke(action, params=None):
    """Function to send requests to the AnkiConnect API."""
    response = requests.post('http://localhost:8765', json.dumps({
        "action": action,
        "version": 6,
        "params": params or {}
    }), verify=False)  # Disable SSL verification to suppress warnings
    return response.json()

def store_media_file(filename, data):
    """
    Uploads a media file to Anki via AnkiConnect.

    :param filename: File name (e.g., 'unique_file_name.mp3')
    :param data: Binary file data
    :return: Upload result
    """
    encoded_data = base64.b64encode(data).decode('utf-8')
    result = invoke('storeMediaFile', {
        "filename": filename,
        "data": encoded_data
    })

    if 'error' in result and result['error']:
        print(f"Error uploading media file '{filename}': {result['error']}")
    else:
        print(f"Media file '{filename}' uploaded successfully.")

    return result

def add_note(deck_name, front, back):
    """
    Adds a new note to Anki.

    :param deck_name: Name of the deck
    :param front: Front field content
    :param back: Back field content
    :return: Add note result
    """
    note = {
        "deckName": deck_name,
        "modelName": "Basic",
        "fields": {
            "Front": front,
            "Back": back
        },
        "options": {
            "allowDuplicate": False
        },
        "tags": []
    }

    result = invoke('addNote', {
        "note": note
    })

    if 'error' in result and result['error']:
        print(f"Error adding note: {result['error']}")
    else:
        print(f"Note added successfully with ID: {result.get('result')}")

    return result

def generate_audio(text, lang='en'):
    """
    Generates TTS audio for the given text.

    :param text: Text to convert to audio
    :param lang: Language for TTS
    :return: Audio data in binary format
    """
    try:
        tts = gTTS(text=text, lang=lang)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_data = audio_buffer.getvalue()
        audio_buffer.close()
        return audio_data
    except Exception as e:
        print(f"Error generating audio for text '{text}': {e}")
        return None

def add_new_words_to_deck(deck_name):
    print("Adding new words from ./newWords/_.md")
    try:
        file_path = Path("./newWords/_.md")
        content = file_path.read_text(encoding="utf-8")
        entries = content.strip().split("\n\n")

        for entry in entries:
            lines = entry.strip().split("\n")
            if len(lines) < 2:
                print("Not enough lines in entry. Skipping...")
                continue

            front = lines[0].strip()          # English word
            back_translation = lines[1].strip()   # Translation

            # Generate TTS audio for the Front field
            audio_data_front = generate_audio(front)
            if audio_data_front:
                audio_filename_front = f"{uuid.uuid4()}_front.mp3"
                store_media_file(audio_filename_front, audio_data_front)
                front += f'\n[sound:{audio_filename_front}]'

            # Processing images and expressions
            images = []
            additional_lines = []

            for line in lines[2:]:
                img_match = re.match(r'!\[.*?\]\((.*?)\)', line)
                if img_match:
                    img_filename = img_match.group(1)
                    images.append(img_filename)
                else:
                    additional_lines.append(line)

            # Form the Back field
            back_parts = [back_translation]

            if images:
                for img in images:
                    try:
                        img_path = Path("./newWords") / img
                        if img_path.exists():
                            with open(img_path, "rb") as f:
                                img_data = f.read()

                            unique_filename = f"{uuid.uuid4()}_{img}"
                            back_parts.append(f'<br><br><img src="{unique_filename}">')
                            store_media_file(unique_filename, img_data)
                        else:
                            print(f"Image file '{img}' not found. Skipping upload.")
                    except Exception as e:
                        print(f"Error uploading image '{img}': {e}")

            if additional_lines:
                for line in additional_lines:
                    back_parts.append(f'<br><br>{line}')

            back_content = ''.join(back_parts)

            # Add the note
            add_note_result = add_note(deck_name, front, back_content)

            if add_note_result.get('error'):
                print(f"Error adding note: {add_note_result.get('error')}")
            else:
                print(f"Note added successfully with ID: {add_note_result.get('result')}")

            time.sleep(0.1)  # Short delay to avoid overloading AnkiConnect

    except Exception as e:
        print(f"Error reading or processing file: {e}")

def main():
    # Get the deck name from .env file or prompt the user
    deck_name = os.getenv('DECK_NAME')

    if not deck_name:
        print("Deck name not specified in the .env file. Exiting.")
        return

    # Add new words
    add_new_words_to_deck(deck_name)

    # process_existing_cards(deck_name)

if __name__ == "__main__":
    main()
