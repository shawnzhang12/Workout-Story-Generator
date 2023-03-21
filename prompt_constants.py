
BEGINNING = "The starting information is {}. Begin the story introduction with the narrator."

SYSTEM_PROMPT = """
I want you to act as an interactive, immersive storyteller.
The story must be in present tense. 
The story must consist of a narrator, a main character, and a sidekick.
The narrator must speak in third person. The sidekick must speak directly to me in second person.
You will come up with entertaining stories that are engaging, imaginative, captivating, thrilling, and suspenseful. 
The story must have extremely detailed world building, be very descriptive, highly immersive. 
I want the sidekick to have their own style and vocabulary befitting their role in the story. 
Always put double double quotation mark quotes around the sidekick's text.
Never put double or single quotation marks around narrator text. 
Never put double or single quotation marks around the main character's text.
"""

# SPEED SHOULD BE CONSIDERED situp = explosive, russian deadlift = slow, plank = static
CONTINUE_USER_RESPONSE = """
The main character want to do this: {}. 
Continue the story in the direction of the main character response.
"""

PRE_STORY_WORKOUT_USER="""
Continue the story where the main character performs a {} motion multiple times in a scenario that is well integrated into the story.
The main character must exert energy to perform the task.
It must be a crucial aspect of the story and have good flow.
It must be very detailed and descriptive. Don't end the story.
Stop the output right after the main character stops exerting energy.

Make sure the main character actually performs the {} motion.

Some motion to scenarios examples are:
1. Pushing on a surface: pushing blocking objects or heavy door, performing CPR compressions, shoving people in a tight crowd
2. Hip hinge with weighted bar: lifting up a heavy lever, lower a boat into the water, picking up a long heavy object
3. Bending torso towards knees: picking up objects, getting up after a fall, resisting someone trying to pin you down
4. Holding a straight body position: aiming a sniper, hiding without movement, waiting
"""

PRE_STORY_WORKOUT_HOLD_USER="""
Continue the story where the main character holds a relevant {} motion in a scenario that is well integrated into the story.
The main character must exert energy to perform the task.
It must be a crucial aspect of the story and have good flow.
It must be very detailed and descriptive. Don't end the story.
Stop the output right after the main character stops exerting energy.

Make sure the main character actually performs the {} motion.

A few, but not all, motion to scenarios examples are:
1. Pushing on a surface: pushing blocking objects or heavy door, performing CPR compressions, shoving people in a tight crowd
2. Hip hinge with weighted bar: lifting up a heavy lever, lower a boat into the water, picking up a long heavy object
3. Bending torso towards knees: picking up objects, getting up after a fall, resisting someone trying to pin you down
4. Holding a straight body position: aiming a sniper, hiding without movement, waiting
"""

SUMMARIZE="""
Rewrite the story to make it shorter. Keep the important information.
"""

CONCLUSION="""
The sidekick congratulates the main character for finishing all their workouts. "Conclude the story."
"""