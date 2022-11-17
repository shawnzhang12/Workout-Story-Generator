import os

from get_sound import get_sound
from get_prompt import get_prompt


def chat():
    prompt = """Human: Hey, how are you doing?
AI: I'm good! What would you like to chat about?
Human:"""
    while True:
        prompt += input('You: ')
        answer, prompt = get_prompt(prompt,
                              temperature=0.9,
                              frequency_penalty=1,
                              presence_penalty=1,
                              start_text='\nAI:',
                              restart_text='\nHuman: ',
                              stop_seq=['\nHuman:', '\n'])
        print('GPT-3:' + answer)


if __name__ == '__main__':
    get_sound("dubstep")