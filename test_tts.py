from TTS.api import TTS

# Running a multi-speaker and multi-lingual model

# List available 🐸TTS models and choose the first one
model_name = TTS.list_models()[0]
# Init TTS
tts = TTS("tts_models/en/vctk/vits")
print(tts.speakers)
tts.tts_to_file(text="Hello world!", speaker=tts.speakers[0], file_path="test_tts.wav")

# Convert script to audio file with different voice parts
# Use multiprocessing to speed up text to speech conversions
# @timing
# def script_to_speech(lines, speech_dir, iteration_number, other_sounds = None):
#     voices = {0: 'p257', 1: 'p263'}
#     commands = []
#     audio_files = []
#     for (order, voice, text) in lines:
#         pid = voices[voice]
#         output_file = "story_{}_{}_{}.wav".format(iteration_number, order, pid)
#         commands.append(["tts", "--text", text, "--model_name", "tts_models/en/vctk/vits", "--out_path", "{}".format(os.path.join(speech_dir, output_file)), "--speaker_idx", "{}".format(pid)])
#         audio_files.append(os.path.join(speech_dir, output_file))
        

#     if other_sounds is not None:
#         audio_files.append(other_sounds)

#     logging.info("Audio Files: {}".format(audio_files))
#     procs = [Popen(i) for i in commands]
#     for p in procs:
#         p.wait()
#     sleep(0.5)

#     final_file = os.path.join(speech_dir, "story_{}_combined.wav".format(iteration_number))
#     concatenate_audio_moviepy(audio_files, final_file)

#     return final_file

# Python API only exists in TTS version 0.10.0 and above, only appears Dec 2022 so pretty recent
# def script_to_speech(lines, speech_dir, iteration_number, other_sounds = None):
#     voices = {0: 'p257', 1: 'p263'}
#     commands = []
#     audio_files = []
#     ts = time()
#     tts = TTS("tts_models/en/vctk/vits")
#     for (order, voice, text) in lines:
#         pid = voices[voice]
#         output_file = "story_{}_{}_{}.wav".format(iteration_number, order, pid)
#         commands.append(threading.Thread(target = (lambda: tts.tts_to_file(text=text, speaker=pid, file_path= os.path.join(speech_dir, output_file)))))
#         audio_files.append(os.path.join(speech_dir, output_file))
        

#     if other_sounds is not None:
#         audio_files.append(other_sounds)

#     logging.info("Audio Files: {}".format(audio_files))
#     for thread in commands:
#         thread.start()

#     for thread in commands:
#         thread.join()
#     sleep(1)

#     final_file = os.path.join(speech_dir, "story_{}_combined.wav".format(iteration_number))
#     concatenate_audio_moviepy(audio_files, final_file)
#     te = time()
#     logging.info("func:{} took: {:.2f} sec".format("script_to_speech", te-ts))
#     return final_file