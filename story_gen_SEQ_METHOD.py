import os
import re
import json
import torch
import random
import logging
import threading
import multiprocessing
from TTS.api import TTS

from utils import *
from get_sound import *
from playsound import playsound
from get_workout import get_workout
from get_prompt import query_chatgpt, generate_random_prompt
from speech_to_text import get_user_response
import prompt_constants


def get_motion(exercise, actual_exercise=False):
    if actual_exercise:
        return exercise
    
    with open('./grammar/workout_motions.json', 'r') as f:
        data = json.load(f)
    
    if exercise in data.keys():
        return data[exercise]
    else: 
        system_prompt = """You will describe a physical exercise under 5 words.
                Make it independent of body orientation. 
                Some example descriptions: pushup maps to pushing against a surface, situps maps to bending torso towards knee."""
        response, usage = query_chatgpt(exercise, system_prompt)
        motion = response.strip("\n\"\'")
        motion = motion.lower()
        data[exercise] = motion
        with open('./grammar/workout_motions.json', 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)
        return motion
    

def create_all_sidekick_text(pool, workout, SPEECH_DIR, gpu=False, debug=False):
    if debug:
        return
    for i, (exercise, reps, _) in enumerate(workout):
        if 's' in reps:
            text = "Start your {} seconds {} now!".format(reps.strip('s'), exercise)
        else:
            text = "Start your {} {} now!".format(reps, exercise)
        file_path = os.path.join(SPEECH_DIR, "sidekick_start_workout_{}.wav".format(i))
        args = (text, "p273", file_path, gpu)
        pool.apply_async(tts_generate_audio, args=(args,))

    file_path = os.path.join(SPEECH_DIR, "what_now.wav")
    text = "What do you want to do now?"
    args = (text, "p273", file_path, gpu)
    pool.apply_async(tts_generate_audio, args=(args,))
    return


def play_sidekick_text(iteration, SPEECH_DIR, SOUNDS_DIR, workout, start_tone=2, debug=False):
    if debug:
        return
    
    # Assume create_all_sidekick_text is run before this so all files exist
    file_path = os.path.join(SPEECH_DIR, "sidekick_start_workout_{}.wav".format(iteration))
    what_now_path = os.path.join(SPEECH_DIR, "what_now.wav")
    start_tone_path = os.path.join(SOUNDS_DIR, "start_tone{}.wav".format(start_tone))
    if workout:
        playsound(file_path)
        playsound(start_tone_path)
    else:
        playsound(what_now_path)
        playsound(start_tone_path)
    return


def split_paragraph(script):
    '''
    Separates the script into lines for the narrator, and lines for the sidekick, 
    Returns list: [(line order number, voice actor #, actual line),...]
    '''
    # Remove headers before colon, narrator quotes
    script = script.replace("\n", "")
    script = script.replace("-:;", ",")

    # Remove narrator quotes
    if script[0] == '"' and script.count('"') % 2 == 1:  # I Don't get why it adds a double quote at the beginning
        script = script[1:]
    elif script[0] == '"' and script[-1] == '"':
        script = script[1:-1]

    in_quote = False
    result = []
    count = 0

    start_index = 0
    while True:
        index = script.find('"', start_index)
        if index == -1:
            if len(script[start_index:index]) > 3:
                result.append((count, 0, script[start_index:index]))
            break
        if not in_quote and len(script[start_index:index]) > 3:
            result.append((count, 0, script[start_index:index]))
            count += 1
            in_quote = not in_quote
        elif in_quote and len(script[start_index:index]) > 2:
            result.append((count, 1, script[start_index:index]))
            count += 1
            in_quote = not in_quote

        start_index = index + 1

    # If only one speaker itll probably be the narrator, split into sentences
    if len(result) == 1:
        sentences = str(result[0][2]).split(".!?")
        result = []
        for i, s in enumerate(sentences):
            result.append((i, 0, s))


    for line in result:
        if line[1] == 0:
            logging.info("Line {} voiced by NARRATOR:  {}".format(line[0], line[2]))
        else:  # line[1] == 1
            logging.info('Line {} voiced by SIDEKICK: "{}"'.format(line[0], line[2]))
    return result


# Convert script to audio file with different voice parts
# Use multiprocessing to speed up text to speech conversions
def tts_generate_audio(args):
    tts = TTS("tts_models/en/vctk/vits", gpu=args[3])
    tts.tts_to_file(text=args[0], speaker=args[1], file_path=args[2])


def process_text(args, output_queue):
    tts.tts_to_file(text=args[0], speaker=args[1], file_path=args[2])
    assert os.path.exists(args[2])
    output_queue.put((args[4], args[2]))


def initialize_worker(gpu):
    global tts
    tts = TTS("tts_models/en/vctk/vits", gpu=gpu)


def process_and_play_text(pool, user_paragraph, workout_paragraph, speech_dir, iteration_number, name, gpu=False, debug=False):
    if debug:
        return
    voices = {0: 'p267', 1: 'p273', 2: 'p330', 3:'p234', 4:'230'}
    user_paragraph.strip("\n\r\t\'")
    lines = split_paragraph(user_paragraph)
    audio_files = []
    manager = multiprocessing.Manager()
    audio_queue = manager.Queue() # to hold the audio objects returned by the text processing jobs

    for (order, voice, text) in lines:
        # submit a new text processing job to the pool
        pid = voices[voice]
        output_file = os.path.join(speech_dir, "story_{}_{}_{}.wav".format(name, iteration_number, order, pid))
        a=(text, pid, output_file, gpu, order)
        audio_files.append(output_file)
        pool.apply_async(process_text, args=(a, audio_queue,))
    
    if workout_paragraph != "":
        workout_lines = split_paragraph(workout_paragraph)
        for (order, voice, text) in workout_lines:
            # submit a new text processing job to the pool
            order = order + len(lines)
            pid = voices[voice]
            output_file = os.path.join(speech_dir, "story_{}_{}_{}.wav".format(name, iteration_number, order, pid))
            a=(text, pid, output_file, gpu, order)
            audio_files.append(output_file)
            pool.apply_async(process_text, args=(a, audio_queue,))
        total_length = len(lines) + len(workout_lines)
    else:
        total_length = len(lines)

    # create a new thread to play the audio files
    audio_thread = threading.Thread(target=play_audio_queue, args=(audio_queue, total_length))
    audio_thread.start()
    audio_thread.join()     
    manager.shutdown()
    concatenate_audio_moviepy(audio_files, os.path.join(speech_dir,"story_{}_{}_complete.wav".format(name, iteration_number)))


# Plays one sentence at a time, in order, when available after being processed
# As long as processing happens faster than playing audio, which it should, then it will be continuous audio
def play_audio_queue(audio_queue, num_files):
    audio_done = set() # to keep track of which audio files have finished playing
    audio_pending = {} # to hold the audio files that are not ready to be played yet
    next_audio_index = 0 # to keep track of the index of the next audio file to be played
    condition = threading.Condition()
    while len(audio_done) < num_files:
        with condition:
            while not audio_queue.empty():
                # get the next audio file from the queue and add it to the pending dict
                index, audio = audio_queue.get()
                audio_pending[index] = audio
            # check if the next audio file is ready to be played
            if next_audio_index in audio_pending:
                audio = audio_pending.pop(next_audio_index)
                playsound(audio)
                audio_done.add(next_audio_index)
                next_audio_index += 1

            condition.wait(timeout=0.05)


def summarize_if_needed(storyline, usage):
    if usage["total_tokens"] > 2500:
        summarized_storyline, usage = query_chatgpt(storyline, prompt_constants.SUMMARIZE, response_length=500)
        return summarized_storyline
    return storyline


def clip_text(storyline):
    question_index = storyline.rfind('?')
    exclamation_index = storyline.rfind('!')
    period_index = storyline.rfind('.')
    max_index = max(question_index, exclamation_index, period_index)
    if max_index > 0:
        storyline = storyline[:max_index+1]
    return storyline

def start_story_generation_SEQ_MODE(starting_prompt, workout_input, gpu, input_type, debug, actual_exercise=False):

    OUTPUT_DIR, SOUNDS_DIR, SPEECH_DIR = folder_creation()
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', filename=os.path.join(OUTPUT_DIR, "logfile.log"), datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
    story_file_path = os.path.join("outputs", "master_storyline.txt")

    workout = get_workout(workout_input, shuffle=True)
    logging.info("Complete Workout: {}".format(workout))
    tts_wpm = 190
    words_to_tokens = 1.4
    master_storyline = ""
    summarized_storyline = ""

    # Initialize Text-to-speech process, just use one TTS model for now
    with multiprocessing.Pool(min(2, multiprocessing.cpu_count()), initializer=initialize_worker, initargs=(gpu,)) as pool: 
        try:
            # Pregenerate all the sidekick text
            create_all_sidekick_text(pool, workout, SPEECH_DIR, gpu, debug)
            master_storyline, usage = query_chatgpt(prompt_constants.BEGINNING.format(starting_prompt), prompt_constants.SYSTEM_PROMPT, response_length=256)
            logging.info("Storyline (Beginning): {}".format(master_storyline))
            
            with open(story_file_path, "w") as f:
                f.write(master_storyline) 

            process_and_play_text(pool, master_storyline, "", SPEECH_DIR, 0, "introduction", gpu, debug)
            add_to_complete_annotation_file("(Introduction)", "Introduction", OUTPUT_DIR, count_words(master_storyline), 
                                            usage["completion_tokens"], 
                                            os.path.join(SPEECH_DIR, "story_0_0_complete.wav"), master_storyline)
            summarized_storyline = master_storyline

            # Iterate through workouts
            for i in range(0, len(workout)):
                # Get exercise
                (exercise, reps, rest_time) = workout[i]
                rest_time = int(rest_time)
                logging.info("Current workout is {} {}.".format(reps, exercise))

                # Get user response
                play_sidekick_text(i, SPEECH_DIR, SOUNDS_DIR, workout=False, start_tone=1, debug=debug)
                if input_type == "text":
                    user_response = input("What do you want to do now?\nYour Response: ")
                else: # Audio 
                    user_response = get_user_response(i, SPEECH_DIR, debug)
                logging.info("User response {}: {}".format(i, user_response))

                ########## USER CONTINUED STORY ##########
                user_response_length = int((tts_wpm * (rest_time/2) // 60) * words_to_tokens)
                user_continued_story, usage = query_chatgpt(summarized_storyline + "\n" + prompt_constants.CONTINUE_USER_RESPONSE.format(user_response), 
                                                    prompt_constants.SYSTEM_PROMPT,
                                                    response_length=user_response_length)
                
                user_continued_story = clip_text(user_continued_story)
                summarized_storyline = summarize_if_needed(summarized_storyline, usage)

                logging.info("User continued story ({} words, suppose to be {} words) {}: {}".format(count_words(user_continued_story), user_response_length, i, user_continued_story))
                
                master_storyline = master_storyline + " " + user_continued_story
                summarized_storyline = summarized_storyline + user_continued_story
                with open(story_file_path, "w") as f:
                    f.write(master_storyline) 

                ########## WORKOUT STORY ##########
                motion = get_motion(exercise, actual_exercise=actual_exercise)
                pre_workout_response_length = int((tts_wpm * (rest_time/2) // 60) * words_to_tokens)

                if 's' in reps: # Check for plank, handstand, and other 'hold' positions
                    pre_workout, usage = query_chatgpt(summarized_storyline + "\n" + prompt_constants.PRE_STORY_WORKOUT_HOLD_USER.format(motion, motion), 
                                                prompt_constants.SYSTEM_PROMPT,
                                                response_length=pre_workout_response_length)
                    summarized_storyline = summarize_if_needed(summarized_storyline, usage)
                else:
                    pre_workout, usage = query_chatgpt(summarized_storyline + "\n" + prompt_constants.PRE_STORY_WORKOUT_USER.format(motion, motion), 
                                                prompt_constants.SYSTEM_PROMPT,
                                                response_length=pre_workout_response_length)
                    summarized_storyline = summarize_if_needed(summarized_storyline, usage)
                pre_workout = clip_text(pre_workout)

                master_storyline = master_storyline + " " + pre_workout
                summarized_storyline = summarized_storyline + " " + pre_workout

                with open(story_file_path, "w") as f:
                    f.write(master_storyline) 

                add_to_eval_file(exercise, reps, pre_workout, OUTPUT_DIR)
                logging.info("Storyline ({} words, suppose to be {} words) {} (WORKOUT STORY): {}".format(count_words(pre_workout), pre_workout_response_length,i, pre_workout))

                # Play story and do workout
                process_and_play_text(pool, user_continued_story, pre_workout, SPEECH_DIR, i, "workout", gpu, debug)

                add_to_complete_annotation_file(i, "USER RESPONSE", OUTPUT_DIR, count_words(user_continued_story), 
                                            usage["completion_tokens"], 
                                            os.path.join(SPEECH_DIR, "story_{}_{}_complete.wav".format("user", i)), 
                                            user_continued_story, 
                                            allocated_rest_time=int((1 * int(rest_time) // 2)))
                
                add_to_complete_annotation_file(i, "WORKOUT STORY", OUTPUT_DIR, count_words(pre_workout), 
                                            usage["completion_tokens"], 
                                            os.path.join(SPEECH_DIR, "story_{}_{}_complete.wav".format("workout", i)), 
                                            pre_workout, 
                                            allocated_rest_time=int((1 * int(rest_time) // 2)), reps=reps, exercise=exercise)

                play_sidekick_text(i, SPEECH_DIR, SOUNDS_DIR, workout=True, start_tone=2, debug=debug)
                # Change to loop and check for the word 'done'
                #workout_time = 25
                #workout_sound_file = os.path.join(SOUNDS_DIR, "fast_workout.wav")
                #play_working(workout_sound_file, workout_time, debug)

            # End the story
            conclusion, usage = query_chatgpt(summarized_storyline + "\n" + prompt_constants.CONCLUSION, prompt_constants.SYSTEM_PROMPT, response_length=512)
            process_and_play_text(pool, conclusion, "", SPEECH_DIR, i, "conclusion", gpu, debug)
            add_to_complete_annotation_file("(CONCLUSION)", "CONCLUSION", OUTPUT_DIR, count_words(conclusion), 
                                            usage["completion_tokens"], os.path.join(SPEECH_DIR, "story_{}_{}_complete.wav".format("conclusion", i)), 
                                            conclusion)
            master_storyline += conclusion
            with open(story_file_path, "w") as f:
                    f.write(master_storyline) 

            # Explicit close  
            pool.close()
            pool.terminate()  
            print("DONE WORKOUT")

        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt, terminating workers...")
            pool.join()
            pool.terminate()   
            print("Workers terminated.")
            exit()

    story_complete=True
    # THE END

if __name__ == '__main__':
    # starting_prompt = """You are Shawn. You are a headhunter trying to survive after the British bombed your country to the ground. You have an old rifle and an old gas mask.
    # You are drinking with a stranger in a bar, but you need to get going. 
    # You decide to leave the building. You are on a mission to kill a captain named Simone. Your target lives in a nearby city."""
    input_type="audio"
    name = "Shawn"
    #starting_prompt = generate_random_prompt(name)
    #start_story_generation_SEQ_MODE(starting_prompt, "inputs/workout4.csv", gpu=torch.cuda.is_available(), input_type=input_type, debug=True)
    name = random.choice(["Sebastian", "Rory", "Nolan", "Orlando", "Serena"])
    starting_prompt = generate_random_prompt(name)
    start_story_generation_SEQ_MODE(starting_prompt, "inputs/workout_all.csv", gpu=torch.cuda.is_available(), input_type=input_type, debug=True, actual_exercise=False)
    