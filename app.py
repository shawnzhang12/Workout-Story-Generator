import os
import re
import ctypes
import random
import logging
import faulthandler
import threading
import multiprocessing
from multiprocessing import Process, Value
from multiprocessing.pool import Pool
from time import sleep, time
from subprocess import Popen
from TTS.api import TTS

from utils import *
from get_sound import *
from playsound import playsound
from get_workout import get_workout
from get_prompt import query_gpt
from speech_to_text import recognize_speech_from_mic

from flask import Flask, render_template, request, flash, Markup, redirect, url_for, session
from flask_session import Session
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.file import FileAllowed, FileRequired
from wtforms.validators import DataRequired, Length, Regexp
from wtforms.fields import *
from flask_bootstrap import Bootstrap5, SwitchField
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = 'dev'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

# set default button sytle and size, will be overwritten by macro parameters
app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'

# set default icon title of table actions
app.config['BOOTSTRAP_TABLE_VIEW_TITLE'] = 'Read'
app.config['BOOTSTRAP_TABLE_EDIT_TITLE'] = 'Update'
app.config['BOOTSTRAP_TABLE_DELETE_TITLE'] = 'Remove'
app.config['BOOTSTRAP_TABLE_NEW_TITLE'] = 'Create'

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), "inputs")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

bootstrap = Bootstrap5(app)
db = SQLAlchemy(app)
csrf = CSRFProtect(app)


class ExampleForm(FlaskForm):
    """An example form that contains all the supported bootstrap style form fields."""
    date = DateField(description="We'll never share your email with anyone else.")  # add help text with `description`
    datetime = DateTimeField(render_kw={'placeholder': 'this is a placeholder'})  # add HTML attribute with `render_kw`
    datetime_local = DateTimeLocalField()
    time = TimeField()
    month = MonthField()
    floating = FloatField()
    integer = IntegerField()
    decimal_slider = DecimalRangeField()
    integer_slider = IntegerRangeField(render_kw={'min': '0', 'max': '4'})
    email = EmailField()
    url = URLField()
    telephone = TelField()
    image = FileField(render_kw={'class': 'my-class'}, validators=[Regexp('.+\.jpg$')])  # add your class
    option = RadioField(choices=[('dog', 'Dog'), ('cat', 'Cat'), ('bird', 'Bird'), ('alien', 'Alien')])
    select = SelectField(choices=[('dog', 'Dog'), ('cat', 'Cat'), ('bird', 'Bird'), ('alien', 'Alien')])
    select_multiple = SelectMultipleField(choices=[('dog', 'Dog'), ('cat', 'Cat'), ('bird', 'Bird'), ('alien', 'Alien')])
    bio = TextAreaField()
    search = SearchField() # will autocapitalize on mobile
    title = StringField() # will not autocapitalize on mobile
    secret = PasswordField()
    remember = BooleanField('Remember me')
    submit = SubmitField()

class WorkoutForm(FlaskForm):
    """An example form that contains all the supported bootstrap style form fields."""

    starting_prompt = StringField(description="Set up the premise of your very own action/fantasy story however you like!") # will not autocapitalize on mobile
    workout_file = FileField(render_kw={'class': 'my-class'}, validators=[FileRequired(), FileAllowed(['xlsx', 'xls', 'csv'], 'Excel and CSV only!')])  # add your class
    workout_mode = SelectField(choices=[('manual', 'Manual'), ('semi-auto', 'Semi-Auto'), ('full-auto', 'Full-Auto')], 
                               description="How to you want the story to progress? Manual (Respond freely) Semi-Auto (Giving fixed choices) Full-Auto (Automatically, no interaction)") 

    submit = SubmitField()

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    draft = db.Column(db.Boolean, default=False, nullable=False)
    create_time = db.Column(db.Integer, nullable=False, unique=True)

@app.before_first_request
def before_first_request_func():
    db.drop_all()
    db.create_all()
    session.pop('_flashes', None)
    for i in range(20):
        url = 'mailto:x@t.me'
        if i % 7 == 0:
            url = 'www.t.me'
        elif i % 7 == 1:
            url = 'https://t.me'
        elif i % 7 == 2:
            url = 'http://t.me'
        elif i % 7 == 3:
            url = 'http://t'
        elif i % 7 == 4:
            url = 'http://'
        elif i % 7 == 5:
            url = 'x@t.me'
        m = Message(
            text=f'Message {i+1} {url}',
            author=f'Author {i+1}',
            category=f'Category {i+1}',
            create_time=4321*(i+1)
            )
        if i % 4:
            m.draft = True
        db.session.add(m)
    db.session.commit()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/form', methods=['GET', 'POST'])
def test_form():
    form = WorkoutForm()
    if form.validate_on_submit():
        flash('Form validated!')
        starting_prompt = form.starting_prompt.data
        workout_file = secure_filename(form.workout_file.data.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], workout_file)
        form.workout_file.data.save(file_path)
        workout_mode = form.workout_mode.data

        start_story_generation(mode=workout_mode, starting_prompt=starting_prompt, workout_file=file_path)
        return redirect(url_for('test_nav'))
    return render_template(
        'form.html',
        form=form,
        workout_form=WorkoutForm()
    )

@app.route('/nav', methods=['GET', 'POST'])
def test_nav():
    return render_template('nav.html')

@app.route('/table')
def test_table():
    page = request.args.get('page', 1, type=int)
    pagination = Message.query.paginate(page=page, per_page=10)
    messages = pagination.items
    titles = [('id', '#'), ('text', 'Message'), ('author', 'Author'), ('category', 'Category'), ('draft', 'Draft'), ('create_time', 'Create Time')]
    data = []
    for msg in messages:
        data.append({'id': msg.id, 'text': msg.text, 'author': msg.author, 'category': msg.category, 'draft': msg.draft, 'create_time': msg.create_time})
    return render_template('table.html', messages=messages, titles=titles, Message=Message, data=data)


@app.route('/table/<int:message_id>/view')
def view_message(message_id):
    message = Message.query.get(message_id)
    if message:
        return f'Viewing {message_id} with text "{message.text}". Return to <a href="/table">table</a>.'
    return f'Could not view message {message_id} as it does not exist. Return to <a href="/table">table</a>.'


@app.route('/table/<int:message_id>/edit')
def edit_message(message_id):
    message = Message.query.get(message_id)
    if message:
        message.draft = not message.draft
        db.session.commit()
        return f'Message {message_id} has been editted by toggling draft status. Return to <a href="/table">table</a>.'
    return f'Message {message_id} did not exist and could therefore not be edited. Return to <a href="/table">table</a>.'


@app.route('/table/<int:message_id>/delete', methods=['POST'])
def delete_message(message_id):
    message = Message.query.get(message_id)
    if message:
        db.session.delete(message)
        db.session.commit()
        return f'Message {message_id} has been deleted. Return to <a href="/table">table</a>.'
    return f'Message {message_id} did not exist and could therefore not be deleted. Return to <a href="/table">table</a>.'


@app.route('/table/<int:message_id>/like')
def like_message(message_id):
    return f'Liked the message {message_id}. Return to <a href="/table">table</a>.'


@app.route('/table/new-message')
def new_message():
    return 'Here is the new message page. Return to <a href="/table">table</a>.'


def separate_script(script):
    '''
    Separates the script into lines for the narrator, and lines for the sidekick, 
    TODO: assumes all quotes are sidekicks for now, can use gpt model to extract quotes later, dont forget to change temperature
    Returns list: [(line order number, voice actor #, actual line),...]
    '''
    # Remove headers before colon
    lines = script.split("\n")
    processed_lines = [re.sub(r".*?:", "", line) for line in lines]
    script = " ".join(processed_lines)
    script = script.lstrip("\"\n\'\r\t")
    script = script.replace("\n", "")
    if script[0] == '"':  # I Don't get why it adds quotes
        script = script[1:-1]
    print(script)
    print(script[0])
    print(script[1])
    lines = []
    count = 0
    start_quote = True
    current_substring = ""

    for char in script:
        if char == '"':
            if start_quote:
                if current_substring.strip(" ") != "":
                    lines.append((count, 0, current_substring))
                    count += 1
                current_substring = ""
                start_quote = False
            else:
                if current_substring.strip(" ") != "":
                    lines.append((count, 1, current_substring))
                    count += 1
                current_substring = ""
                start_quote = True
        else:
            current_substring += char

    if current_substring.strip() != "":
                    lines.append((count, 0, current_substring))        
    # 0 means narrator, 1 means sidekick
    # Return format [(line order number, voice actor #, actual line),...]

    for line in lines:
        logging.info("Line {} voiced by {}:  {}".format(line[0], line[1], line[2]))
    return lines

# Convert script to audio file with different voice parts
# Use multiprocessing to speed up text to speech conversions
def tts_generate_audio(args):
    tts = TTS("tts_models/en/vctk/vits")
    tts.tts_to_file(text=args[0], speaker=args[1], file_path=args[2])

#@timing
def script_to_speech(lines, speech_dir, iteration_number, other_sounds=None, parallel=True):
    voices = {0: 'p267', 1: 'p273', 2: 'p330', 3:'p234', 4:'230'}
    audio_files = []
    tts = TTS("tts_models/en/vctk/vits")
    if parallel:
         for (order, voice, text) in lines:
            pid = voices[voice]
            output_file = "story_{}_{}_{}.wav".format(iteration_number, order, pid)

            tts.tts_to_file(text=text, speaker=pid, file_path=os.path.join(speech_dir, output_file))

            audio_files.append(os.path.join(speech_dir, output_file))
    else:
        args = []
        for (order, voice, text) in lines:
            pid = voices[voice]
            output_file = "story_{}_{}_{}.wav".format(iteration_number, order, pid)
            args.append((text, pid,os.path.join(speech_dir, output_file)))
            audio_files.append(os.path.join(speech_dir, output_file))
        
        with Pool(multiprocessing.cpu_count()) as pool:
            pool.map(tts_generate_audio, args)
        pool.close()
        pool.join()

    if other_sounds is not None:
        audio_files.append(other_sounds)

    logging.info("Audio Files: {}".format(audio_files))
    for f in audio_files:
        assert os.path.exists(f)
    final_file = os.path.join(speech_dir, "story_{}_combined.wav".format(iteration_number))
    concatenate_audio_moviepy(audio_files, final_file)

    return final_file


def setup_workout(master_storyline, reps, exercise, i, send_end, SPEECH_DIR=None, SOUNDS_DIR=None):
    SIDEKICK_WORKOUT_INTERJECTION = """
    Assume that the sidekick asked the main character "What to do next?" and is given a reply back. 
    Write a response from the sidekick that agrees with the main character ambiguously and 
    continues the story by motivates the main character to do {} {}..
    Always put double quotes around the sidekick's lines.
    Never put quotes around narrator text.
    End with the sidekick giving motivation for the main character to start right now!.
    I want the sidekick to have their own style and vocabulary befitting their role in the story.
    """

    response = query_gpt(master_storyline + "\n" + SIDEKICK_WORKOUT_INTERJECTION.format(reps, exercise), temperature=0.8, response_length=128)
    logging.info("Sidekick Response {}: {}".format(i, response))
    lines = separate_script(response)
    audio_file = script_to_speech(lines,SPEECH_DIR,str(i)+"s",other_sounds=os.path.join(SOUNDS_DIR, "start_tone2.wav"))
    send_end.send((response, audio_file))

def start_story_generation(mode, starting_prompt, workout_file):

    CONST_BEGINNING = """I want you to act as an interactive, immersive storyteller. 
    The story must consist of a narrator, a main character, and a sidekick.
    The narrator must speak in third person. The sidekick must speak directly to me in second person.
    You will come up with entertaining stories that are engaging, imaginative, captivating, thrilling, and suspenseful. 
    The story must have extremely detailed world building and be very descriptive. 
    I want the sidekick to have their own style and vocabulary befitting their role in the story. Always put double quotes around the sidekick's lines.
    Never put quotes around narrator text. Never put quotes around the main character's text.
    I am the main character. Stop text generation when it is the main character's turn to speak. 
    The starting information is {}. Begin the story introduction with the narrator. End the output with the sidekick asking me what to do next."
    """

    CONTINUE_PROMPT = """Continue the story according to the main character's previous response.
    Always put double quotes around the sidekick's lines. Never put quotes around narrator text. Never put quotes around the main character's text.
    The story must have extremely detailed world building and be very descriptive. 
    The narrator must speak in third person. The sidekick must speak directly to me in second person. 
    I am the main character. Stop text generation when it is the main character's turn to speak. 
    I want the sidekick to have their own style and vocabulary befitting their role in the story.
    Don't end the story. End output with the sidekick asking me what to do next."""

    OUTPUT_DIR, SOUNDS_DIR, SPEECH_DIR = folder_creation()
    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', filename=os.path.join(OUTPUT_DIR, "logfile.log"), datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)

    #starting_prompt = 'I am Bob, a knight living in the kingdom of Athens. I have a steel sword and a wooden shield. I am on a quest to defeat the evil dragon of Athens.'
    CONST_BEGINNING = CONST_BEGINNING.format(starting_prompt)

    beginning = True
    main_character_lines =[]

    ## TODO: Handle seconds in workouts
    workout = get_workout(workout_file, shuffle=False)
    logging.info("Workout: {}".format(workout))

    # Use 1 indexing as beginning starts at 0
    for i in range(1, len(workout)+1):

        if beginning:
            exercise = workout[0][0]
            reps = workout[0][1]
            rest_time = workout[0][2]
            logging.info("Current workout is {} {}.".format(reps, exercise))

            #  Begin story
            prompt = CONST_BEGINNING
            master_storyline = query_gpt(prompt)

            logging.info("Storyline 0: {}".format(master_storyline))
            lines = separate_script(master_storyline.strip("\n\r\"\'"))

            audiofile_start = script_to_speech(lines,SPEECH_DIR,0,other_sounds=os.path.join(SOUNDS_DIR, "start_tone1.wav"))
            
            #  Prep workout response
            recv_end, send_end = multiprocessing.Pipe(False)
            workout_setup_process = Process(target=setup_workout, args=(master_storyline, reps, exercise, 0, send_end, SPEECH_DIR, SOUNDS_DIR))
            workout_setup_process.start()

            #  Play story file
            playsound(audiofile_start)
            beginning = False

        if mode == "manual":
            #stop_event = threading.Event()

            faulthandler.enable()
            #waiting_thread = threading.Thread(target=play_waiting, args=(os.path.join(SOUNDS_DIR, "waiting.wav"), stop_event))
            #waiting_thread.start()
            answer = recognize_speech_from_mic(i-1, SPEECH_DIR)

            ## TODO: handle exception when no answer is received within 20 seconds, probably auto generate/continue story
            logging.info("Answer has been accepted from mic.")
            #stop_event.set()
            #waiting_thread.join()

            
            if answer["transcription"]:
                main_character_response = answer["transcription"]
                main_character_lines.append(main_character_response)
                logging.info("Main character Response: {}".format(main_character_response))
            else: 
                print("ERROR: {}".format(answer["error"]))
                exit()   

            workout_setup_process.join()

            sidekick_workout_response, sidekick_audio_file = recv_end.recv()


            playsound(sidekick_audio_file)

            # play workout music and process answer
            #  TODO: Listen specifically for "I'm done", but now just wait 20 seconds
            workout_time = 25
            working_thread = threading.Thread(target=play_working, args=(os.path.join(SOUNDS_DIR, "fast_workout.wav"), workout_time))
            working_thread.start()

            # Add responses to storyline
            master_storyline += "\nMain Character: " + main_character_response
            master_storyline += "\nSidekick: " + sidekick_workout_response


            if i == len(workout):
                working_thread.join()
                break

            # Query GPT for the continuation of the story
            gpt_output = query_gpt(master_storyline + CONTINUE_PROMPT)   
            logging.info("Storyline {}: {}".format(i, gpt_output))
            master_storyline += "\n" + gpt_output

            # Process and prepare audio file for continued story
            lines = separate_script(gpt_output)
            audiofile = script_to_speech(lines,SPEECH_DIR,i,other_sounds=os.path.join(SOUNDS_DIR, "start_tone1.wav"))

            # Begin processing the 'sidekick yes good plan response with workout' before playing the continued story
            exercise = workout[i][0]
            reps = workout[i][1]
            rest_time = workout[i][2]
            logging.info("Current workout is {} {}.".format(reps, exercise))
            
            recv_end, send_end = multiprocessing.Pipe(False)
            workout_setup_process = Process(target=setup_workout, args=(master_storyline, reps, exercise, i, send_end, SPEECH_DIR, SOUNDS_DIR))
            workout_setup_process.start()

            working_thread.join()
            playsound(r"{}".format(audiofile))
            # END MANUAL

        elif mode == "semi-auto":
            exit()
        else:  # mode == "auto"
            exit()


    conclusion = query_gpt(master_storyline + "Conclude the story. The sidekick congratulates the main character on them finishing their workouts.")
    master_storyline += conclusion
    lines = separate_script(conclusion)
    conclusion = script_to_speech(lines,SPEECH_DIR,i+1)
    playsound(conclusion)
    with open(os.path.join(OUTPUT_DIR, "complete_storyline.txt"), "w") as f:
        f.write(master_storyline)     
    print("The End") 

if __name__ == '__main__':
    app.run(debug=True)

# END OF FILE