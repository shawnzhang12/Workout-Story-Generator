import os
import logging
import speech_recognition as sr

def get_user_response(iteration: int, speech_dir: str, debug: bool = False) -> str:
    """
    Gets user speech input and returns the transcribed text.

    Parameters
    ----------
    iteration : int
        Current iteration count.
    speech_dir : str
        Directory path to save the speech file.
    debug : bool, optional
        If True, returns a default transcription.

    Returns
    -------
    str
        Transcribed user speech.
    """
    if debug:
        return "Let's continue. Don't end the story."

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=10)

    response = {"success": True, "error": None, "transcription": None}

    try:
        response["transcription"] = recognizer.recognize_google(audio)
    except sr.RequestError:
        response.update({"success": False, "error": "API unavailable"})
    except sr.UnknownValueError:
        response["error"] = "Unable to recognize speech"

    if response["error"] is None:
        file_path = os.path.join(speech_dir, f"story_{iteration}_mc_response.wav")
        with open(file_path, "wb") as file:
            file.write(audio.get_wav_data())
        logging.info("Storing user response. Success.")
    else:
        response["transcription"] = "Let's continue. Don't end the story."   
        logging.info("User response. Failed.")

    return response["transcription"] or "Let's continue. Don't end the story."