import os
import wave
from datetime import datetime
from typing import Tuple

def create_folder(name: str = None) -> Tuple[str, str, str]:
    """
    Creates necessary directories.

    Parameters
    ----------
    name : str, optional
        Custom name for the folder, if provided.

    Returns
    -------
    Tuple[str, str, str]
        Paths for the created directories.
    """
    root_dir = os.path.join(os.getcwd(), "outputs", datetime.now().strftime('%Y-%m-%d'))
    os.makedirs(root_dir, exist_ok=True)

    if name is None:
        my_dir = os.path.join(root_dir, datetime.now().strftime('%H-%M-%S'))
    else:
        my_dir = os.path.join(os.getcwd(), "outputs", name)

    sounds_dir = os.path.join(os.getcwd(), "story_sounds")
    speech_dir = os.path.join(my_dir, "speech")
    os.makedirs(my_dir, exist_ok=True)
    os.makedirs(speech_dir, exist_ok=True)

    return my_dir, sounds_dir, speech_dir


def count_words(text: str) -> int:
    """Counts words in a text."""
    return len(text.split())


def add_to_eval_file(exercise: str, reps: str, workout_text: str, output_dir: str) -> None:
    """Appends exercise information to the workout evaluation file."""
    file_path = os.path.join(output_dir, "workouts.txt")
    with open(file_path, 'a+') as f:
        f.write(f"CURRENT EXERCISE: {reps} {exercise}\n")
        f.write(f"WORKOUT STORY: {workout_text}\n")
        f.write(f"SIDEKICK SAYS: DO YOUR {reps} {exercise} NOW!\n\n")


def get_wav_duration(file_path: str) -> float:
    """Returns the duration of a .wav file in seconds."""
    if not os.path.exists(file_path):
        return -1

    with wave.open(file_path, 'r') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        return frames / float(rate)


def add_to_annotation_file(iteration: int, annotation: str, output_dir: str, word_count: int, token_count: int, 
                           audio_path: str, text: str, allocated_rest_time: str = "None", 
                           reps: str = "None", exercise: str = "None") -> None:
    """Appends annotation information to the complete annotation file."""
    file_path = os.path.join(output_dir, "complete_annotation.txt")
    audio_duration = get_wav_duration(audio_path)
    wpm = int((word_count  * 60) / audio_duration) if audio_duration != -1 else -1
    text = text.replace("\n", "")
    texts = text.split(".")

    with open(file_path, 'a+') as f:
        f.write(f"ITERATION: {iteration}\n")
        f.write(f"STORY SECTION: {annotation}\n")
        f.write(f"EXERCISE: {reps} {exercise}\n")
        f.write(f"WORD COUNT: {word_count} words\n")
        f.write(f"TOKEN COUNT: {token_count} tokens\n")
        f.write(f"AUDIO TIME: {audio_duration} seconds\n")
        f.write(f"WPM (TTS): {wpm} wpm\n")
        f.write(f"ALLOCATED_REST_TIME: {allocated_rest_time} seconds\n")
        f.write("TEXT:\n")
        for t in texts:
            f.write(f"{t}.\n")
        f.write(" \n")
        f.write(" \n")

