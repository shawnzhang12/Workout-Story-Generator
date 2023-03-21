import os
import speech_recognition as sr
import logging
import prompt_constants

def get_user_response(iteration, SPEECH_DIR, debug=False):
    return "Let's continue. Don't end the story."  
    if debug:
        response = {
            "transcription": "Let's continue. Don't end the story."  
        }
        return response

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")
    
    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

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
        response["transcription"] = "Let's continue. Don't end the story."   
        logging.info("User response. Failed.")

    if response["transcription"] == "":
        response = {
            "transcription": "Let's continue. Don't end the story."  
        }

    return response["transcription"]

def loop_for_finish():
    pass
