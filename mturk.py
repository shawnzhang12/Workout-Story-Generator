import os
import openai
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def query_chatgpt(prompt, system_prompt, response_length=256,
         temperature=0.7, top_p=1, frequency_penalty=1, presence_penalty=1, **kwargs):
    response = openai.ChatCompletion.create(
            model = 'gpt-3.5-turbo',
            messages = [
                {'role': 'system', 'content': system_prompt},
                {"role": "user", "content": prompt},
                ],
        temperature = temperature,
        top_p = top_p,
        frequency_penalty = frequency_penalty,
        presence_penalty = presence_penalty,
        max_tokens = response_length
    )
    return response['choices'][0]['message']['content'], response["usage"]

if __name__=='__main__':
    storyline = """
    As Rory makes his way towards the village of Dragonwick, he comes across a troupe of wandering painters. 
    Their brightly colored wagons are adorned with intricate designs and patterns that catch his eye. As he approaches, one of the painters steps forward to greet him.
    "Welcome, welcome! You must be a traveler passing through our humble domain," says the painter with a smile.
    Rory nods in agreement and introduces himself as a wizard from the duchy of Birahan. The painter's eyes light up at this news.
    "A wizard! How marvelous! We love meeting folks who practice magic," exclaims the painter.
    Rory smiles politely but can't help but feel uneasy around such enthusiastic strangers. 
    However, before Rory can continue on his journey, he notices something glinting in the grass nearby - an oval amulet lying forgotten on the ground next to one of their wagons.
    Without thinking twice about it, Rory picks up the oval amulet and examines it closely. It seems to glow with an otherworldly energy that thrums beneath his fingertips. 
    Suddenly, another voice interrupts Rory's thoughts:
    "Hey you there! What do you think you're doing touching my things?" barks a small goblin-like creature standing beside him."
    """

    PRE_STORY_WORKOUT_USER="""
    Continue the story where the main character performs a {} motion multiple times in a scenario that is well integrated into the story.
    The main character must exert energy to perform the task.
    It must be a crucial aspect of the story and have good flow.
    It must be very detailed and descriptive. Don't end the story.
    Stop the output right after the main character stops exerting energy.

    Make sure the main character actually performs the {} motion.

    Some motion to scenarios examples are:
    1. Pushing on a surface: pushing blocking objects or heavy door, performing CPR compressions, shoving people in a tight crowd
    2. Hip hinge with weighted bar: lifting up a heavy lever, lower a boat into the water, picking up a long heavy object
    3. Bending torso towards knees: picking up objects, getting up after a fall, resisting someone trying to pin you down
    4. Holding a straight body position: aiming a sniper, hiding without movement, waiting
    """

    motion = "jumping and spreading legs."

    SYSTEM_PROMPT = """
    I want you to act as an interactive, immersive storyteller.
    The story must be in present tense. 
    The story must consist of a narrator, a main character, and a sidekick.
    The narrator must speak in third person. The sidekick must speak directly to me in second person.
    You will come up with entertaining stories that are engaging, imaginative, captivating, thrilling, and suspenseful. 
    The story must have extremely detailed world building, be very descriptive, highly immersive. 
    I want the sidekick to have their own style and vocabulary befitting their role in the story. 
    Always put double double quotation mark quotes around the sidekick's text.
    Never put double or single quotation marks around narrator text. 
    Never put double or single quotation marks around the main character's text.
    """

    prompt = storyline + "\n" + PRE_STORY_WORKOUT_USER.format(motion, motion)

    tts_wpm = 190
    words_to_tokens = 1.4
    rest_time = 45 # half of the total rest time (90s)
    pre_workout_response_length = int((tts_wpm * (rest_time/2) // 60) * words_to_tokens)

    continued_story = query_chatgpt(prompt, SYSTEM_PROMPT, response_length=pre_workout_response_length)
    print(continued_story)

