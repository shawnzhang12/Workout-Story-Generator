import os
import freesound
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("FREESOUND_CLIENT_ID")
client_secret = os.getenv("FREESOUND_API_KEY")

client = freesound.FreesoundClient()
client.set_token(client_secret, "token")

def get_sound(query):
    results = client.text_search(query=query,fields="id,name,previews")
    count = 0
    for sound in results:
        sound.retrieve_preview("./outputs/sounds",sound.name+".mp3")
        print("Sound Name: ", sound.name)
        count += 1
        if count > 2:
            break



