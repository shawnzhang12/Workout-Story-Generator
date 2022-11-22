import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_prompt(prompt, engine='text-davinci-002', response_length=256,
         temperature=0.7, top_p=1, frequency_penalty=0, presence_penalty=0,
         start_text='', restart_text='', stop_seq=[]):
    response = openai.Completion.create(
        prompt=prompt + start_text,
        engine=engine,
        max_tokens=response_length,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
    )
    answer = response.choices[0]['text']
    return answer