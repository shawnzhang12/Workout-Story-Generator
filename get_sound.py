import os
import wave
import pyaudio
from datetime import datetime
from moviepy.editor import *

def concatenate_audio_moviepy(audio_clip_paths, output_path, background_music=None):
    """
    Concatenates multiple audio files into one using MoviePy and saves it to `output_path`.
    `background_music` (optional) is applied to the concatenated audio as a soft background track.
    """
    clips = [AudioFileClip(c) for c in audio_clip_paths]
    final_clip = concatenate_audioclips(clips)

    if background_music is not None:
        final_clip.write_audiofile(background_music)
        backgroundclip = AudioFileClip(background_music).volumex(0.4)
        backgroundclip.set_duration(final_clip.duration)
        end_clip = CompositeAudioClip([backgroundclip, final_clip])
        end_clip.write_audiofile(output_path)
    else:
        final_clip.write_audiofile(output_path)

def play_audio(file_path, duration, stop_event=None):
    """
    Plays an audio file using PyAudio for the specified duration. 
    If stop_event (threading.Event object) is set, it stops the playback.
    """
    # Initialize PyAudio object
    p = pyaudio.PyAudio()

    # Open the wave file
    wf = wave.open(file_path, 'rb')

    # Open a stream for the wave file
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Start playing the sound, loop waiting
    start = datetime.now()
    while (datetime.now() - start).total_seconds() < duration:
        wf.rewind()
        data = wf.readframes(1024)
        while len(data) > 0:
            if stop_event and stop_event.is_set():
                break
            stream.write(data)
            data = wf.readframes(1024)
            
    # Stop the stream and close it
    stream.stop_stream()
    stream.close()

    # Terminate the PyAudio object
    p.terminate()

def play_waiting(file_path, stop_event):
    """
    Plays a waiting sound for a maximum of 30 seconds or until stop_event is set.
    """
    play_audio(file_path, 30, stop_event)

def play_working(file_path, workout_time, debug=False):
    """
    Plays a workout sound for the specified workout time in seconds.
    """
    if debug:
        return
    play_audio(file_path, workout_time)