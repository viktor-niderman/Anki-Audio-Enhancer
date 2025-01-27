import os

import time
from dotenv import load_dotenv
from pathlib import Path
import re
import uuid

from utils.anki import invoke, store_media_file, add_note
from utils.audio import generate_audio

# Load environment variables from .env file
load_dotenv()

def add_new_words_to_deck(deck_name, new_words_path, limit, language):
    print("Adding new words from ", new_words_path)
    try:
        file_path = Path(new_words_path)
        content = file_path.read_text(encoding="utf-8")
        entries = content.strip().split("\n\n")

        for entry in entries:
            lines = entry.strip().split("\n")
            if len(lines) < 2:
                print("Not enough lines in entry. Skipping...")
                continue

            front = lines[0].strip()          # English word
            # Generate TTS audio for the Front field
            audio_data_front = generate_audio(front)
            if audio_data_front:
                audio_filename_front = f"{uuid.uuid4()}_front.mp3"
                store_media_file(audio_filename_front, audio_data_front)
                front += f'\n[sound:{audio_filename_front}]'


            back_translation = lines[1].strip()   # Translation

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
                        img_path = Path(os.path.dirname(new_words_path)) / img
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

            time.sleep(0.15)  # Short delay to avoid overloading AnkiConnect

    except Exception as e:
        print(f"Error reading or processing file: {e}")

def main():
    deck_name = os.getenv('DECK_NAME')
    new_words_path = os.getenv('NEW_WORDS_FILE_NAME')
    is_add_new = os.getenv('ADD_NEW')
    is_rewrite_old = os.getenv('REWRITE_OLD')
    limit = os.getenv('LIMIT')
    language = os.getenv('LANGUAGE')

    if not deck_name:
        print("Deck name not specified in the .env file. Exiting.")
        return

    if is_rewrite_old == 'True':
        print("Rewrite old is set - DISABLE")
    if is_add_new == 'True':
        if not new_words_path:
            print("Deck name not specified in the .env file. Exiting.")
            return
        add_new_words_to_deck(deck_name, new_words_path, limit, language)


    # Add new words


    # process_existing_cards(deck_name)

if __name__ == "__main__":
    main()
