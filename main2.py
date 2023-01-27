import os
import re
import random
from utils import *
from playsound import playsound
from moviepy.editor import *
from get_workout import get_workout
from get_sound import get_sound
from get_prompt import query_gpt
from text_to_speech import text_to_speech
from speech_to_text import recognize_speech_from_mic

def concatenate_audio_moviepy(audio_clip_paths, output_path, background_music=None):
    """Concatenates several audio files into one audio file using MoviePy
    and save it to `output_path`. Note that extension (mp3, etc.) must be added to `output_path`"""
    clips = [AudioFileClip(c + ".wav") for c in audio_clip_paths]
    print(audio_clip_paths)
    final_clip = concatenate_audioclips(clips)

    if background_music is not None:
        final_clip.write_audiofile("no_music.mp3")

        backgroundclip = AudioFileClip(background_music).volumex(0.4)
        backgroundclip.set_duration(final_clip.duration)
        end_clip = CompositeAudioClip([backgroundclip, final_clip])

        end_clip.write_audiofile(output_path)

    else:
        final_clip.write_audiofile(output_path)


# Returns two lists of text, one for the narrator lines and one for the sidekick lines
def separate_script(script):
    narrator_lines = re.findall(r'<n>(.*?)</n>', script)
    sidekick_lines = re.findall(r'<s>(.*?)</s>', script)
    print(script)
    print(narrator_lines)
    print(sidekick_lines)
    print(len(narrator_lines))
    print(len(sidekick_lines))
    assert len(narrator_lines) >= len(sidekick_lines)
    return narrator_lines, sidekick_lines

def script_to_speech(narrator_lines, sidekick_lines, speech_dir, iteration_number):
    audio_files = []
    for i in range(len(narrator_lines)):
        output_file = "narration_lines_{}_{}.mp3".format(iteration_number, i)
        text_to_speech(narrator_lines[i], output_file=output_file, output_dir=speech_dir, pid='p257')
        audio_files.append(os.path.join(speech_dir, output_file))

        if i < len(sidekick_lines):
            output_file = "sidekick_lines_{}_{}.mp3".format(iteration_number, i)
            text_to_speech(sidekick_lines[i], output_file=output_file, output_dir=speech_dir, pid='p260')
            audio_files.append(os.path.join(speech_dir, output_file))
    
    final_file = "./outputs/test_main2_{}.mp3".format(iteration_number)
    concatenate_audio_moviepy(audio_files, final_file)

    return final_file


def main(workout_file=None, starting_prompt=None):
    workout = get_workout(workout_file, shuffle=True)

    prompt = CONST_BEGINNING.format(starting_prompt)
    count = 0
    
    main_character_lines =[]
    story_chunks = [prompt]

    storyline = query_gpt(prompt)
    n, s = separate_script(storyline)

    audiofile0 = script_to_speech(n,s,SPEECH_DIR,0)
    playsound(audiofile0)

    for iteration, w in enumerate(workout):
        exercise = w[0]
        reps = w[1]
        rest_time = w[2]

        for j in range(PROMPT_LIMIT):
            print("Begin talking")
            answer = recognize_speech_from_mic()
            if answer["transcription"]:
                answer_text = answer["transcription"]
                main_character_lines.append(answer_text)
                break
            if not answer["success"]:
                break
            print("I didn't catch that. What did you say?\n")
        if answer["error"]:
            print("ERROR: {}".format(answer["error"]))
            break

        gpt_output = query_gpt(storyline + "\n" + answer_text + "\n" + """Continue the story with dialogue between the narrator and the sidekick.  
        Start and end narrator text with <n> and </n>. Start and end sidekick text with <s> and </s>. 
        End with the sidekick telling me to do {} {} as part of storyline in second person narrative. It can be humourous. Don't end the story.""".format(reps, exercise))   


        storyline += gpt_output

        n, s = separate_script(gpt_output)
        audiofile = script_to_speech(n,s,SPEECH_DIR,iteration)
        playsound(audiofile)

        count += 1
        if count == 3: 
            conclusion = query_gpt(prompt + "Conclude the story")
            storyline += conclusion
            n, s = separate_script(gpt_output)
            conclusion = script_to_speech(n,s,SPEECH_DIR,conclusion)
            playsound(conclusion)
            print("Final Story")
            print(storyline)
            break


if __name__ == '__main__':
    CONST_BEGINNING = """I want you to act as an interactive storyteller with me, like a dungeon master from Dungeons & Dragons. 
    The story will consists of a narrator, a main character, a sidekick, and potential adventures or enemies.
    You will come up with entertaining stories that are engaging, imaginative and captivating that will have dialogue for a narrator and a sidekick. 
    The narrator will speak in third person while the sidekick will speak in second person.
    The story must have extremely detailed world building and be very descriptive. 
    I want the sidekick to have their own manners and vocabulary befitting their role in the story.  
    Start and end narrator text with <n> and </n>. Start and end sidekick text with <s> and </s>. 
    I will be the main character, so stop text generation when it is the main character's turn to speak. 
    The starting information is {}. Begin the story now. End with a question from the sidekick directed towards me."
    """

    PROMPT_LIMIT = 3
    OUTPUT_DIR = folder_creation()
    SOUNDS_DIR = os.join(OUTPUT_DIR, "sounds")
    SPEECH_DIR = os.join(OUTPUT_DIR, "speech")
    BACKGROUND_DIR = os.join(OUTPUT_DIR, "backgrounds")

    workout_file = "inputs/workout1.csv"
    starting_prompt = """I am John, a knight living in the kingdom of Larion. I have a steel sword and a wooden shield. I am on a quest to defeat the evil dragon of Larion."""

    main(workout_file=workout_file, starting_prompt=starting_prompt)
