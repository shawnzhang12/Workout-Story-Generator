import os
import wave
import pyaudio
import freesound
from datetime import datetime
from moviepy.editor import *
from dotenv import load_dotenv
from utils import timing

load_dotenv()

client_id = os.getenv("FREESOUND_CLIENT_ID")
client_secret = os.getenv("FREESOUND_API_KEY")

client = freesound.FreesoundClient()
client.set_token(client_secret, "token")

def get_sound(query):
    results = client.text_search(query=query,fields="id,name,previews")
    if results.count == 0:
        return None
    #perform better filtering later
    results[0].retrieve_preview("./outputs/sounds",results[0].name+".mp3")
    return results[0].name+".mp3"

def concatenate_audio_moviepy(audio_clip_paths, output_path, background_music=None):
    """Concatenates several audio files into one audio file using MoviePy
    and save it to `output_path`. Note that extension (mp3, etc.) must be added to `output_path`"""
    clips = [AudioFileClip(c) for c in audio_clip_paths]
    print(audio_clip_paths)
    final_clip = concatenate_audioclips(clips)

    if background_music is not None:
        final_clip.write_audiofile(background_music)

        backgroundclip = AudioFileClip(background_music).volumex(0.4)
        backgroundclip.set_duration(final_clip.duration)
        end_clip = CompositeAudioClip([backgroundclip, final_clip])

        end_clip.write_audiofile(output_path)

    else:
        final_clip.write_audiofile(output_path)

def play_waiting(file_path, stop_event):
    # Open the wave file
    wf = wave.open(file_path, 'rb')

    # Create a PyAudio object
    p = pyaudio.PyAudio()

    # Open a stream for the wave file
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Start playing the sound, loop waiting
    start = datetime.now()
    while (datetime.now() - start).total_seconds() < 30:
        wf.rewind()
        data = wf.readframes(1024)
        while len(data) > 0 and not stop_event.is_set():
            stream.write(data)
            data = wf.readframes(1024)
            
    # Stop the stream and close it
    stream.stop_stream()
    stream.close()

    # Terminate the PyAudio object
    p.terminate()

@timing
def play_working(file_path, workout_time):
    # Open the wave file
    wf = wave.open(file_path, 'rb')

    # Create a PyAudio object
    p = pyaudio.PyAudio()

    # Open a stream for the wave file
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # Start playing the sound, loop waiting
    start = datetime.now()
    while (datetime.now() - start).total_seconds() < workout_time:
        wf.rewind()
        data = wf.readframes(1024)
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(1024)
            
    # Stop the stream and close it
    stream.stop_stream()
    stream.close()

    # Terminate the PyAudio object
    p.terminate()

    return None