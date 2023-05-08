import multiprocessing
import os
import re
import json
import threading
import torch
import random
import logging
from typing import Dict, Tuple, List, Union
from TTS.api import TTS

from utils import add_to_annotation_file, add_to_eval_file, count_words, create_folder
from get_sound import *
from playsound import playsound
from get_workout import get_workout
from get_prompt import query_chatgpt, generate_random_prompt
from speech_to_text import get_user_response
import prompt_constants


def get_motion(exercise: str, model, actual_exercise: bool = False) -> str:
    """
    Returns the motion corresponding to the exercise.

    Parameters
    ----------
    exercise : str
        Name of the exercise.
    model : str
        GPT model type.
    actual_exercise : bool, optional
        Whether to return the exercise name itself.

    Returns
    -------
    str
        Name of the motion.
    """
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
        response, _ = query_chatgpt(exercise, model, system_prompt)
        motion = response.strip("\n\"\'").lower()
        data[exercise] = motion
        with open('./grammar/workout_motions.json', 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)
        return motion


def create_all_sidekick_text(pool, workout: List[Tuple[str, str, int]], speech_dir: str, gpu: bool = False, debug: bool = False):
    """
    Creates sidekick text for all workouts.

    Parameters
    ----------
    pool : multiprocessing.Pool
        Pool of worker processes.
    workout : List[Tuple[str, str, int]]
        List of workouts, each represented as a tuple (exercise, reps, TODO).
    speech_dir : str
        Directory to save the speech files.
    gpu : bool, optional
        Whether to use GPU for TTS.
    debug : bool, optional
        Whether to run in debug mode.

    Returns
    -------
    None
    """
    if debug:
        return
    for i, (exercise, reps, _) in enumerate(workout):
        if 's' in reps:
            text = "Start your {} seconds {} now!".format(reps.strip('s'), exercise)
        else:
            text = "Start your {} {} now!".format(reps, exercise)
        file_path = os.path.join(speech_dir, "sidekick_start_workout_{}.wav".format(i))
        args = (text, "p273", file_path, gpu)
        pool.apply_async(tts_generate_audio, args=(args,))

    file_path = os.path.join(speech_dir, "what_now.wav")
    text = "What do you want to do now?"
    args = (text, "p273", file_path, gpu)
    pool.apply_async(tts_generate_audio, args=(args,))
    return



def play_sidekick_text(iteration: int, speech_dir: str, sounds_dir: str, workout: bool, start_tone: int = 2, debug: bool = False) -> None:
    """
    Plays sidekick text for the specified iteration.

    Parameters
    ----------
    iteration : int
        Index of the workout to play the sidekick text for.
    speech_dir : str
        Directory containing the speech files.
    sounds_dir : str
        Directory containing the sound files.
    workout : bool
        Whether to play the workout response.
    start_tone : int, optional
        Index of the start tone to play.
    debug : bool, optional
        Whether to run in debug mode.

    Returns
    -------
    None
    """
    if debug:
        return
    
    file_path = os.path.join(speech_dir, "sidekick_start_workout_{}.wav".format(iteration))
    what_now_path = os.path.join(speech_dir, "what_now.wav")
    start_tone_path = os.path.join(sounds_dir, "start_tone{}.wav".format(start_tone))
    if workout:
        playsound(file_path)
        playsound(start_tone_path)
    else:
        playsound(what_now_path)
        playsound(start_tone_path)
    return


def split_paragraph(script: str) -> List[Tuple[int, int, str]]:
    """
    Separates the script into lines for the narrator and lines for the sidekick.

    Parameters
    ----------
    script : str
        The script to split.

    Returns
    -------
    List[Tuple[int, int, str]]
        A list of tuples, each containing the line order number, voice actor number, and the actual line.
    """
    # Remove headers before colon, narrator quotes
    script = script.replace("\n", "").replace("-:;", ",")

    # Remove narrator quotes
    if script[0] == '"' and script.count('"') % 2 == 1:
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

    # If only one speaker, it'll probably be the narrator; split into sentences
    if len(result) == 1:
        sentences = str(result[0][2]).split(".!?")
        result = [(i, 0, s) for i, s in enumerate(sentences)]

    for line in result:
        if line[1] == 0:
            logging.info("Line {} voiced by NARRATOR:  {}".format(line[0], line[2]))
        else:  # line[1] == 1
            logging.info('Line {} voiced by SIDEKICK: "{}"'.format(line[0], line[2]))
    return result


def tts_generate_audio(args: Tuple) -> None:
    """
    Generates audio using TTS.

    Parameters
    ----------
    args : Tuple
        Arguments for the TTS function.

    Returns
    -------
    None
    """
    tts = TTS("tts_models/en/vctk/vits", gpu=args[3])
    tts.tts_to_file(text=args[0], speaker=args[1], file_path=args[2])


def process_text(args: Tuple, output_queue: multiprocessing.Queue) -> None:
    """
    Processes text and stores the output in the provided queue.

    Parameters
    ----------
    args : Tuple
        Arguments for the text processing.
    output_queue : multiprocessing.Queue
        Queue to store the output.

    Returns
    -------
    None
    """
    tts.tts_to_file(text=args[0], speaker=args[1], file_path=args[2])
    assert os.path.exists(args[2])
    output_queue.put((args[4], args[2]))


def initialize_worker(gpu: Union[bool, int]) -> None:
    """
    Initializes the TTS worker.

    Parameters
    ----------
    gpu : Union[bool, int]
        GPU flag or index.

    Returns
    -------
    None
    """
    global tts
    tts = TTS("tts_models/en/vctk/vits", gpu=gpu)


def process_and_play_text(pool: multiprocessing.Pool, user_paragraph: str, workout_paragraph: str, speech_dir: str, iteration_number: int, name: str, gpu: Union[bool, int] = False, debug: bool = False) -> None:
    """
    Processes and plays text using multiprocessing and threading.

    Parameters
    ----------
    pool : multiprocessing.Pool
        The multiprocessing pool.
    user_paragraph : str
        The user paragraph.
    workout_paragraph : str
        The workout paragraph.
    speech_dir : str
        Directory containing the speech files.
    iteration_number : int
        Index of the iteration.
    name : str
        Name of the output file.
    gpu : Union[bool, int], optional
        GPU flag or index.
    debug : bool, optional
        Whether to run in debug mode.

    Returns
    -------
    None
    """
    if debug:
        return

    voices = {0: 'p267', 1: 'p273', 2: 'p330', 3: 'p234', 4: 'p230'}
    user_paragraph.strip("\n\r\t\'")
    lines = split_paragraph(user_paragraph)
    audio_files = []
    manager = multiprocessing.Manager()
    audio_queue = manager.Queue()  # to hold the audio objects returned by the text processing jobs

    for (order, voice, text) in lines:
        pid = voices[voice]
        output_file = os.path.join(speech_dir, "story_{}_{}_{}.wav".format(name, iteration_number, order, pid))
        args = (text, pid, output_file, gpu, order)
        audio_files.append(output_file)
        pool.apply_async(process_text, args=(args, audio_queue,))

    if workout_paragraph != "":
        workout_lines = split_paragraph(workout_paragraph)
        for (order, voice, text) in workout_lines:
            order = order + len(lines)
            pid = voices[voice]
            output_file = os.path.join(speech_dir, "story_{}_{}_{}.wav".format(name, iteration_number, order, pid))
            args = (text, pid, output_file, gpu, order)
            audio_files.append(output_file)
            pool.apply_async(process_text, args=(args, audio_queue,))
        total_length = len(lines) + len(workout_lines)
    else:
        total_length = len(lines)

    audio_thread = threading.Thread(target=play_audio_queue, args=(audio_queue, total_length))
    audio_thread.start()
    audio_thread.join()

    manager.shutdown()
    concatenate_audio_moviepy(audio_files, os.path.join(speech_dir, "story_{}_{}_complete.wav".format(name, iteration_number)))


def play_audio_queue(audio_queue: multiprocessing.Queue, num_files: int) -> None:
    """
    Play audio files one sentence at a time, in order, as they become available after being processed.

    Parameters
    ----------
    audio_queue : multiprocessing.Queue
        Queue to hold the audio objects returned by the text processing jobs.
    num_files : int
        Number of audio files to be played.

    Returns
    -------
    None
    """
    audio_done = set()  # to keep track of which audio files have finished playing
    audio_pending = {}  # to hold the audio files that are not ready to be played yet
    next_audio_index = 0  # to keep track of the index of the next audio file to be played
    condition = threading.Condition()
    while len(audio_done) < num_files:
        with condition:
            while not audio_queue.empty():
                index, audio = audio_queue.get()
                audio_pending[index] = audio
            if next_audio_index in audio_pending:
                audio = audio_pending.pop(next_audio_index)
                playsound(audio)
                audio_done.add(next_audio_index)
                next_audio_index += 1

            condition.wait(timeout=0.05)


def summarize_if_needed(storyline: str, usage: Dict[str, int], model) -> str:
    """
    Summarize the storyline if the total number of tokens exceeds 2500.

    Parameters
    ----------
    storyline : str
        The storyline to summarize.
    usage : Dict[str, int]
        Dictionary with token usage information.
    model : object
        Chatbot model object.

    Returns
    -------
    str
        Summarized storyline or the original storyline.
    """
    if usage["total_tokens"] > 2500:
        summarized_storyline, usage = query_chatgpt(storyline, prompt_constants.SUMMARIZE, model, response_length=500)
        return summarized_storyline
    return storyline


def clip_text(storyline: str) -> str:
    """
    Clip the text at the last punctuation mark.

    Parameters
    ----------
    storyline : str
        The storyline to clip.

    Returns
    -------
    str
        Clipped storyline.
    """
    question_index = storyline.rfind('?')
    exclamation_index = storyline.rfind('!')
    period_index = storyline.rfind('.')
    max_index = max(question_index, exclamation_index, period_index)
    if max_index > 0:
        storyline = storyline[:max_index + 1]
    return storyline


def start_sequential_story_generation(starting_prompt: str, workout_input: str, gpu: bool, input_type: str, debug: bool, model: str = "gpt-3.5-turbo", actual_exercise: bool = False) -> None:
    """
    Start story generation in sequence mode.

    Parameters
    ----------
    starting_prompt : str
        The starting prompt for the story.
    workout_input : str
        The workout input.
    gpu : bool
        If True, use the GPU for processing.
    input_type : str
        The input type, either 'text' or 'audio'.
    debug : bool
        If True, run the function in debug mode.
    model : str, optional
        The GPT model to use, by default "gpt-3.5-turbo".
    actual_exercise : bool, optional
        If True, perform actual exercise, by default False.

    Returns
    -------
    None
    """
    OUTPUT_DIR, SOUNDS_DIR, SPEECH_DIR = create_folder()
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', filename=os.path.join(OUTPUT_DIR, "logfile.log"), datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
    story_file_path = os.path.join("outputs", "master_storyline_{}.txt")

    workout = get_workout(workout_input, shuffle=True)
    logging.info("Complete Workout: {}".format(workout))
    tts_wpm = 190
    words_to_tokens = 1.4
    master_storyline = ""
    summarized_storyline = ""
    count = 0

    # Initialize Text-to-speech process, just use one TTS model for now
    with multiprocessing.Pool(min(2, multiprocessing.cpu_count()), initializer=initialize_worker, initargs=(gpu,)) as pool: 
        try:
            # Pregenerate all the sidekick text
            create_all_sidekick_text(pool, workout, SPEECH_DIR, gpu, debug)
            master_storyline, usage = query_chatgpt(prompt_constants.BEGINNING.format(starting_prompt), prompt_constants.SYSTEM_PROMPT, model, response_length=256)
            logging.info("Storyline (Beginning): {}".format(master_storyline))

            with open(story_file_path.format(count), "w") as f:
                f.write(master_storyline) 
                count += 1

            process_and_play_text(pool, master_storyline, "", SPEECH_DIR, 0, "introduction", gpu, debug)
            add_to_annotation_file("(Introduction)", "Introduction", OUTPUT_DIR, count_words(master_storyline), usage["completion_tokens"], os.path.join(SPEECH_DIR, "story_0_0_complete.wav"), master_storyline)
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
                user_continued_story, usage = query_chatgpt(summarized_storyline + "\n" + prompt_constants.CONTINUE_USER_RESPONSE.format(user_response), prompt_constants.SYSTEM_PROMPT, model, response_length=user_response_length)
                
                user_continued_story = clip_text(user_continued_story)
                summarized_storyline = summarize_if_needed(summarized_storyline, usage, model)

                logging.info("User continued story ({} words, suppose to be {} words) {}: {}".format(count_words(user_continued_story), user_response_length, i, user_continued_story))

                master_storyline = master_storyline + " " + user_continued_story
                summarized_storyline = summarized_storyline + user_continued_story
                with open(story_file_path.format(count), "w") as f:
                    f.write(master_storyline) 
                    count += 1

                ########## WORKOUT STORY ##########
                motion = get_motion(exercise, model, actual_exercise=actual_exercise)
                pre_workout_response_length = int((tts_wpm * (rest_time/2) // 60) * words_to_tokens)

                if 's' in reps: # Check for plank, handstand, and other 'hold' positions
                    pre_workout, usage = query_chatgpt(summarized_storyline + "\n" + prompt_constants.PRE_STORY_WORKOUT_HOLD_USER.format(motion, motion), prompt_constants.SYSTEM_PROMPT, model, response_length=pre_workout_response_length)
                    summarized_storyline = summarize_if_needed(summarized_storyline, usage, model)
                else:
                    pre_workout, usage = query_chatgpt(summarized_storyline + "\n" + prompt_constants.PRE_STORY_WORKOUT_USER.format(motion, motion), prompt_constants.SYSTEM_PROMPT, model, response_length=pre_workout_response_length)
                    summarized_storyline = summarize_if_needed(summarized_storyline, usage, model)
                pre_workout = clip_text(pre_workout)

                master_storyline = master_storyline + " " + pre_workout
                summarized_storyline = summarized_storyline + " " + pre_workout

                with open(story_file_path.format(count), "w") as f:
                    f.write(master_storyline) 
                    count += 1

                add_to_eval_file(exercise, reps, pre_workout, OUTPUT_DIR)
                logging.info("Storyline ({} words, suppose to be {} words) {} (WORKOUT STORY): {}".format(count_words(pre_workout), pre_workout_response_length,i, pre_workout))

                # Play story and do workout
                process_and_play_text(pool, user_continued_story, pre_workout, SPEECH_DIR, i, "workout", gpu, debug)

                add_to_annotation_file(i, "USER RESPONSE", OUTPUT_DIR, count_words(user_continued_story), usage["completion_tokens"], os.path.join(SPEECH_DIR, "story_{}_{}_complete.wav".format("user", i)), user_continued_story, allocated_rest_time=int((1 * int(rest_time) // 2)))

                add_to_annotation_file(i, "WORKOUT STORY", OUTPUT_DIR, count_words(pre_workout), usage["completion_tokens"], os.path.join(SPEECH_DIR, "story_{}_{}_complete.wav".format("workout", i)), pre_workout, allocated_rest_time=int((1 * int(rest_time) // 2)), reps=reps, exercise=exercise)

                play_sidekick_text(i, SPEECH_DIR, SOUNDS_DIR, workout=True, start_tone=2, debug=debug)

                # Play workout music    
                workout_time = 25
                workout_sound_file = os.path.join(SOUNDS_DIR, "fast_workout.wav")
                play_working(workout_sound_file, workout_time, debug)

            # End the story
            conclusion, usage = query_chatgpt(summarized_storyline + "\n" + prompt_constants.CONCLUSION, prompt_constants.SYSTEM_PROMPT, model, response_length=512)
            process_and_play_text(pool, conclusion, "", SPEECH_DIR, i, "conclusion", gpu, debug)
            add_to_annotation_file("(CONCLUSION)", "CONCLUSION", OUTPUT_DIR, count_words(conclusion), 
                                            usage["completion_tokens"], os.path.join(SPEECH_DIR, "story_{}_{}_complete.wav".format("conclusion", i)), 
                                            conclusion)
            master_storyline += conclusion
            with open(story_file_path.format(count), "w") as f:
                f.write(master_storyline) 
                count += 1

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
    input_type="audio"
    name = random.choice(["Sebastian", "Rory", "Nolan", "Orlando", "Serena"])
    starting_prompt = generate_random_prompt(name)

    start_sequential_story_generation(starting_prompt, "inputs/workout_all.csv", gpu=torch.cuda.is_available(), input_type=input_type, debug=True, actual_exercise=False)
    