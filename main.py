import os
import re
import sys
import argparse
import csv
import random
from moviepy.editor import *
from get_workout import get_workout
from get_sound import get_sound
from get_prompt import get_prompt
from text_to_speech import text_to_speech

def concatenate_audio_moviepy(audio_clip_paths, output_path, background_music):
    """Concatenates several audio files into one audio file using MoviePy
    and save it to `output_path`. Note that extension (mp3, etc.) must be added to `output_path`"""
    clips = [AudioFileClip(c + ".wav") for c in audio_clip_paths]
    print(audio_clip_paths)
    final_clip = concatenate_audioclips(clips)
    final_clip.write_audiofile("final_test.mp3")

    backgroundclip = AudioFileClip(background_music).volumex(0.4)
    backgroundclip.set_duration(final_clip.duration)
    end_clip = CompositeAudioClip([backgroundclip, final_clip])

    end_clip.write_audiofile(output_path)

# use the world info memory ai dungeon next
def chat(prompt, **kwargs):
    answer = get_prompt(prompt,
                              temperature=0.7,
                              frequency_penalty=1,
                              presence_penalty=1,
                              start_text='',
                              restart_text='', **kwargs)
    return answer


if __name__ == '__main__':
    workout = get_workout("inputs/workout1.csv", shuffle=True)

    initial_prompt = """You are John, a knight living in the kingdom of Larion. You have a steel sword and a wooden shield. You are on a quest to defeat the evil dragon of Larion."""
    # initial_prompt = """You are Luke Skywalker, Jedi Knight. Boba Fett is hunting you. You need to escape."""
    prompt = initial_prompt

    count = 0
    storyline = prompt
    story_chunks = []
    action_prompts = []
    sounds = []
    sound_times = []

    # Still need to incorporate rest times
    for w in workout:
        exercise = w[0]
        reps = w[1]
        rest_time = w[2]
        verbs = chat("give me 2 action verbs separated by commas that can describe {}.".format(w[0]))
        verbs = verbs.strip(" \n").split(", ")
        action = random.choice(verbs)
        print(verbs, action)
 
        # Check if reps are seconds or count
        # Get the responses here

        if exercise == "Handstands":
            hold_time = reps
            answer = chat(prompt + "Continue the story with John doing a {}-second {}, don't end the story.".format(hold_time, exercise)) 
            action_prompt = "(Start your {} second {} now!)".format(hold_time, exercise)
        else:
            answer = chat(prompt + "Continue the story with John doing {} {}, don't end the story.".format(reps, exercise))      
            action_prompt = "(Start your {} {} now!)".format(reps, exercise) 

        storyline += answer + action_prompt
        
        sound = None
        response_length = 4
        while sound is None:
            sound_query = chat("Describe the following text as a simple sound effect using 2 words.\n {}".format(answer), response_length=response_length)
            sound = get_sound(sound_query)
            response_length -= 1
            if response_length == 0:
                sound = "heartbeat-60bpm.wav.mp3"
                break

        # Add story chunks, action prompts, and sounds to storage
        story_chunks.append(answer)
        action_prompts.append(action_prompt)
        sounds.append(sound)
        sound_times.append(int(reps))
        print(sounds)

        prompt = prompt + answer
        action_prompt = ""

        # print("RESULTS GENERATION ", count)
        # print("Exercise: ", w[0])
        # print("Action: ", action)
        # print("Answer: ", answer)
        # print("Sound Query: ", sound_query)
        # print("END")
        # print("")

        count += 1

        # End it
        if count > 3: 
            answer = chat(prompt + "Conclude the story")
            story_chunks.append(answer)
            storyline += answer
            print("Final Story")
            print(storyline)
            break

    # Now to form the audio file
    sounds_dir = "./outputs/sounds/"
    speech_dir = "./outputs/speech/"
    background_dir = "./outputs/backgrounds/"

    list_of_audios = [speech_dir + "story_prompt.mp3"]
    text_to_speech(initial_prompt, output_file="story_prompt.mp3")
    for i in range(len(action_prompts)):
        print(story_chunks[i])
        text_to_speech(story_chunks[i], output_file="story{}.mp3".format(i), output_dir=speech_dir)
        text_to_speech(action_prompts[i], output_file="action_prompts{}.mp3".format(i), output_dir=speech_dir, pid='p257')

        audio = AudioFileClip(sounds_dir + sounds[i])
        audio = afx.audio_loop(audio, duration=int(sound_times[i]))
        audio.write_audiofile(background_dir + "background{}.mp3.wav".format(i))
        audio.close()

        list_of_audios.append(speech_dir + "story{}.mp3".format(i))
        list_of_audios.append(speech_dir + "action_prompts{}.mp3".format(i))
        list_of_audios.append(background_dir + "background{}.mp3".format(i))

    # Add concluding story part
    text_to_speech(story_chunks[-1], output_file="story_end.mp3", output_dir=speech_dir)
    list_of_audios.append(speech_dir + "story_end.mp3")

    background_music = "./medieval_music.mp3"
    concatenate_audio_moviepy(list_of_audios, "./outputs/finalstoryv2n2.mp3", background_music)


    