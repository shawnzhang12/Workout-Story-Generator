## Workout Story Generator

### This project is a fun application of GPT's story generation capabilities integrated with a customizable workout routine for a more engaging, immersive workout. 

Some people (referring to myself) tend to be bored of the monotonous, repetitive nature of exercise routines and lose motivation to persist or even start. 
Also, it's easy to get distracted between sets as there is nothing really to do but be browse your phone -- a dangerous context switch. 
![](/static/home_page.png)

Here are some of the project features that would help keep your full attention during the workout:

- Full Audio-based Storytelling and Interaction :sound: (no reading or typing)

- You are the main protagonist! :mage: You have a sidekick who will <u>regularly converse with you</u> through speaker/microphone in real-time so how the story plays out is up to you! There is also a narrator, who has a different voice profile than the sidekick for easy differentiation.

- Workout exercises are integrated into the story:muscle:. Your story self will perform similar motions to overcome challenges.

- Fully customizable workouts :grin:

- The rest time between sets? Now enjoy listening to the story advancements! :relieved:


### Getting Started

#### Prerequisites

- Python 3.8 (Have not tested yet on other python versions)
- An OpenAI account and API key (free signup) [https://openai.com/api/login](https://openai.com/api/login)
- (Windows Only) ESpeak-ng [https://github.com/espeak-ng/espeak-ng/releases](https://github.com/espeak-ng/espeak-ng/releases)

#### Installation

1. Open up a terminal, clone the repo

   ```sh
   git clone https://github.com/shawnzhang12/Workout-Story-Generator.git 
   ```

2. Create a `.env` in the root directory with the same contents as `example.env`

3. Replace `"INSERT KEY HERE"` with your OpenAI API Key (create one from your account)

4. Create a virtual environment (venv or conda) and activate the environment

   ```sh
   python -m venv env
   ```

   ```sh
   source env/Scripts/activate (Windows) OR source env/bin/activate (LINUX)
   ```

5. Install the required packages

   CPU: `pip install requirements_cpu.txt`

   GPU: `pip install requirements_gpu.txt`

6. Run the flask interface, open up `http://localhost:5000` and enjoy!

   ```sh
   flask run
   ```

### Roadmap
- [ ] Still in development, may break while adding improvements
- [ ] Finetune prompts, optimize for speed
- [ ] Host on a website
- [ ] Add actions workflow for CD
