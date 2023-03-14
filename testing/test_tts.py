from TTS.api import TTS

# Init TTS
tts = TTS("tts_models/en/vctk/vits")
print(tts.speakers)
text="""You are John, a headhunter trying to survive after the British bombed your country to the ground. You have an old rifle and an old gas mask.
    You are drinking with a stranger in a bar, but you need to get going. 
    You decide to leave the building. You are on a mission to kill a captain named Simone. Your target lives in a nearby city."""
text=""", and stopped for the world."""
tts.tts_to_file(text=text, speaker='p267', file_path="test_tts.wav")