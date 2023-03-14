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
    for i in range(len(response['choices'][0])):
        print(response['choices'][i]['message']['content'])
    return response['choices'][0]['message']['content']

if __name__=='__main__':
    system_prompt = """You will describe a physical exercise under 5 words.
                Be general enough that people can guess what exercise it is. Make it independent of body orientation. One example description: 
                    pushup maps to pushing against a surface."""
    final_answer = query_chatgpt('situp', system_prompt)
    print(final_answer)


