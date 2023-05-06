"""
This file contains a Flask application that provides an interface for users to create 
and manage workout exercises and start story generation based on workout data.
"""

# Standard libraries
import os
import json
import random

# Third party libraries
import torch
from flask import Flask, render_template, flash, redirect, url_for, request
from flask_session import Session
from flask_wtf import FlaskForm, CSRFProtect
from wtforms.fields import *
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_executor import Executor

# Local modules
from get_prompt import generate_random_prompt
from story_gen_SEQ_METHOD import start_story_generation_SEQ_MODE

# Initializing Flask app and setting configuration parameters
app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(32)
app.config.update({
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///exercises.db',
    'BOOTSTRAP_BTN_STYLE': 'primary',
    'BOOTSTRAP_BTN_SIZE': 'sm',
    'UPLOAD_FOLDER': os.path.join(os.getcwd(), "inputs"),
    'SESSION_PERMANENT': False,
    'SESSION_TYPE': "filesystem",
    'WTF_CSRF_CHECK_DEFAULT': False,
    'BOOTSTRAP_BOOTSWATCH_THEME': 'sketchy'
})
Session(app)

# Initialize the executor after initializing the app
executor = Executor(app)
bootstrap = Bootstrap5(app)
db = SQLAlchemy(app)
csrf_token = CSRFProtect(app)

# Global variables, story complete requests don't go through Flask executor
story_complete = False
count = 0

class Exercise(db.Model):
    """Database model for an exercise."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    reps = db.Column(db.String(10), nullable=False)
    sets = db.Column(db.Integer, nullable=False)


class WorkoutForm(FlaskForm):
    """
    FlaskForm for setting up the workout and starting story generation. 
    Includes a textarea for the starting story prompt and a select field for the workout mode.
    """
    name = StringField(description="What's your name?")
    starting_prompt = TextAreaField(description="Set up the premise of your very own action/fantasy story however you like!", render_kw={"rows": 3}) 
    workout_mode = SelectField(choices=[('Interactive', 'Interactive'), ('Auto', 'Auto')], 
                               description="'Interactive' enables user input to steer the story, 'Auto' lets the story continue by itself.")         
    debug_mode = BooleanField("Debug Mode ON?")  
    exercise_mode = BooleanField("Use actual exercise instead of motion mapping?")           
    gpt_mode = SelectField(choices=[('GPT3.5', 'gpt-3.5-turbo'), ('GPT4', 'gpt4')], 
                               description="Which GPT model do you want for story generation (GPT4 will likely have better stories, but takes longer to generate)")   
    random_prompt = SubmitField()
    submit = SubmitField('Begin Workout!')

@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route, displays the workout form and handles form submissions."""
    form = WorkoutForm()
    exercises = Exercise.query.all()

    if form.random_prompt.data == True:
        if form.name.data is not None and form.name.data is not "":
            form.starting_prompt.data = generate_random_prompt(form.name.data)
        else:
            name = random.choice(["Sebastian", "Rory", "Nolan", "Orlando", "Serena"])
            form.starting_prompt.data = generate_random_prompt(name)
    elif form.submit.data == True:
        if form.validate_on_submit():        
            flash('Loading your story!')
            executor.submit(start_story_generation_SEQ_MODE, 
                            starting_prompt=form.starting_prompt.data, 
                            workout_input=exercises, 
                            gpu=torch.cuda.is_available(), 
                            input_type="audio", 
                            debug=form.debug_mode.data, 
                            model=form.gpt_mode.data,
                            actual_exercise=form.exercise_mode.data)
            return redirect(url_for('test_nav'))

    return render_template('index.html', workout_form=form, exercises=exercises)

@app.route('/get_story_chunks', methods=['GET'])
def get_story_chunks():
    """Returns story chunks from the output file."""
    global story_complete
    global count

    # previous story files
    story_file_path = os.path.join("outputs","master_storyline_{}.txt".format(count))
    old_story_file_path = os.path.join("outputs","master_storyline_{}.txt".format(count-1))

    # If the current story file does not exist yet
    if not os.path.exists(story_file_path):
        # If the old story file does not exist yet
        if not os.path.exists(old_story_file_path):
            return json.dumps({"chunks": [], "completed": False})
        else:
            with open(old_story_file_path, "r") as story_file:
                story_chunks = story_file.readlines()
                return json.dumps({"chunks": story_chunks, "completed": story_complete})

    # If the current story file exists
    with open(story_file_path, "r") as story_file:
        story_chunks = story_file.readlines()
        count += 1
    return json.dumps({"chunks": story_chunks, "completed": story_complete})

@app.route('/story', methods=['GET', 'POST'])
def test_nav():
    """Returns the story navigation page."""
    return render_template('nav.html')

@app.before_first_request
def init_tables():
    """Initializes the database tables before the first request."""
    db.drop_all()
    db.create_all()

@app.before_request
def check_csrf():
    """Placeholder for adding CSRF check for AJAX requests."""
    pass

@app.route('/add', methods=['POST'])
def add_exercise():
    """Adds a new exercise to the database."""
    data = request.get_json()
    new_exercise = Exercise(name=data['name'], reps=data['reps'], sets=data['sets'])
    db.session.add(new_exercise)
    db.session.commit()
    return redirect('/')

@app.route('/delete', methods=['POST'])
def delete_exercise():
    """Deletes an exercise from the database."""
    data = request.get_json()
    exercise_id = data['id']
    exercise = Exercise.query.get(exercise_id)
    db.session.delete(exercise)

    exercises = Exercise.query.order_by(Exercise.id).all()
    # Update each exercise's ID to its index in the sorted list
    for i, exercise in enumerate(exercises):
        exercise.id = i

    db.session.commit()
    return redirect('/')

@app.route('/update', methods=['POST'])
def update_exercise():
    """Updates an existing exercise in the database."""
    data = request.get_json()
    exercise_id = data['id']
    exercise = Exercise.query.get(exercise_id)
    exercise.name = data['name']
    exercise.reps = data['reps']
    exercise.sets = data['sets']
    db.session.commit()
    return redirect('/')    

if __name__ == '__main__':
    """Run the Flask app."""
    app.run(debug=True)