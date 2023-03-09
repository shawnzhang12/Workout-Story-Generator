import os
import logging
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