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


def get_deck_names():
    """Gets the list of all decks."""
    result = invoke('deckNames')
    if 'error' in result and result['error']:
        print(f"Error getting deck names: {result['error']}")
        return []
    return result.get('result', [])


def get_deck_cards(deck_name):
    """
    Gets the list of card IDs from the specified deck.

    :param deck_name: Name of the deck
    :return: List of card IDs
    """
    # Search for all cards in the deck
    result = invoke('findCards', {
        "query": f'deck:"{deck_name}"'
    })

    if 'error' in result and result['error']:
        print(f"Error getting cards: {result['error']}")
        return []

    card_ids = result.get('result', [])
    print(f"Found {len(card_ids)} cards in deck '{deck_name}'")
    print("Card IDs:", card_ids)

    return card_ids


def get_cards_info(deck_name):
    """
    Gets information about cards by their IDs.

    :param deck_name: Name of the deck
    :return: List of card information
    """
    card_ids = get_deck_cards(deck_name)

    if not card_ids:
        print("No cards to display.")
        return []

    result = invoke('cardsInfo', {
        "cards": card_ids
    })

    if 'error' in result and result['error']:
        print(f"Error getting card information: {result['error']}")
        return []

    return result.get('result', [])


def get_notes_info(note_ids):
    """
    Gets information about notes by their IDs.

    :param note_ids: List of note IDs
    :return: List of note information
    """
    if not note_ids:
        return []

    result = invoke('notesInfo', {
        "notes": note_ids
    })

    if 'error' in result and result['error']:
        print(f"Error getting note information: {result['error']}")
        return []

    return result.get('result', [])


def store_media_file(filename, data):
    """
    Uploads a media file to Anki via AnkiConnect.

    :param filename: File name (e.g., 'card_12345.mp3')
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


def update_note_field(note_id, field_name, new_value):
    """
    Updates a note field in Anki.

    :param note_id: Note ID
    :param field_name: Field name (e.g., 'Front')
    :param new_value: New field value
    :return: Update result
    """
    result = invoke('updateNoteFields', {
        "note": {
            "id": note_id,
            "fields": {
                field_name: new_value
            }
        }
    })

    if 'error' in result and result['error']:
        print(f"Error updating field '{field_name}' for note ID {note_id}: {result['error']}")
    else:
        print(f"Field '{field_name}' for note ID {note_id} updated successfully.")

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


def get_card_due(card_id):
    """
    Gets the current due date of a card.

    :param card_id: Card ID
    :return: Card 'due' value
    """
    result = invoke('cardsInfo', {
        "cards": [card_id]
    })

    if 'error' in result and result['error']:
        print(f"Error getting information for card ID {card_id}: {result['error']}")
        return None

    card_info = result.get('result', [])[0]
    due = card_info.get('due')
    return due


def set_card_due(card_id, due):
    """
    Sets the due date of a card.

    :param card_id: Card ID
    :param due: 'due' value to set
    :return: Update result
    """
    result = invoke('updateCard', {
        "card": card_id,
        "due": due
    })

    if 'error' in result and result['error']:
        print(f"Error updating due date for card ID {card_id}: {result['error']}")
    else:
        print(f"Due date for card ID {card_id} updated successfully.")

    return result


def strip_html(html_content):
    """
    Removes HTML tags from a string.

    :param html_content: String containing HTML tags
    :return: Clean text without HTML
    """
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def print_line():
    print("-" * 40)


def select_deck_name():
    # Display the list of available decks
    decks = get_deck_names()
    if not decks:
        print("Failed to get the list of decks.")
        return

    print("Available decks:")
    for deck in decks:
        print(f"- {deck}")
    print_line()

    deck_name = os.getenv('DECK_NAME')
    # Prompt the user to enter the deck name
    if not deck_name:
        deck_name = input("Please enter the deck name you want to process: ").strip()

    if not deck_name:
        print("No deck name entered. Exiting.")
        return

    if deck_name not in decks:
        print(f"Deck '{deck_name}' not found. Please check the deck name.")
        return
    return deck_name


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

            # Processing images and expressions
            images = []
            expressions = []
            additional_lines = []

            for line in lines[2:]:
                img_match = re.match(r'!\[.*?\]\((.*?)\)', line)
                if img_match:
                    img_filename = img_match.group(1)
                    images.append(img_filename)
                else:
                    # Check for expressions in ~ ~
                    expr_match = re.findall(r'~(.*?)~', line)
                    if expr_match:
                        expressions.extend(expr_match)
                        additional_lines.append(line)  # Save the line with the expression
                    else:
                        additional_lines.append(line)

            # Load images before adding the note
            for img in images:
                try:
                    img_path = Path("./newWords") / img
                    if img_path.exists():
                        with open(img_path, "rb") as f:
                            img_data = f.read()
                        store_media_file(img, img_data)
                    else:
                        print(f"Image file '{img}' not found. Skipping upload.")
                except Exception as e:
                    print(f"Error uploading image '{img}': {e}")

            # Form the Back field
            back_parts = [back_translation]

            if images:
                for img in images:
                    # Embed the image using HTML tag
                    back_parts.append(f'<br><br><img src="{img}">')

            if additional_lines:
                for line in additional_lines:
                    back_parts.append(f'<br><br>{line}')  # Keep ~ ~ around expressions

            back_content = ''.join(back_parts)

            # Add the note
            add_note_result = add_note(deck_name, front, back_content)

            # Check if the note was added successfully
            if add_note_result.get('error'):
                print(f"Error adding note: {add_note_result.get('error')}")
            else:
                print(f"Note added successfully with ID: {add_note_result.get('result')}")

            time.sleep(0.1)  # Short delay to avoid overloading AnkiConnect

    except Exception as e:
        print(f"Error reading or processing file: {e}")


def process_existing_cards(deck_name):
    print("Processing existing cards to add audio")
    cards_info = get_cards_info(deck_name)

    if not cards_info:
        print("No card information available.")
        return

    # Collect unique note IDs
    note_ids = list({card.get('note') for card in cards_info if 'note' in card})
    print("Note IDs:", note_ids)

    notes_info = get_notes_info(note_ids)

    # Create a dictionary for quick access to note information by ID
    notes_dict = {note['noteId']: note for note in notes_info}

    for card in cards_info:
        card_id = card.get('cardId', 'No ID')
        note_id = card.get('note')
        note = notes_dict.get(note_id)

        if not note:
            print(f"Note information not found for ID: {note_id}")
            continue

        fields = note.get('fields', {})

        # Swap Front and Back
        front_html = fields.get('Front', {}).get('value', 'No data')  # English word
        back_html = fields.get('Back', {}).get('value', 'No data')    # Translation and images

        print(f"Processing Card ID: {card_id}")
        print(f"Front (HTML): {front_html}")
        print(f"Back (HTML): {back_html}")

        # --- Processing Front Field ---
        # Check if Front already contains [sound:]
        if "[sound:" not in front_html:
            # Generate audio for Front
            front_text = strip_html(front_html)
            print(f"Front (Text): {front_text}")

            try:
                tts_front = gTTS(text=front_text, lang='en')
                audio_buffer_front = io.BytesIO()
                tts_front.write_to_fp(audio_buffer_front)
                audio_data_front = audio_buffer_front.getvalue()
                audio_buffer_front.close()
            except Exception as e:
                print(f"Error generating audio for Front of card ID {card_id}: {e}")
                print_line()
                continue

            # Create a unique filename for Front audio
            audio_filename_front = f"card_{card_id}_front.mp3"

            # Attempt to upload the media file
            try:
                store_media_file(audio_filename_front, audio_data_front)
            except Exception as e:
                print(f"Error uploading media file '{audio_filename_front}': {e}")
                print_line()
                continue

            # Add the sound tag to Front field
            updated_front = front_html + f'\n[sound:{audio_filename_front}]'

            # Update Front field in the note
            update_note_field(note_id, 'Front', updated_front)

        else:
            print("Front field already contains audio. Skipping Front field.")

        # --- Processing Expressions Wrapped in ~ ~ in Back Field ---
        # Find expressions wrapped in ~ ~
        expressions = re.findall(r'~(.*?)~', back_html)
        if expressions:
            for expr in expressions:
                print(f"Found expression to vocalize: {expr}")
                expr_text = strip_html(expr)

                try:
                    tts_expr = gTTS(text=expr_text, lang='en')
                    audio_buffer_expr = io.BytesIO()
                    tts_expr.write_to_fp(audio_buffer_expr)
                    audio_data_expr = audio_buffer_expr.getvalue()
                    audio_buffer_expr.close()
                except Exception as e:
                    print(f"Error generating audio for expression '{expr}' in card ID {card_id}: {e}")
                    continue

                # Create a unique filename for the expression audio
                safe_expr = re.sub(r'\W+', '_', expr_text)
                audio_filename_expr = f"card_{card_id}_expr_{safe_expr}.mp3"

                # Attempt to upload the media file
                try:
                    store_media_file(audio_filename_expr, audio_data_expr)
                except Exception as e:
                    print(f"Error uploading media file '{audio_filename_expr}': {e}")
                    continue

                # Create the sound tag
                sound_tag = f'[sound:{audio_filename_expr}]'
                # Replace ~expression~ with "expression [sound:file.mp3]"
                updated_back = back_html.replace(f'~{expr}~', f"{expr} {sound_tag}")

                # Update Back field in the note
                update_note_field(note_id, 'Back', updated_back)
        else:
            print("No expressions wrapped in ~ ~ found in Back field.")

        # Restore the due date
        due = get_card_due(card_id)
        if due is None:
            print(f"Failed to get the due date for card ID {card_id}. Skipping.")
            print_line()
            continue

        # Restore the due date of the card
        set_card_due(card_id, due)

        print_line()
        # Short delay to avoid overloading AnkiConnect
        time.sleep(0.1)


def main():
    # Get the deck name from .env file or prompt the user
    deck_name = select_deck_name()

    if not deck_name:
        print("Deck name not selected. Exiting.")
        return

    # Add new words
    add_new_words_to_deck(deck_name)

    # Process existing cards
    process_existing_cards(deck_name)


if __name__ == "__main__":
    main()