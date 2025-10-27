import os
import sys
import time
from dotenv import load_dotenv
from pathlib import Path
import re
import uuid

from utils.anki import invoke, store_media_file, add_note
from utils.audio import generate_audio

# Load environment variables from .env file, allowing config to override system defaults
load_dotenv(sys.argv[1], override=True)

def add_new_words_to_deck(deck_name, new_words_path, limit, language, tld):
    print("Adding new words from ", new_words_path)
    try:
        file_path = Path(new_words_path)
        content = file_path.read_text(encoding="utf-8")
        entries = content.strip().split("\n\n")

        for entry in entries:
            lines = [ln.strip() for ln in entry.strip().split("\n") if ln.strip()]

            # Expecting at least: 1) front word, 2) example phrase, 3) translation
            if len(lines) < 3:
                print("Not enough lines in entry (need: word, phrase, translation). Skipping...")
                continue

            # Front: English word
            front = lines[0]  # keep exact text

            # Generate TTS for the Front field (word)
            audio_data_front = generate_audio(front, lang=language, tld=tld)
            if audio_data_front:
                audio_filename_front = f"{uuid.uuid4()}_front.mp3"
                store_media_file(audio_filename_front, audio_data_front)
                front += f'\n[sound:{audio_filename_front}]'

            # Back parts in the new order:
            # 1) English phrase (with TTS)
            # 2) Images (if any)
            # 3) Translation
            # 4) Additional lines (if any)

            phrase_en = lines[1]
            translation = lines[2]

            # Prepare containers
            images = []
            additional_lines = []

            # Parse remaining lines (from 4th line onward)
            for line in lines[3:]:
                img_match = re.match(r'!\[.*?\]\((.*?)\)', line)
                if img_match:
                    img_filename = img_match.group(1)
                    images.append(img_filename)
                else:
                    additional_lines.append(line)

            back_parts = []

            # (1) Phrase + TTS
            phrase_block = phrase_en
            audio_data_phrase = generate_audio(phrase_en, lang=language, tld=tld)
            if audio_data_phrase:
                audio_filename_phrase = f"{uuid.uuid4()}_phrase.mp3"
                store_media_file(audio_filename_phrase, audio_data_phrase)
                phrase_block += f'\n[sound:{audio_filename_phrase}]'
            back_parts.append(phrase_block)

            # (2) Images
            if images:
                for img in images:
                    try:
                        img_path = Path(os.path.dirname(new_words_path)) / img
                        if img_path.exists():
                            with open(img_path, "rb") as f:
                                img_data = f.read()
                            unique_filename = f"{uuid.uuid4()}_{img}"
                            # keep exact upload & embedding flow
                            store_media_file(unique_filename, img_data)
                            back_parts.append(f'<br><br><img src="{unique_filename}">')
                        else:
                            print(f"Image file '{img}' not found. Skipping upload.")
                    except Exception as e:
                        print(f"Error uploading image '{img}': {e}")

            # (3) Translation
            back_parts.append(f'<br><br>{translation}')

            # (4) Additional lines (if any)
            if additional_lines:
                for line in additional_lines:
                    back_parts.append(f'<br><br>{line}')

            back_content = ''.join(back_parts)

            # Add the note
            add_note_result = add_note(deck_name, front, back_content)

            # Small delay to avoid overloading AnkiConnect
            time.sleep(0.15)

    except Exception as e:
        print(f"Error reading or processing file: {e}")

def main():
    deck_name = os.getenv('DECK_NAME')
    new_words_path = os.getenv('NEW_WORDS_FILE_NAME')
    is_add_new = os.getenv('ADD_NEW')
    is_rewrite_old = os.getenv('REWRITE_OLD')
    limit = os.getenv('LIMIT')
    lang = os.getenv('LANG')
    tld = os.getenv('TLD')

    if not deck_name:
        print("Deck name not specified in the .env file. Exiting.")
        return

    if is_rewrite_old == 'True':
        print("Rewrite old is set - DISABLE")
    if is_add_new == 'True':
        if not new_words_path:
            print("Deck name not specified in the .env file. Exiting.")
            return
        add_new_words_to_deck(deck_name, new_words_path, limit, lang, tld)

    # process_existing_cards(deck_name)

if __name__ == "__main__":
    main()
