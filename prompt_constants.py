global CONST_BEGINNING, CONTINUE_PROMPT_AUTO, CONTINUE_PROMPT, CONST_BEGINNING_AUTO, WORD_LIMIT_PROMPT, CONST_BEGINNING_INTERACTIVE

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
Don't end the story. End output with the sidekick asking me what to do next.
"""

WORD_LIMIT_PROMPT = ""

CONST_BEGINNING_AUTO = """I want you to act as an interactive, immersive storyteller. 
The story must consist of a narrator, a main character, and a sidekick.
The narrator must speak in third person. The sidekick must speak directly to me in second person.
You will come up with entertaining stories that are engaging, imaginative, captivating, thrilling, and suspenseful. 
The story must have extremely detailed world building and be very descriptive. 
I want the sidekick to have their own style and vocabulary befitting their role in the story. 
Always put double double quotation mark quotes around the sidekick's text.
Never put double or single quotation marks around narrator text. 
Never put double or single quotation marks around the main character's text.
I am the main character. Stop text generation when it is the main character's turn to speak.
The starting information is {}. Begin the story introduction with the narrator."
"""

CONTINUE_PROMPT_AUTO = """Continue the story according to the main character's previous response.
Always put double quotes around the sidekick's lines. Never put quotes around narrator text. Never put quotes around the main character's text.
The story must have extremely detailed world building and be very descriptive. 
The narrator must speak in third person. The sidekick must speak directly to me in second person. 
I am the main character. Stop text generation when it is the main character's turn to speak. 
I want the sidekick to have their own style and vocabulary befitting their role in the story.
End the output with the sidekick asking the main character what to do next and the main character responding with something typical to the storyline.
Don't end the story.
"""

# SPEED SHOULD BE CONSIDERED situp = explosive, russian deadlift = slow, plank = static
CONTINUE_USER_STORY = """
The main character responded with {} after the sidekick asked him what to do.
Begin the story continuation in detail revolving around the main character's response.
Only write 2-3 sentences.
"""


CONTINUE_WITH_WORKOUT = """
I want you to act as an interactive, immersive storyteller. 
The story must consist of a narrator, a main character, and a sidekick.
The narrator must speak in third person. The sidekick must speak directly to me in second person.
You will come up with entertaining stories that are engaging, imaginative, captivating, thrilling, and suspenseful. 
The story must have extremely detailed world building, be very descriptive, highly immersive. 
I want the sidekick to have their own style and vocabulary befitting their role in the story. 
Always put double double quotation mark quotes around the sidekick's text.
Never put double or single quotation marks around narrator text. 
Never put double or single quotation marks around the main character's text.


Continue the story where the main character performs a {} motion.
It must be a crucial aspect of the story and have good flow, well integrated into the story.
It must be very detailed and descriptive. Don't end the story.
Append <STOP_TOKEN> to the end of the sentence where the main character completes the motion.
"""

FEW_SHOT = """ 
Here are some scenario examples based on a few motion types, adapt the actual motion to the story with seamless integration:
1. Pushing on a surface: pushing blocking objects or heavy door, performing CPR compressions, shoving people in a tight crowd
2. Hip hinge with weighted bar: lifting up a heavy lever, lower a boat into the water, picking up a long heavy object
3. Bending torso towards knees: picking up objects, getting up after a fall, resisting someone trying to pin you down
4. Holding a straight body position: aiming a sniper, hiding without movement, waiting"""