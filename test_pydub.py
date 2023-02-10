from pydub import AudioSegment
from pydub.playback import play

sound = AudioSegment.from_file("story_sounds/waiting.wav", format="wav")

# pydub does things in milliseconds
five_seconds = 5 * 1000

first_five_seconds = sound[:five_seconds]
play(first_five_seconds)
play(first_five_seconds)