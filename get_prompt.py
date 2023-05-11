import os
import openai
import random
import tracery
import json
from dotenv import load_dotenv
from tracery.modifiers import base_english
from tenacity import retry, stop_after_attempt, wait_random_exponential

# Load environment variables
load_dotenv()

# Set OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Choices for generating random prompts
PROMPT_CHOICES = {
    "fantasy": ["knight", "wizard", "peasant", "rogue", "noble"],
    "apocalyptic": ["headhunter"],
}

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def query_chatgpt(prompt, system_prompt, model="gpt-3.5-turbo", response_length=256,
                  temperature=0.7, top_p=1, frequency_penalty=1, presence_penalty=1):
    """Create a chat completion with OpenAI's GPT-3."""
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        max_tokens=response_length
    )
    return response['choices'][0]['message']['content'], response["usage"]

def apply_grammar(key, rules):
    """Apply grammar rules to the key and return the modified string."""
    grammar = tracery.Grammar(rules)
    grammar.add_modifiers(base_english)
    return grammar.flatten("#{}#".format(key))

def load_rules(setting):
    """Load grammar rules from a JSON file."""
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "grammar", "{}_rules.json".format(setting)), "r") as f:
        rules = json.load(f)
    return rules

def generate_prompt(setting, character_type, key):
    """Generate a randomized prompt according to the loaded grammar rules."""
    rules = load_rules(setting)
    return apply_grammar("{}_{}".format(character_type, key), rules)

def generate_random_prompt(name):
    """Generate a random prompt based on pre-defined choices and a given name."""
    genre = random.choices(list(PROMPT_CHOICES.keys()), weights=(5, 1), k=1)[0]
    character_type = random.choice(PROMPT_CHOICES[genre])

    context = generate_prompt(genre, character_type, "context").replace("<NAME>", name)
    prompt = generate_prompt(genre, character_type, "prompt") + "..."

    return (context + " " + prompt).replace("\n", " ")