import os
import re
import json
import logging
import threading
import multiprocessing
from TTS.api import TTS

from utils import *
from get_sound import *
from playsound import playsound
from get_workout import get_workout
from get_prompt import query_gpt, query_chatgpt, generate_random_prompt
from speech_to_text import recognize_speech_from_mic
import prompt_constants


def get_motion(exercise):
    with open('./grammar/workout_motions.json', 'r') as f:
        data = json.load(f)
    
    if exercise in data.keys():
        return data[exercise]
    else: 
        system_prompt = """You will describe a physical exercise under 5 words.
                Be general enough that people can guess what exercise it is. 
                Make it independent of body orientation. 
                One example description: pushup maps to pushing against a surface."""
        motion = query_chatgpt(exercise, system_prompt).strip("\n\"\'")
        data[exercise] = motion
        with open('./grammar/workout_motions.json', 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)
        return motion
    

def play_sidekick_text(reps: str, exercise: str, gpu, iteration, SPEECH_DIR, SOUNDS_DIR, workout, start_tone=2):
    if workout:
        if 's' in reps:
            num = reps.strip('s')
            text = "Start your {} seconds {} now!".format(num, exercise)
        else:
            text = "Start your {} {} now!".format(reps, exercise)
        file_path = os.path.join(SPEECH_DIR, "sidekick_start_workout_{}.wav".format(iteration))
        tts_generate_audio([text, "p273", file_path, gpu])
    else:
        file_path = os.path.join(SPEECH_DIR, "what_now.wav")
        if not os.path.exists(file_path):
            tts_generate_audio(["What do you want to do now?", "p273", file_path, gpu])
    assert os.path.exists(file_path)        
    playsound(file_path)
    playsound(os.path.join(SOUNDS_DIR, "start_tone{}.wav".format(start_tone)))


def fix_output(text):
    answer =  query_gpt("Wrap all the sidekick's spoken text in DOUBLE QUOTATIONS only and remove quotation marks around the narrator's lines for the following text: {}".format(text))
    return answer


def split_paragraph(script):
    '''
    Separates the script into lines for the narrator, and lines for the sidekick, 
    TODO: assumes all quotes are sidekicks for now, can use gpt model to extract quotes later
    Returns list: [(line order number, voice actor #, actual line),...]
    '''
    # Remove headers before colon, narrator quotes
    script = script.replace("\n", "")
    script = script.replace("-:;", ",")
    #processed_lines = [re.sub(r".*?:", "", line) for line in lines]
    #processed_lines = [re.sub(r'[-:;]', ',', line) for line in processed_lines]
    #script = " ".join(processed_lines)

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


def process_and_play_text(pool, paragraph, speech_dir, iteration_number, name, gpu=False):
    voices = {0: 'p267', 1: 'p273', 2: 'p330', 3:'p234', 4:'230'}
    paragraph.strip("\n\r\t\'")
    lines = split_paragraph(paragraph)
    manager = multiprocessing.Manager()
    audio_queue = manager.Queue() # to hold the audio objects returned by the text processing jobs

    for (order, voice, text) in lines:
        # submit a new text processing job to the pool
        pid = voices[voice]
        output_file = "story_{}_{}_{}.wav".format(name, iteration_number, order, pid)
        a=(text, pid, os.path.join(speech_dir, output_file), gpu, order)
        pool.apply_async(process_text, args=(a, audio_queue,))

    # create a new thread to play the audio files
    audio_thread = threading.Thread(target=play_audio_queue, args=(audio_queue, len(lines)))
    audio_thread.start()
    audio_thread.join()     
    manager.shutdown()

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


def start_story_generation_SEQ_MODE(starting_prompt, workout_input, gpu=False):

    OUTPUT_DIR, SOUNDS_DIR, SPEECH_DIR = folder_creation()
    workout_sound_file = os.path.join(SOUNDS_DIR, "fast_workout.wav")
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', filename=os.path.join(OUTPUT_DIR, "logfile.log"), datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
  
    workout = get_workout(workout_input, shuffle=True)
    logging.info("Complete Workout: {}".format(workout))

    master_storyline = query_gpt(prompt_constants.CONST_BEGINNING_AUTO.format(starting_prompt))
    logging.info("Storyline (Beginning): {}".format(master_storyline))

    # Initialize Text-to-speech process, just use one TTS model for now
    with multiprocessing.Pool(min(1, multiprocessing.cpu_count()), initializer=initialize_worker, initargs=(gpu,)) as pool:

        process_and_play_text(pool, master_storyline, SPEECH_DIR, 0, 0)

        # Iterate through workouts
        for i in range(0, len(workout)):
            # Get exercise
            (exercise, reps, _) = workout[i]
            logging.info("Current workout is {} {}.".format(reps, exercise))
            sidekick_args = (reps, exercise, gpu, i, SPEECH_DIR, SOUNDS_DIR)

            # Get user response
            play_sidekick_text(*sidekick_args, workout=False, start_tone=1)
            user_response = recognize_speech_from_mic(i, SPEECH_DIR)
            logging.info("User response {}: {}".format(i, user_response))

            # Output short user response response
            user_continued_story = query_gpt(master_storyline + "\n" + prompt_constants.CONTINUE_USER_STORY.format(user_response))
            master_storyline = master_storyline + " " + user_continued_story
            process_and_play_text(pool, user_continued_story, SPEECH_DIR, i, "user")

            # Get workout story
            motion = get_motion(exercise)
            gpt_output = query_gpt(master_storyline + "\n" + prompt_constants.CONTINUE_WITH_WORKOUT.format(motion))

            if gpt_output.find("<STOP_TOKEN>") == -1:
                gpt_output = query_gpt(master_storyline + " Append <STOP_TOKEN> to the end of the sentence where the main character completes the {} motion.".format(motion))

            pre_workout, post_workout = gpt_output.split("<STOP_TOKEN>")
            if post_workout == "":
                post_workout = query_gpt(master_storyline + " Continue the story for a few more descriptive, juicy sentences")
            master_storyline = master_storyline + " " + pre_workout + " " + post_workout
            logging.info("Storyline {} (PRE): {}".format(i, pre_workout))
            logging.info("Storyline {} (POST): {}".format(i, post_workout))
            
            # Play story and do workout
            process_and_play_text(pool, pre_workout, SPEECH_DIR, i, "pre")
            play_sidekick_text(*sidekick_args, workout=True, start_tone=2)
            # Change to loop and check for the word 'done'
            workout_time = 25
            play_working(workout_sound_file, workout_time)
            process_and_play_text(pool, post_workout, SPEECH_DIR, i, "post")

        # End the story
        conclusion = query_gpt(master_storyline + "Conclude the story. The sidekick congratulates the main character on them finishing their workouts.", response_length=512)
        process_and_play_text(pool, conclusion, SPEECH_DIR, len(workout), "conclude")
        master_storyline += conclusion
        with open(os.path.join(OUTPUT_DIR, "complete_storyline.txt"), "w") as f:
            f.write(master_storyline)  

        # Explicit close  
        pool.close()
    # THE END

if __name__ == '__main__':
    starting_prompt = """You are Shawn. You are a headhunter trying to survive after the British bombed your country to the ground. You have an old rifle and an old gas mask.
    You are drinking with a stranger in a bar, but you need to get going. 
    You decide to leave the building. You are on a mission to kill a captain named Simone. Your target lives in a nearby city."""
    starting_prompt = generate_random_prompt("Shawn")
    start_story_generation_SEQ_MODE(starting_prompt, "inputs/workout1.csv")
    