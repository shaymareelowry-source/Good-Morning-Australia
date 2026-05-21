import asyncio
from datetime import datetime

import edge_tts

VOICE = "en-AU-NatashaNeural"

script = f"""
Good morning Australia!

Today is {datetime.now().strftime("%A")}.

In Bendigo today, it will be lovely.

Today's letter is A.

Today's number is 5.

Today's joke:
What do clouds wear under their raincoats?
Thunderwear!

See you tomorrow!
"""

async def main():
    communicate = edge_tts.Communicate(script, VOICE)
    await communicate.save("episode.mp3")

asyncio.run(main())
