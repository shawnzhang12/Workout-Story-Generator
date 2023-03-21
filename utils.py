import os
import logging
import wave
from functools import wraps
from time import time
from threading import Thread
from datetime import datetime

def folder_creation(name=None):
    rootdir = os.path.join(
            os.getcwd(), 
            "outputs",
            datetime.now().strftime('%Y-%m-%d'))
    if not os.path.exists(rootdir):
        os.makedirs(rootdir)

    if name is None:
        mydir = os.path.join(
            rootdir,
            datetime.now().strftime('%H-%M-%S'))
    else:
        mydir = os.path.join(
            os.getcwd(), 
            "outputs",
            name)

    SOUNDS_DIR = os.path.join(os.getcwd(), "story_sounds")
    SPEECH_DIR = os.path.join(mydir, "speech")
    os.makedirs(mydir)
    os.makedirs(SPEECH_DIR)
    return mydir, SOUNDS_DIR, SPEECH_DIR


def count_words(text):
    words = text.split()
    return len(words)


def add_to_eval_file(exercise, reps, workout_text, OUTPUT_DIR):
    file_path = os.path.join(OUTPUT_DIR, "workouts.txt")
    with open(file_path, 'a+') as f:
        f.write("CURRENT EXERCISE: {} {}\n".format(reps, exercise))
        f.write("WORKOUT STORY: {}\n".format(workout_text))
        f.write("SIDEKICK SAYS: DO YOUR {} {} NOW!".format(reps, exercise))
        f.write("\n\n")


def get_wav_duration(file_path):
    if not os.path.exists(file_path):
        return -1
    with wave.open(file_path, 'r') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration


def add_to_complete_annotation_file(iteration, annotation, OUTPUT_DIR, word_count, token_count, audio_path, text, allocated_rest_time="None", reps="None", exercise="None"):
    file_path = os.path.join(OUTPUT_DIR, "complete_annotation.txt")
    audio_duration = get_wav_duration(audio_path)
    wpm = int((word_count  * 60) / audio_duration)
    text = text.replace("\n", "")
    texts = text.split(".")
    if audio_duration == -1:
        wpm = -1
    
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


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return


def timing(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        te = time()
        logging.info("func:{} took: {:.2f} sec".format(f.__name__, te-ts))
        return result
    return wrap
