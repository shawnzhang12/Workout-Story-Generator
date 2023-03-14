import os
import openai
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

import json
import random
import tracery
from tracery.modifiers import base_english

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def query_gpt(prompt, engine='text-davinci-003', response_length=800,
         temperature=0.7, top_p=1, frequency_penalty=1, presence_penalty=1, **kwargs):
    response = openai.Completion.create(
        prompt=prompt,
        engine=engine,
        max_tokens=response_length,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
    )
    answer = response.choices[0]['text']
    return answer

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def query_chatgpt(prompt, system_prompt, response_length=512,
         temperature=0.7, top_p=1, frequency_penalty=1, presence_penalty=1, **kwargs):
    response = openai.ChatCompletion.create(
            model = 'gpt-3.5-turbo',
            messages = [
                {'role': 'system', 'content': system_prompt},
                {"role": "user", "content": prompt},
                ],
    temperature = 0.5
    )
    return response['choices'][0]['message']['content']


def apply_grammar(key, rules):
    grammar = tracery.Grammar(rules)
    grammar.add_modifiers(base_english)
    return grammar.flatten("#{}#".format(key))


def load_rules(setting):
    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "grammar", "{}_rules.json".format(setting)
        ),
        "r",
    ) as f:
        rules = json.load(f)
    return rules


def generate(setting, character_type, key):
    """
    Provides a randomized prompt according to the grammar rules in <setting>_rules.json
    """
    rules = load_rules(setting)
    artefact = apply_grammar("{}_{}".format(character_type, key), rules)
    return artefact


def direct(setting, key):
    rules = load_rules(setting)
    artefact = apply_grammar(key, rules)
    return artefact

def generate_random_prompt(name):
    choices = {"fantasy": ["knight", "wizard", "peasant", "rogue", "noble"], "apocalyptic": ["mutant", "headhunter"]}

    genre = random.choice(list(choices))
    character_type = random.choice(list(choices[genre]))

    context = generate(genre, character_type, "context")
    prompt = generate(genre, character_type, "prompt") + "..."
    context = context.replace("<NAME>", name)
    
    random_prompt = context + " " + prompt
    random_prompt = random_prompt.replace("\n", " ")
    return random_prompt