import csv
import random
def get_workout(file, shuffle=False):
    workout = []
    with open(file, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            for set in range(int(row["Sets"])):
                workout.append([row["Exercise"],row["Reps"],row["Rest Time"]])
    if shuffle:
        random.shuffle(workout)
    return workout
