import os
import re
import random
import logging
import threading
from time import sleep, time
from subprocess import Popen
from TTS.api import TTS

from utils import *
from get_sound import *
from playsound import playsound
from get_workout import get_workout
from get_prompt import query_gpt
from speech_to_text import recognize_speech_from_mic

def separate_script(script):
    '''
    Separates the script into lines for the narrator, and lines for the sidekick, 
    TODO: assumes all quotes are sidekicks for now, can use gpt model to extract quotes later, dont forget to change temperature
    Returns list: [(line order number, voice actor #, actual line),...]
    '''
    # Remove headers before colon
    lines = script.split("\n")
    processed_lines = [re.sub(r".*?:", "", line) for line in lines]
    script = " ".join(processed_lines)
    script = script.lstrip("\"\n\'\r\t")
    script = script.replace("\n", "")
    
    lines = []
    count = 0
    start_quote = True
    current_substring = ""

    for char in script:
        if char == '"':
            if start_quote:
                if current_substring.strip() != "":
                    lines.append((count, 0, current_substring))
                    count += 1
                current_substring = ""
                start_quote = False
            else:
                if current_substring.strip() != "":
                    lines.append((count, 1, current_substring))
                    count += 1
                current_substring = ""
                start_quote = True
        else:
            current_substring += char

    if current_substring.strip() != "":
                    lines.append((count, 0, current_substring))        
    # 0 means narrator, 1 means sidekick
    # Return format [(line order number, voice actor #, actual line),...]
    logging.info("Lines: {}".format(lines))
    return lines

# Convert script to audio file with different voice parts
# Use multiprocessing to speed up text to speech conversions

@timing
def script_to_speech(lines, speech_dir, iteration_number, other_sounds = None):
    voices = {0: 'p257', 1: 'p263'}
    audio_files = []
    tts = TTS("tts_models/en/vctk/vits")
    for (order, voice, text) in lines:
        pid = voices[voice]
        output_file = "story_{}_{}_{}.wav".format(iteration_number, order, pid)
        tts.tts_to_file(text=text, speaker=pid, file_path= os.path.join(speech_dir, output_file))
        audio_files.append(os.path.join(speech_dir, output_file))
        

    if other_sounds is not None:
        audio_files.append(other_sounds)

    logging.info("Audio Files: {}".format(audio_files))
    for f in audio_files:
        assert os.path.exists(f)
    final_file = os.path.join(speech_dir, "story_{}_combined.wav".format(iteration_number))
    concatenate_audio_moviepy(audio_files, final_file)

    return final_file


def setup_workout(master_storyline, reps, exercise, i):
    sidekick_response = query_gpt(master_storyline + "\n" + SIDEKICK_WORKOUT_INTERJECTION.format(reps, exercise))
    logging.info("Sidekick Response {}: {}".format(i, sidekick_response))
    lines = separate_script(sidekick_response)
    sidekick_audio_file = script_to_speech(lines,SPEECH_DIR,str(i)+"s",other_sounds=os.path.join(SOUNDS_DIR, "start_tone2.wav"))
    return sidekick_response, sidekick_audio_file


### MAIN ###
def main(workout_file=None, mode=["manual", "semi-auto", "auto"], timed=[True, False]):
    
    # debugging variables, count is not needed
    beginning = True
    count = 0
    main_character_lines =[]

    ## TODO: Handle seconds in workouts
    workout = get_workout(workout_file, shuffle=False)

    # Use 1 indexing as beginning starts at 0
    for i, w in enumerate(workout, 1):
        exercise = w[0]
        reps = w[1]
        rest_time = w[2]

        if beginning:
            #  Begin story
            prompt = CONST_BEGINNING
            master_storyline = query_gpt(prompt)

            logging.info("Storyline 0: {}".format(master_storyline))
            lines = separate_script(master_storyline)
            print(master_storyline)

            audiofile_start = script_to_speech(lines,SPEECH_DIR,0,other_sounds=os.path.join(SOUNDS_DIR, "start_tone1.wav"))
            
            #  Prep workout response
            workout_setup_thread = ThreadWithReturnValue(target=setup_workout, args=(master_storyline, reps, exercise, 0))
            workout_setup_thread.start()

            #  Play story file
            playsound(audiofile_start)

            beginning = False

        if mode == "manual":
            stop_event = threading.Event()
            #waiting_thread = threading.Thread(target=play_waiting, args=(os.path.join(SOUNDS_DIR, "waiting.wav"), stop_event))
            waiting_thread = threading.Thread(target= (lambda: playsound(os.path.join(SOUNDS_DIR, "waiting.wav"))))
            waiting_thread.start()

            answer = recognize_speech_from_mic(i, SPEECH_DIR)

            ## TODO: handle exception when no answer is received within 20 seconds, probably auto generate/continue story
            logging.info("Answer has been accepted from mic.")
            stop_event.set()
            waiting_thread.join()

            if answer["transcription"]:
                main_character_response = answer["transcription"]
                main_character_lines.append(main_character_response)
                logging.info("Main character Response: {}".format(main_character_response))
            else: 
                print("ERROR: {}".format(answer["error"]))
                return Exception

            sidekick_response, sidekick_audio_file = workout_setup_thread.join()
            playsound(sidekick_audio_file)

            # play workout music and process answer
            #  TODO: Listen specifically for "I'm done", but now just wait 20 seconds
            workout_time = 20
            working_thread = threading.Thread(target=play_working, args=(os.path.join(SOUNDS_DIR, "fast_workout.wav"), workout_time))
            working_thread.start()

            master_storyline += "\nMain Character: " + main_character_response
            master_storyline += "\nSidekick: " + sidekick_response

            gpt_output = query_gpt(master_storyline + "\n" + main_character_response + "\n" + sidekick_response + "\n" + 
            """Continue the story centered around the main character's response with dialogue between the narrator and the sidekick now that the workout is done.
            Always put double quotes around the sidekick's lines. Never put quotes around narrator text.
            Don't end the story. End output with the sidekick asking me what to do next.""")   
            logging.info("Storyline {}: {}".format(i, gpt_output))
            master_storyline += "\n" + gpt_output

            lines = separate_script(gpt_output)
            audiofile = script_to_speech(lines,SPEECH_DIR,i,other_sounds=os.path.join(SOUNDS_DIR, "start_tone1.wav"))

            workout_setup_thread = ThreadWithReturnValue(target=setup_workout, args=(master_storyline, reps, exercise, i))
            workout_setup_thread.start()

            working_thread.join()
            playsound(r"{}".format(audiofile))
            # END MANUAL

        elif mode == "semi-auto":
            return NotImplementedError
        else:  # mode == "auto"
            return NotImplementedError


    conclusion = query_gpt(prompt + "Conclude the story")
    master_storyline += conclusion
    lines = separate_script(gpt_output)
    conclusion = script_to_speech(lines,SPEECH_DIR,i+1)
    playsound(conclusion)
    with open (os.path.join(OUTPUT_DIR, "complete_storyline.txt"), "wb") as f:
        f.write(master_storyline)     
    print("The End")      


if __name__ == '__main__':

    CONST_BEGINNING = """I want you to act as an interactive storyteller, like a dungeon master from Dungeon & Dragons. 
    The story must consist of a narrator, a main character, and a sidekick.
    The narrator must speak in third person. The sidekick must speak directly to me in second person.
    You will come up with entertaining stories that are engaging, imaginative and captivating. 
    The story must have extremely detailed world building and be very descriptive. 
    I want the sidekick to have their own style and vocabulary befitting their role in the story. Always put double quotes around the sidekick's lines.
    Never put quotes around narrator text. Never put quotes around the main character's text.
    I am the main character. Stop text generation when it is the main character's turn to speak. 
    The starting information is {}. Begin the story introduction with the narrator. End the output with the sidekick asking me what to do next."
    """

    SIDEKICK_WORKOUT_INTERJECTION = """
    Assume that the sidekick asked the main character "What to do next?". 
    Write a response from the sidekick that agrees with whatever answer and continues the story by motivating the main character to do {} {}.
    Always put double quotes around the sidekick's lines.
    Never put quotes around narrator text.
    End with the sidekick giving motivation for the main character to start right now!.
    I want the sidekick to have their own style and vocabulary befitting their role in the story.
    """

    OUTPUT_DIR, SOUNDS_DIR, SPEECH_DIR = folder_creation()
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', filename=os.path.join(OUTPUT_DIR, "logfile.log"), datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

    workout_file = "inputs/workout1.csv"
    starting_prompt = """I am John, a knight living in the kingdom of Larion. I have a steel sword and a wooden shield. I am on a quest to defeat the evil dragon of Larion."""
    CONST_BEGINNING = CONST_BEGINNING.format(starting_prompt)

    main(workout_file=workout_file, mode="manual")
