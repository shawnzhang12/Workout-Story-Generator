import os
import re
import logging
import faulthandler
import threading
import multiprocessing
from multiprocessing import Process
from multiprocessing.pool import Pool
from TTS.api import TTS

from utils import *
from get_sound import *
from playsound import playsound
from get_workout import get_workout
from get_prompt import query_gpt
from speech_to_text import recognize_speech_from_mic
import prompt_constants


def separate_script(script):
    '''
    Separates the script into lines for the narrator, and lines for the sidekick, 
    TODO: assumes all quotes are sidekicks for now, can use gpt model to extract quotes later
    Returns list: [(line order number, voice actor #, actual line),...]
    '''
    # Remove headers before colon
    lines = script.split("\n")
    processed_lines = [re.sub(r".*?:", "", line) for line in lines]
    processed_lines = [re.sub(r'[-:;]', ',', line) for line in processed_lines]
    script = " ".join(processed_lines)
    script = script.lstrip("\"\n\'\r\t")
    script = script.replace("\n", "")
    if script[0] == '"' and script.count('"') % 2 == 1:  # I Don't get why it adds a double quote at the beginning
        script = script[1:]
    lines = []
    count = 0
    start_quote = True
    current_substring = ""

    for char in script:
        if char == '"':
            if start_quote:
                if current_substring.strip(" ") != "":
                    lines.append((count, 0, current_substring))
                    count += 1
                current_substring = ""
                start_quote = False
            else:
                if current_substring.strip(" ") != "":
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
    for line in lines:
        if line[1] == 0:
            logging.info("Line {} voiced by NARRATOR:  {}".format(line[0], line[2]))
        else:  # line[1] == 1
            logging.info('Line {} voiced by SIDEKICK: "{}"'.format(line[0], line[2]))
    return lines

# Convert script to audio file with different voice parts
# Use multiprocessing to speed up text to speech conversions
def tts_generate_audio(args):
    tts = TTS("tts_models/en/vctk/vits", gpu=args[3])
    tts.tts_to_file(text=args[0], speaker=args[1], file_path=args[2])


#@timing
def script_to_speech(lines, speech_dir, iteration_number, other_sounds=None, parallel=True, gpu=False):
    voices = {0: 'p267', 1: 'p273', 2: 'p330', 3:'p234', 4:'230'}
    audio_files = []
    tts = TTS("tts_models/en/vctk/vits", gpu=gpu)
    if not parallel:
         for (order, voice, text) in lines:
            pid = voices[voice]
            output_file = "story_{}_{}_{}.wav".format(iteration_number, order, pid)
            tts.tts_to_file(text=text, speaker=pid, file_path=os.path.join(speech_dir, output_file))
            audio_files.append(os.path.join(speech_dir, output_file))
    else:
        args = []
        for (order, voice, text) in lines:
            pid = voices[voice]
            output_file = "story_{}_{}_{}.wav".format(iteration_number, order, pid)
            args.append((text, pid, os.path.join(speech_dir, output_file),gpu))
            audio_files.append(os.path.join(speech_dir, output_file))
        
        with Pool(multiprocessing.cpu_count()) as pool:
            pool.map(tts_generate_audio, args)
        pool.close()
        pool.join()

    if other_sounds is not None:
        audio_files.append(other_sounds)

    logging.info("Audio Files: {}".format(audio_files))
    for f in audio_files:
        assert os.path.exists(f)
    final_file = os.path.join(speech_dir, "story_{}_combined.wav".format(iteration_number))
    concatenate_audio_moviepy(audio_files, final_file)

    return final_file


def setup_workout(master_storyline, reps, exercise, i, send_end, SPEECH_DIR=None, SOUNDS_DIR=None, gpu=False, sidekick_word_limit=0):
    SIDEKICK_WORKOUT_INTERJECTION = """
    Assume that the sidekick asked the main character "What to do next?" and is given a reply back. 
    Write a response from the sidekick that agrees with the main character ambiguously and 
    continues the story by motivating the main character to do {} {}.
    Always put double quotes around the sidekick's lines.
    Never put quotes around narrator text.
    End with the sidekick giving motivation for the main character to start right now!.
    I want the sidekick to have their own style and vocabulary befitting their role in the story. 
    """

    if sidekick_word_limit != 0:
        LIMIT_WORDS = " Limit the output to around {} words.".format(sidekick_word_limit)
        SIDEKICK_WORKOUT_INTERJECTION.append(LIMIT_WORDS)

    response = query_gpt(master_storyline + "\n" + SIDEKICK_WORKOUT_INTERJECTION.format(reps, exercise), temperature=0.7, response_length=128)
    logging.info("Sidekick Response {}: {}".format(i, response))
    lines = separate_script(response)
    audio_file = script_to_speech(lines,SPEECH_DIR,str(i)+"s",other_sounds=os.path.join(SOUNDS_DIR, "start_tone2.wav"), gpu=gpu)
    send_end.send((response, audio_file))


def start_story_generation(mode, starting_prompt, workout_input, gpu=False, verbs=False):

    OUTPUT_DIR, SOUNDS_DIR, SPEECH_DIR = folder_creation()
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', filename=os.path.join(OUTPUT_DIR, "logfile.log"), datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
  
    workout = get_workout(workout_input, shuffle=False)
    logging.info("Workout: {}".format(workout))

    (exercise, reps, rest_time) = workout[0]
    logging.info("Current workout is {} {}.".format(reps, exercise))
    iteration_word_count = 0
    main_character_lines =[]

    ### BEGIN WORKOUT STORY GENERATION
    if mode == "manual":
        CONST_BEGINNING = prompt_constants.CONST_BEGINNING.format(starting_prompt)
        master_storyline = query_gpt(CONST_BEGINNING)
    else:
        master_storyline = query_gpt(prompt_constants.CONST_BEGINNING_AUTO.format(starting_prompt))

    logging.info("Storyline 0: {}".format(master_storyline))
    lines = separate_script(master_storyline.strip("\n\r\"\'"))

    audiofile_start = script_to_speech(lines,SPEECH_DIR,0,other_sounds=os.path.join(SOUNDS_DIR, "start_tone1.wav"), gpu=gpu)
            
    #  Prep workout response
    recv_end, send_end = multiprocessing.Pipe(False)
    workout_setup_process = Process(target=setup_workout, args=(master_storyline, reps, exercise, 0, send_end, SPEECH_DIR, SOUNDS_DIR, gpu))
    workout_setup_process.start()

    #  Play starting story file
    playsound(audiofile_start)

    ### ITERATE THROUGH WORKOUTS
    for i in range(1, len(workout)+1):

        if mode == "interactive":
            stop_event = threading.Event()
            faulthandler.enable()
            waiting_thread = threading.Thread(target=play_waiting, args=(os.path.join(SOUNDS_DIR, "waiting.wav"), stop_event))
            waiting_thread.start()
            answer = recognize_speech_from_mic(i-1, SPEECH_DIR)

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
                exit()   

            workout_setup_process.join()

            sidekick_workout_response, sidekick_audio_file = recv_end.recv()
            workout_response_word_count = len(sidekick_workout_response.split())


            playsound(sidekick_audio_file)

            # play workout music and process answer
            # TODO: Listen specifically for "I'm done", but now just wait 20 seconds
            workout_time = 25
            working_thread = threading.Thread(target=play_working, args=(os.path.join(SOUNDS_DIR, "fast_workout.wav"), workout_time))
            working_thread.start()

            # Add responses to storyline
            master_storyline += "\nMain Character: " + main_character_response
            master_storyline += "\nSidekick: " + sidekick_workout_response


            if i == len(workout):
                working_thread.join()
                break

            # Query GPT for the continuation of the story
            if iteration_word_count != 0:
                word_count_left = round((iteration_word_count - workout_response_word_count) / 10) * 10
                WORD_LIMIT_PROMPT = "Limit the output to around {} words.".format(word_count_left)
            gpt_output = query_gpt(master_storyline + prompt_constants.CONTINUE_PROMPT + WORD_LIMIT_PROMPT)   
            logging.info("Storyline {}: {}".format(i, gpt_output))
            master_storyline += "\n" + gpt_output

            # Process and prepare audio file for continued story
            lines = separate_script(gpt_output)
            audiofile = script_to_speech(lines,SPEECH_DIR,i,other_sounds=os.path.join(SOUNDS_DIR, "start_tone1.wav"), gpu=gpu)

            # Begin processing the 'sidekick yes good plan response with workout' before playing the continued story
            exercise = workout[i][0]
            reps = workout[i][1]
            rest_time = workout[i][2]
            iteration_word_count = int(2.5 * rest_time)
            logging.info("Current workout is {} {}.".format(reps, exercise))
            
            recv_end, send_end = multiprocessing.Pipe(False)

            sidekick_word_limit = [round(int(iteration_word_count*0.25)/10) * 10]
            workout_setup_process = Process(target=setup_workout, args=(master_storyline, reps, exercise, i, send_end, SPEECH_DIR, SOUNDS_DIR, gpu, sidekick_word_limit))
            workout_setup_process.start()

            working_thread.join()
            playsound(r"{}".format(audiofile))
            # END INTERACTIVE
        elif mode == "manual":
            stop_event = threading.Event()
            faulthandler.enable()
            waiting_thread = threading.Thread(target=play_waiting, args=(os.path.join(SOUNDS_DIR, "waiting.wav"), stop_event))
            waiting_thread.start()
            answer = recognize_speech_from_mic(i-1, SPEECH_DIR)

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
                exit()   

            workout_setup_process.join()

            sidekick_workout_response, sidekick_audio_file = recv_end.recv()
            workout_response_word_count = len(sidekick_workout_response.split())


            playsound(sidekick_audio_file)

            # play workout music and process answer
            # TODO: Listen specifically for "I'm done", but now just wait 20 seconds
            workout_time = 25
            working_thread = threading.Thread(target=play_working, args=(os.path.join(SOUNDS_DIR, "fast_workout.wav"), workout_time))
            working_thread.start()

            # Add responses to storyline
            master_storyline += "\nMain Character: " + main_character_response
            master_storyline += "\nSidekick: " + sidekick_workout_response


            if i == len(workout):
                working_thread.join()
                break

            # Query GPT for the continuation of the story
            if iteration_word_count != 0:
                word_count_left = round((iteration_word_count - workout_response_word_count) / 10) * 10
                WORD_LIMIT_PROMPT = "Limit the output to around {} words.".format(word_count_left)
            gpt_output = query_gpt(master_storyline + prompt_constants.CONTINUE_PROMPT + WORD_LIMIT_PROMPT)   
            logging.info("Storyline {}: {}".format(i, gpt_output))
            master_storyline += "\n" + gpt_output

            # Process and prepare audio file for continued story
            lines = separate_script(gpt_output)
            audiofile = script_to_speech(lines,SPEECH_DIR,i,other_sounds=os.path.join(SOUNDS_DIR, "start_tone1.wav"), gpu=gpu)

            # Begin processing the 'sidekick yes good plan response with workout' before playing the continued story
            (exercise, reps, rest_time) = workout[i]
            iteration_word_count = int(2.5 * rest_time)
            logging.info("Current workout is {} {}.".format(reps, exercise))
            
            recv_end, send_end = multiprocessing.Pipe(False)

            sidekick_word_limit = [round(int(iteration_word_count*0.25)/10) * 10]
            workout_setup_process = Process(target=setup_workout, args=(master_storyline, reps, exercise, i, send_end, SPEECH_DIR, SOUNDS_DIR, gpu, sidekick_word_limit))
            workout_setup_process.start()

            working_thread.join()
            playsound(r"{}".format(audiofile))
            # END MANUAL

        else:  # mode == "auto"
            workout_setup_process.join()
            sidekick_workout_response, sidekick_audio_file = recv_end.recv()
            playsound(sidekick_audio_file)
            # play workout music and process answer
            workout_time = 25
            working_thread = threading.Thread(target=play_working, args=(os.path.join(SOUNDS_DIR, "fast_workout.wav"), workout_time))
            working_thread.start()

            # Add responses to storyline
            master_storyline += "\nSidekick: " + sidekick_workout_response

            # Exit if all workout exercises are completed
            if i == len(workout):
                working_thread.join()
                break

            # Query GPT for the continuation of the story
            gpt_output = query_gpt(master_storyline + prompt_constants.CONTINUE_PROMPT_AUTO)   
            logging.info("Storyline {}: {}".format(i, gpt_output))
            master_storyline += "\n" + gpt_output

            # Process and prepare audio file for continued story
            lines = separate_script(gpt_output)
            audiofile = script_to_speech(lines,SPEECH_DIR,i,other_sounds=os.path.join(SOUNDS_DIR, "start_tone1.wav"), gpu=gpu)

            # Begin processing the 'sidekick yes good plan response with workout' before playing the continued story
            (exercise, reps, rest_time) = workout[i]
            logging.info("Current workout is {} {}.".format(reps, exercise))
            
            recv_end, send_end = multiprocessing.Pipe(False)
            workout_setup_process = Process(target=setup_workout, args=(master_storyline, reps, exercise, i, send_end, SPEECH_DIR, SOUNDS_DIR, gpu))
            workout_setup_process.start()

            working_thread.join()
            playsound(r"{}".format(audiofile))
            # END AUTO

    conclusion = query_gpt(master_storyline + "Conclude the story. The sidekick congratulates the main character on them finishing their workouts.", response_length=512)
    master_storyline += conclusion
    lines = separate_script(conclusion)
    conclusion = script_to_speech(lines,SPEECH_DIR,i+1,gpu=gpu)
    playsound(conclusion)
    with open(os.path.join(OUTPUT_DIR, "complete_storyline.txt"), "w") as f:
        f.write(master_storyline)     
    print("The End") 