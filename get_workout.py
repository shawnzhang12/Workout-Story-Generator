import csv
import random
from typing import List, Union

def get_workout(input_data: Union[str, List], shuffle: bool = False) -> List:
    """
    Generates a workout from a CSV file or a list of Exercise objects.

    Parameters
    ----------
    input_data : Union[str, List]
        Either a path to a CSV file or a list of Exercise objects.
    shuffle : bool, optional
        If True, shuffles the resulting workout list.

    Returns
    -------
    List
        A list of workouts, each workout is a list [exercise_name, reps, rest_time].
    """
    workout = []

    if isinstance(input_data, list):  # List of exercise objects
        for exercise in input_data:
            for _ in range(exercise.sets):
                workout.append([exercise.name, exercise.reps, 90])
    else:  # CSV File
        with open(input_data, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                for _ in range(int(row["Sets"])):
                    workout.append([row["Exercise"], row["Reps"], row["Rest Time"]])

    if shuffle:
        random.shuffle(workout)

    return workout