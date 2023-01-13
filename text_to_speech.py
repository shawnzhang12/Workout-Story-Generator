import pyttsx3
import subprocess
def text_to_speech(text, output_file = "tts.mp3", output_dir = "outputs/speech/", pid='p236'):
   subprocess.run(["tts", "--text", text, "--model_name", "tts_models/en/vctk/vits", "--out_path", "{}{}.wav".format(output_dir, output_file), "--speaker_idx", "{}".format(pid)])