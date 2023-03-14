import os
import speech_recognition as sr
import logging

def recognize_speech_from_mic(iteration, SPEECH_DIR):
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    """Transcribe speech from recorded from `microphone`.

    Returns a dictionary with three keys:
    "success": a boolean indicating whether or not the API request was
               successful
    "error":   `None` if no error occured, otherwise a string containing
               an error message if the API could not be reached or
               speech was unrecognizable
    "transcription": `None` if speech could not be transcribed,
               otherwise a string containing the transcribed text
    """
    # check that recognizer and microphone arguments are appropriate type
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    # adjust the recognizer sensitivity to ambient noise and record audio
    # from the microphone

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=10)

    # set up the response object
    response = {
        "success": True,
        "error": None,
        "transcription": None
    }

    # try recognizing the speech in the recording
    # if a RequestError or UnknownValueError exception is caught,
    #     update the response object accordingly
    try:
        response["transcription"] = recognizer.recognize_google(audio)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    if response["error"] is None:
        with open(os.path.join(SPEECH_DIR,"story_{}_mc_response.wav".format(iteration)), "wb") as file:
            file.write(audio.get_wav_data())
            logging.info("Storing user response. Success.")
    else:
        response["transcription"] = """
        I want you to act as an interactive, immersive storyteller. 
        The story must consist of a narrator, a main character, and a sidekick.
        The narrator must speak in third person. The sidekick must speak directly to me in second person.
        You will come up with entertaining stories that are engaging, imaginative, captivating, thrilling, and suspenseful. 
        The story must have extremely detailed world building and be very descriptive. 
        I want the sidekick to have their own style and vocabulary befitting their role in the story. 
        Always put double double quotation mark quotes around the sidekick's text.
        Never put double or single quotation marks around narrator text. 
        Never put double or single quotation marks around the main character's text.
        Continue the story with great depth and immersiveness. Don't end the story.
        
        """
        logging.info("User response. Failed.")

    return response