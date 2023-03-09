from app import start_story_generation


if __name__=="__main__":
    starting_prompt = """You are Shawn, a headhunter trying to survive after the British bombed your country to the ground. You have an old rifle and an old gas mask.
    You are drinking with a stranger in a bar, but you need to get going. 
    You decide to leave the building. You are on a mission to kill a captain named Simone. Your target lives in a nearby city."""
    workout_file = "./inputs/workout1.csv"
    start_story_generation(mode="auto", starting_prompt=starting_prompt, workout_file=workout_file, verbs=True)