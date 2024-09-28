# Anki Audio Enhancer

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Requirements](#requirements)
- [License](#license)

## Overview

**Anki Audio Enhancer** is a Python script designed to streamline the process of adding audio to your Anki flashcards. Utilizing the power of [AnkiConnect](https://ankiweb.net/shared/info/2055492159) and [Google Text-to-Speech (gTTS)](https://pypi.org/project/gTTS/), this tool automatically generates audio files for the front side of each card in a specified deck and embeds them directly into your Anki notes. Enhance your learning experience by integrating auditory elements seamlessly into your study routine.

## Features

- **Dynamic Deck Selection:** Prompt users to select any deck within Anki for audio enhancement.
- **Automated Audio Generation:** Converts text from the front field of each card into speech using gTTS.
- **Media Management:** Automatically uploads generated audio files to Anki, avoiding duplicates.
- **HTML Parsing:** Strips HTML tags to ensure clean text-to-speech conversion.
- **Error Handling:** Robust mechanisms to handle potential issues during API interactions and audio generation.
- **Due Date Preservation:** Maintains the original due dates of cards after updates to avoid disrupting your study schedule.

## Installation

### Prerequisites

- **Python 3.7+**: Ensure you have Python installed. You can download it from [here](https://www.python.org/downloads/).
- **Anki**: Download and install Anki from [here](https://apps.ankiweb.net/).
- **AnkiConnect Add-on**: Install the AnkiConnect add-on by navigating to `Tools > Add-ons > Get Add-ons` in Anki and entering the code `2055492159`.

### Steps

1. **Clone the Repository**

   ```bash
   cd Anki-Audio-Enhancer
    ```
2.	**Create a Virtual Environment (Recommended)**

   ```bash
   python -m venv venv
   ```
    It’s good practice to use a virtual environment to manage dependencies.

3.	**Activate the Virtual Environment**

   - **Windows:**

     ```bash
     venv\Scripts\activate
     ```

   - **macOS/Linux:**

     ```bash
     source venv/bin/activate
     ```

4.	**Install Required Packages**

   ```bash
   pip install -r requirements.txt
   ```
   
# Usage
1.	Ensure Anki is Running
    Start Anki and make sure the AnkiConnect add-on is active.
2. Run the Script
    ```bash
    python anki_audio_enhancer.py
    ``` 
3.	Enter Deck Name
    When prompted, input the exact name of the deck you wish to enhance with audio.
4.	Process Execution
The script will:
	•	Retrieve all cards from the specified deck.
	•	Generate audio for the front side of each card.
	•	Upload the audio to Anki and embed it into the card’s front field.
	•	Preserve the original due dates of the cards.
	5.	Completion
Upon successful execution, your selected Anki deck will have audio files integrated into each card’s front field, enhancing your study sessions with auditory learning.

# License

This project is licensed under the MIT License. You are free to use, modify, and distribute this software as per the license terms.