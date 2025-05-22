import os
import sys

import time
from dotenv import load_dotenv
from pathlib import Path
import re
import uuid

from utils.anki import store_media_file, add_note
from utils.audio import generate_audio

# Load environment variables from .env file
load_dotenv(sys.argv[1])

def add_new_words_to_deck(deck_name, new_words_path, language, tld):
    print("Adding new words from ", new_words_path)
    try:
        file_path = Path(new_words_path)
        content = file_path.read_text(encoding="utf-8")
        entries = content.strip().split("\n\n")

        for entry in entries:
            lines = entry.strip().split("\n")
            if len(lines) < 7:
                print("Not enough lines in entry. Skipping...")
                continue

            front = lines[0].strip()          # English word
            # Generate TTS audio for the Front field
            audio_data_front = generate_audio(front, lang=language, tld=tld)
            if audio_data_front:
                audio_filename_front = f"{uuid.uuid4()}_front.mp3"
                store_media_file(audio_filename_front, audio_data_front)
                front += f'\n[sound:{audio_filename_front}]'


            image_line = lines[1].strip()
            img_match = re.match(r'!\[.*?\]\((.*?)\)', image_line)
            image = img_match.group(1)

            word_image = ""
            word_description = lines[2].strip()
            word_examples = lines[3].strip()
            word_phrases = lines[4].strip()
            word_synonyms = lines[5].strip()
            word_translation = lines[6].strip()

            try:
                img_path = Path(os.path.dirname(new_words_path)) / image
                if img_path.exists():
                    with open(img_path, "rb") as f:
                        img_data = f.read()

                    unique_filename = f"{uuid.uuid4()}_{image}"
                    word_image = f'<img src="{unique_filename}">'
                    store_media_file(unique_filename, img_data)
                else:
                    print(f"Image file '{image}' not found. Skipping upload.")
            except Exception as e:
                print(f"Error uploading image '{image}': {e}")

            back_content = f"""
<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; border-radius: 12px; background: #1b1b1b; color: white; padding: 1em;">

  <div style="margin-bottom: 1em; font-weight: bold;">
    {word_description}
  </div>

  <div style="font-size: 0.85em; border-radius: 8px; padding: 0.65em 1em; background-color: #263543; margin-bottom: 0.75em; position: relative; color: #349ca7;">
    <div style="position: absolute; top: 0.2em; right: 0.2em; font-size: 0.6em; font-weight: bold; color: #0077cc;">💬</div>
    <i>{word_examples}</i>
  </div>

  <div style="font-size: 0.85em; border-radius: 8px; padding: 0.65em 1em; background-color: #222e1e; margin-bottom: 0.75em; position: relative; color: #6bb86b;">
    <div style="position: absolute; top: 0.2em; right: 0.2em; font-size: 0.6em; font-weight: bold; color: #2d8a34;">🧩</div>
    <i>{word_phrases}</i>
  </div>

  <div style="font-size: 0.85em; border-radius: 8px; padding: 0.65em 1em; background-color: #30253d;; margin-bottom: 0.75em; position: relative; color: #c76cc5;">
    <div style="position: absolute; top: 0.2em; right: 0.2em; font-size: 0.6em; font-weight: bold; color: #8e44ad;">🔁</div>
    <i>{word_synonyms}</i>
  </div>

  <div style="margin: 1em 0;">{word_image}</div>

  <details style="margin-top: 1em;">
    <summary style="cursor: pointer; color: #4a6373; font-weight: 500;">Translate</summary>
    <div style="margin-top: 0.5em;">{word_translation}</div>
  </details>

</div>
            """

            # Add the note
            add_note_result = add_note(deck_name, front, back_content)

            time.sleep(0.15)  # Short delay to avoid overloading AnkiConnect

    except Exception as e:
        print(f"Error reading or processing file: {e}")

def main():
    deck_name = os.getenv('DECK_NAME')
    new_words_path = os.getenv('NEW_WORDS_FILE_NAME')
    lang = os.getenv('LANG')
    tld = os.getenv('TLD')

    if not new_words_path or not deck_name:
        print("Deck name not specified in the .env file. Exiting.")
        return

    add_new_words_to_deck(deck_name, new_words_path, lang, tld)

if __name__ == "__main__":
    main()
