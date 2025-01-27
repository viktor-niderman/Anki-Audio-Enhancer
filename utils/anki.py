import requests
import json
import base64

def invoke(action, params=None):
    """Function to send requests to the AnkiConnect API."""
    response = requests.post('http://localhost:8765', json.dumps({
        "action": action,
        "version": 6,
        "params": params or {}
    }))
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