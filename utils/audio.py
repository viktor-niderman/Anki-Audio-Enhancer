from gtts import gTTS
import io

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