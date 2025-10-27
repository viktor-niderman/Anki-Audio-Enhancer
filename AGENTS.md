# Repository Guidelines

## Project Structure & Module Organization
`main.py` orchestrates the CLI flow: reading `.env` settings, parsing Markdown word lists, and coordinating media uploads. Shared integrations live in `utils/`, with `anki.py` wrapping AnkiConnect calls and `audio.py` generating gTTS assets. Language assets reside under `words-<locale>/`, while `example-words-english/` provides starter content. Keep large media files alongside their source Markdown so relative paths resolve during ingestion.

## Build, Test, and Development Commands
Create an isolated environment before installing dependencies:
- `python -m venv venv` – prepare a local virtual environment.
- `source venv/bin/activate` (or `venv\Scripts\activate` on Windows) – activate the environment.
- `pip install -r requirements.txt` – install runtime libraries (requests, gTTS, dotenv, bs4).
Run the importer by pointing to a config file: `python main.py .env.english`. Launch Anki with AnkiConnect enabled first so API calls succeed.

## Coding Style & Naming Conventions
Follow standard PEP 8 with four-space indentation and descriptive, snake_case function names. Keep network helpers in `utils/` and limit new modules to single-responsibility utilities. Store secrets and deck configuration in uppercase `.env` keys; name locale-specific configs `.env.<language>`. When adding Markdown word lists, prefer lowercase filenames with hyphens and embed media using Markdown image syntax to keep parsing consistent.

## Testing Guidelines
There is no automated test suite yet; verify work by running `python main.py <env-file>` against a throwaway deck. Confirm that audio, translations, and optional images land in Anki as expected. For new helpers, add lightweight scripts or docstring examples that demonstrate usage, and document any manual validation steps in the pull request.

## Commit & Pull Request Guidelines
Commits in this repository are short, present-tense summaries (e.g., `add newWords`). Keep each commit focused on one change set. Pull requests should explain the motivation, outline manual test steps, and call out required `.env` updates or new word lists. If you modify media or deck structure, include before/after screenshots or Anki note counts to speed up review.

## Environment & Security Tips
Do not commit `.env.*` files or personal decks. AnkiConnect defaults to `localhost:8765`; update the port via environment variables when needed. Large audio or image assets should remain under version control only if they are reusable samples—otherwise document how to regenerate them.
