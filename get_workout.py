import csv
import random

# input can be either a file (used for tesing) or an Exercise object
def get_workout(file, shuffle=False):
    workout = []

    if isinstance(file, list):  # List of exercise objects
        for row in file:
            for _ in range(row.sets):

                    workout.append([row.name,row.reps,90])
    else:  # CSV File
        with open(file, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                for _ in range(int(row["Sets"])):
                    workout.append([row["Exercise"],row["Reps"],row["Rest Time"]])
        if shuffle:
            random.shuffle(workout)
    return workout
