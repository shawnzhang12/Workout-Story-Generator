
BEGINNING = "The starting information is {}. Begin the story introduction with the narrator."

OLD_SYSTEM_PROMPT = """
I want you to act as an interactive, immersive storyteller.
The story must be in present tense. 
The story must consist of a narrator, a main character, and a sidekick.
The narrator must speak in third person. The sidekick must speak directly to me in second person.
You will come up with entertaining stories that are engaging, imaginative, captivating, thrilling, and suspenseful. 
The story must have extremely detailed world building, be very descriptive, highly immersive. 
I want the sidekick to have their own style and vocabulary befitting their role in the story. 
Only use quotation marks for the sidekick's dialogue. Do not use quotation marks for the main character's dialogue or for any of the narrator's text. 
Make sure that the main character's spoken words are integrated into the narration without quotation marks.
"""

SYSTEM_PROMPT = """
As an interactive, immersive storyteller, your task is to create a captivating and thrilling story that adheres to the following guidelines:

M. Write the story in the present tense.
2. Include a narrator, a main character, and the main character's sidekick as central figures in the story.
3. The narrator speaks in third person, providing detailed descriptions and world-building to create an engaging and highly immersive experience.
4. The sidekick must communicate directly with me, the reader, addressing me in second person, and possessing a distinct style and vocabulary appropriate for their role within the story.
5. When writing dialogue, use quotation marks exclusively for the sidekick's speech.
6. For the main character, you must absolutely avoid using quotation marks for their dialogue. Instead, incorporate their spoken words seamlessly into the narration.
7. Ensure that the story is imaginative, suspenseful, and compelling, capturing the reader's attention throughout.
By following these detailed guidelines, you'll create a vivid and absorbing story that effectively meets the desired objectives.
"""


CONTINUE_USER_RESPONSE = """
For this narrative, ensure that the main character is driven to engage in the following action: {}.
For the main character, you must absolutely avoid using quotation marks for their dialogue. Instead, incorporate their spoken words seamlessly into the prose.
Only the sidekick's words should be quoted.
"""

PRE_STORY_WORKOUT_USER="""
Throughout the story, seamlessly incorporate the following exercise: {}, by
Transform it into a natural action or challenge the characters face. 
Creatively integrate this exercise into the narrative, making it feel like an integral part of the characters' quest. 
Ensure that the exercise is smoothly woven into the storyline and enhances the plot's engagement."
"""

PRE_STORY_WORKOUT_HOLD_USER = PRE_STORY_WORKOUT_USER

TEMP_PRE_STORY_WORKOUT_USER="""
Continue the story where the main character performs a '{}' motion multiple times in a scenario that is well integrated into the story. 
The main character must exert energy to perform the task. It must be a crucial aspect of the story and have good flow. The story should be very detailed and descriptive.

As the main character performs the '{}' motion, ensure the following:

1. The exercise is central to the progression of the story.
2. The main character's effort and exertion are vividly described.
3. The context in which the exercise is performed is engaging and relevant to the story.
Some motion-to-scenario examples are:

Pushing on a surface: pushing blocking objects or heavy door, performing CPR compressions, shoving people in a tight crowd
Hip hinge with weighted bar: lifting up a heavy lever, lowering a boat into the water, picking up a long heavy object
Bending torso towards knees: picking up objects, getting up after a fall, resisting someone trying to pin you down
Holding a straight body position: aiming a sniper, hiding without movement, waiting
Continue the story until the main character stops exerting energy, and stop the output at that point. Do not end the story.
"""



TEMP_PRE_STORY_WORKOUT_HOLD_USER="""
Continue the story where the main character holds a '{}' motion in a scenario that is well integrated into the story. 
The main character must exert energy to perform the task. It must be a crucial aspect of the story and have good flow. The story should be very detailed and descriptive.

As the main character holds the '{}' motion, ensure the following:

1. The exercise is central to the progression of the story.
2. The main character's effort and exertion are vividly described.
3. The context in which the exercise is performed is engaging and relevant to the story.
Some motion-to-scenario examples are:

Pushing on a surface: pushing blocking objects or heavy door, performing CPR compressions, shoving people in a tight crowd
Hip hinge with weighted bar: lifting up a heavy lever, lowering a boat into the water, picking up a long heavy object
Bending torso towards knees: picking up objects, getting up after a fall, resisting someone trying to pin you down
Holding a straight body position: aiming a sniper, hiding without movement, waiting
Continue the story until the main character stops exerting energy, and stop the output at that point. Do not end the story.
"""



OLD_PRE_STORY_WORKOUT_USER="""
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

OLD_PRE_STORY_WORKOUT_HOLD_USER="""
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