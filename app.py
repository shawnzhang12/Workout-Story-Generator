import os
import sys
from get_prompt import generate_random_prompt
from story_gen import start_story_generation
from story_gen_SEQ_METHOD import start_story_generation_SEQ_MODE

from flask import Flask, render_template, request, flash, redirect, url_for
from flask_session import Session
from flask_wtf import FlaskForm, CSRFProtect
from wtforms.validators import DataRequired, Length
from wtforms.fields import *
from flask_bootstrap import Bootstrap5, SwitchField
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(32)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exercises.db'

# set default button sytle and size, will be overwritten by macro parameters
app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), "inputs")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

app.config['WTF_CSRF_CHECK_DEFAULT'] = False

# TODO: Add theme as a toggle
app.config['BOOTSTRAP_BOOTSWATCH_THEME'] = 'sketchy'
Session(app)

bootstrap = Bootstrap5(app)
db = SQLAlchemy(app)
csrf_token = CSRFProtect(app)

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    reps = db.Column(db.String(10), nullable=False)
    sets = db.Column(db.Integer, nullable=False)

# Consult Flask Bootstrap 5 for documentation: https://github.com/helloflask/bootstrap-flask
class WorkoutForm(FlaskForm):
    starting_prompt = TextAreaField(description="Set up the premise of your very own action/fantasy story however you like!", render_kw={"rows": 3}) 
    workout_mode = SelectField(choices=[('Interactive', 'Interactive'), ('Auto', 'Auto')], 
                               description="'Interactive' enables user input to steer the story, 'Auto' lets the story continue by itself.")                      
    random_prompt = SubmitField()
    submit = SubmitField('Begin Workout!')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = WorkoutForm()
    exercises = Exercise.query.all()

    if form.random_prompt.data == True:
       form.starting_prompt.data = generate_random_prompt("Shawn")
       return render_template(
        'index.html',
        workout_form=form,
        exercises=exercises
        )
    elif form.submit.data == True:
        if form.validate_on_submit():        
            flash('Loading your story!')
            starting_prompt = form.starting_prompt.data
            workout_mode = form.workout_mode.data
            #TODO: Merge with legacy start story
            start_story_generation_SEQ_MODE(starting_prompt=starting_prompt, workout_input=exercises)
            return redirect(url_for('test_nav'))

    return render_template(
        'index.html',
        workout_form=form,
        exercises=exercises
    )

@app.route('/nav', methods=['GET', 'POST'])
def test_nav():
    return render_template('nav.html')

@app.before_first_request
def init_tables():
    db.drop_all()
    db.create_all()

@app.before_request
def check_csrf():
    #TODO: ADD CSRF check for ajax request
    pass

@app.route('/add', methods=['POST'])
def add_exercise():
    data=request.get_json()
    name = data['name']
    reps = data['reps']
    sets = data['sets']
    new_exercise = Exercise(name=name, reps=reps, sets=sets)
    db.session.add(new_exercise)
    db.session.commit()
    return redirect('/')

@app.route('/delete', methods=['POST'])
def delete_exercise():
    data=request.get_json()
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
    data=request.get_json()
    exercise_id = data['id']
    exercise = Exercise.query.get(exercise_id)
    exercise.name = data['name']
    exercise.reps = data['reps']
    exercise.sets = data['sets']
    db.session.commit()
    return redirect('/')    
  
if __name__ == '__main__':
    app.run(debug=True)