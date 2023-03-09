import json
import os
import random
import tracery
from tracery.modifiers import base_english


def apply_grammar(key, rules):
    grammar = tracery.Grammar(rules)
    grammar.add_modifiers(base_english)
    return grammar.flatten("#{}#".format(key))


def load_rules(setting):
    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "grammar", "{}_rules.json".format(setting)
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

if __name__=='__main__':
    choices = {"fantasy": ["knight", "wizard", "peasant", "rogue", "noble"], "apocalyptic": ["mutant", "headhunter"]}

    genre = random.choice(list(choices))
    character_type = random.choice(list(choices[genre]))

    context = generate(genre, character_type, "context")
    prompt = generate(genre, character_type, "prompt") + "..."
    name = "Shawn"
    context = context.replace("<NAME>", name)
    print(context)
    print(prompt)