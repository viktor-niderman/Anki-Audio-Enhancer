import requests
import json
import urllib3
from gtts import gTTS
import base64
import io
import time
from bs4 import BeautifulSoup

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
    Gets the list of cards from the specified deck.

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


def get_cards_info(card_ids):
    """
    Gets information about cards by their IDs.

    :param card_ids: List of card IDs
    :return: List of card information
    """
    if not card_ids:
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


def media_exists(filename):
    """
    Checks if a media file exists in Anki.

    :param filename: File name
    :return: True if file exists, else False
    """
    result = invoke('mediaFiles')
    if 'error' in result and result['error']:
        print(f"Error getting media files list: {result['error']}")
        return False
    media_files = result.get('result', [])
    return filename in media_files


def main():
    # Display the list of available decks
    decks = get_deck_names()
    if not decks:
        print("Failed to get the list of decks.")
        return

    print("Available decks:")
    for deck in decks:
        print(f"- {deck}")
    print("-" * 40)

    # Prompt the user to enter the deck name
    deck_name = input("Please enter the deck name you want to process: ").strip()

    if not deck_name:
        print("No deck name entered. Exiting.")
        return

    if deck_name not in decks:
        print(f"Deck '{deck_name}' not found. Please check the deck name.")
        return

    card_ids = get_deck_cards(deck_name)

    if not card_ids:
        print("No cards to display.")
        return

    cards_info = get_cards_info(card_ids)

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

        # Assume that fields are named 'Front' and 'Back'
        front_html = fields.get('Front', {}).get('value', 'No data')
        back = fields.get('Back', {}).get('value', 'No data')

        print(f"Processing Card ID: {card_id}")
        print(f"Front (HTML): {front_html}")
        print(f"Back: {back}")

        # Check if the 'Front' field already contains the [sound:] tag
        if "[sound:" in front_html:
            print("Audio already added for this card. Skipping.")
            print("-" * 40)
            continue

        # Strip HTML tags from the 'Front' field
        front_text = strip_html(front_html)
        print(f"Front (Text): {front_text}")

        # Generate audio for the cleaned text
        try:
            tts = gTTS(text=front_text, lang='en')
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_data = audio_buffer.getvalue()
            audio_buffer.close()
        except Exception as e:
            print(f"Error generating audio for card ID {card_id}: {e}")
            print("-" * 40)
            continue

        # Create a unique filename for the audio
        audio_filename = f"card_{card_id}.mp3"

        # Check if the media file already exists
        if media_exists(audio_filename):
            print(f"Media file '{audio_filename}' already exists. Skipping upload.")
            # Add the sound tag to the 'Front' field
            updated_front = front_html + f'\n[sound:{audio_filename}]'
            update_note_field(note_id, 'Front', updated_front)
            print("-" * 40)
            continue

        # Upload the audio to Anki
        store_media_file(audio_filename, audio_data)

        # Add the sound tag to the 'Front' field
        updated_front = front_html + f'\n[sound:{audio_filename}]'

        # Update the 'Front' field in the note
        update_note_field(note_id, 'Front', updated_front)

        # Get the current due date of the card
        due = get_card_due(card_id)
        if due is None:
            print(f"Failed to get the due date for card ID {card_id}. Skipping.")
            print("-" * 40)
            continue

        # Restore the due date of the card
        set_card_due(card_id, due)

        print("-" * 40)
        # Add a short delay to avoid overloading AnkiConnect
        time.sleep(0.1)


if __name__ == "__main__":
    main()