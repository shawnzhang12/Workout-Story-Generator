import os
import csv
import random
from get_workout import get_workout
from get_sound import get_sound
from get_prompt import get_prompt
from text_to_speech import text_to_speech

# store past 5 sentences as prompt for now
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
    prompt = """You are John, a knight living in the kingdom of Larion. You have a steel sword and a wooden shield. You are on a quest to defeat the evil dragon of Larion."""


    count = 0
    storyline = prompt
    for w in workout:
        verbs = chat("give me 3 action verbs separated by commas that can describe {}.".format(w[0]))
        verbs = verbs.strip(" \n").split(", ")
        action = random.choice(verbs)
        if count == 5:
            answer = chat(prompt + "Conclude the story with the character performing {} actions.".format(action))
            storyline += answer
        else: 
            answer = chat(prompt + "Continue the story with the character performing {} actions.".format(action))
            storyline += answer + "(Start your {} {} now!)".format(w[1],w[0])

        sound_query = chat("Describe the following text as a simple sound effect using 2 words.\n {}".format(answer), response_length=5)
        sound = get_sound(sound_query)
        prompt = prompt + answer
        print("RESULTS GENERATION ", count)
        print("Exercise: ", w[0])
        print("Action: ", action)
        print("Answer: ", answer)
        print("Sound Query: ", sound_query)
        print("END")
        print("")
        count += 1
        if count > 5: 
            print("Final Story")
            print(storyline)
            break
    text_to_speech(storyline)