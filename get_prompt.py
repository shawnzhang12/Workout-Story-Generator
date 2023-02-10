import os
import openai
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff
from utils import timing


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
def query_gpt(prompt, engine='text-davinci-003', response_length=256,
         temperature=0.5, top_p=1, frequency_penalty=1, presence_penalty=1,
         start_text='', restart_text='', stop_seq=[], **kwargs):
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