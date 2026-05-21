
import asyncio
import html
import os
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import edge_tts
import requests
import os
from icalendar import Calendar
from pydub import AudioSegment

REPO_NAME = "Good-Morning-Australia"

# Bendigo coordinates
LAT = -36.7570
LON = 144.2794

VOICE = "en-AU-NatashaNeural"

PAUSE_SHORT = ". . . . ."
PAUSE_MEDIUM = ". . . . . . . . ."
PAUSE_LONG = ". . . . . . . . . . . . . ."

GREETINGS = [
    "Good morning Darcy, Spencer and Neve!",
    "Wake up Darcy, Spencer and Neve!",
    "Hello breakfast crew!",
    "Good morning Walkers!",
]

ANIMALS = [
    ("wombat", "Wombats do cube-shaped poos to stop them rolling away."),
    ("echidna", "Echidnas use their long sticky tongues to catch ants."),
    ("platypus", "Platypuses close their eyes and ears underwater."),
    ("kangaroo", "Kangaroos cannot walk backwards very well."),
    ("kookaburra", "Kookaburras laugh to talk to other birds."),
    ("emu", "Emus can run very fast, but they cannot fly."),
    ("bilby", "Bilbies have huge ears to help them hear underground."),
    ("koala", "Koalas sleep for many hours every day."),
]

JOKES = [
    ("What do clouds wear under their raincoats?", "Thunderwear!"),
    ("What do you call a sleeping bull?", "A bulldozer!"),
    ("Why did the banana go to the doctor?", "Because it was not peeling well!"),
    ("Why are kangaroos bad at hiding?", "Because they always stand out!"),
]

MOVEMENTS = [
    "Can you hop like a kangaroo ten times?",
    "Can you stomp like a wombat?",
    "Can you flap your wings like a kookaburra?",
    "Can you stretch up tall like a gum tree?",
    "Can you waddle like an echidna?",
]

CATCHPHRASES = [
    "Keep looking for tiny adventures today!",
    "Remember to be kind to your grown ups!",
    "Don’t forget to laugh today!",
    "See if you can spot a bird outside today!",
]

def get_calendar_events():
    try:
        calendar_url = os.environ.get("KIDS_CALENDAR_ICS_URL")

        if not calendar_url:
            return []

        response = requests.get(calendar_url, timeout=20)

        cal = Calendar.from_ical(response.text)

        today = datetime.now(ZoneInfo("Australia/Melbourne")).date()

        events = []

        for component in cal.walk():
            if component.name == "VEVENT":
                start = component.get("dtstart").dt

                if hasattr(start, "date"):
                    start = start.date()

                summary = str(component.get("summary"))

                if start == today:
                    events.append(summary)

        return events

    except Exception:
        return []

def get_tomorrow_events():
    try:
        calendar_url = os.environ.get("KIDS_CALENDAR_ICS_URL")

        if not calendar_url:
            return []

        response = requests.get(calendar_url, timeout=20)

        cal = Calendar.from_ical(response.text)

        tomorrow = (
            datetime.now(ZoneInfo("Australia/Melbourne")).date()
            + timedelta(days=1)
        )

        events = []

        for component in cal.walk():
            if component.name == "VEVENT":
                start = component.get("dtstart").dt

                if hasattr(start, "date"):
                    start = start.date()

                summary = str(component.get("summary"))

                if start == tomorrow:
                    events.append(summary)

        return events

    except Exception:
        return []

def get_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        "&timezone=Australia%2FMelbourne"
        "&forecast_days=1"
    )

    data = requests.get(url, timeout=20).json()

    max_temp = round(data["daily"]["temperature_2m_max"][0])
    min_temp = round(data["daily"]["temperature_2m_min"][0])
    rain = data["daily"]["precipitation_probability_max"][0]
    code = data["daily"]["weather_code"][0]

    if code in [0, 1]:
        condition = "mostly sunny"
    elif code in [2, 3]:
        condition = "cloudy"
    elif code in [45, 48]:
        condition = "foggy"
    elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
        condition = "rainy"
    elif code in [95, 96, 99]:
        condition = "stormy"
    else:
        condition = "mixed"

    if rain >= 50:
        clothing = "You might need a raincoat today."
    elif max_temp <= 15:
        clothing = "You might need a warm jumper today."
    elif max_temp >= 28:
        clothing = "It might be a hot day, so remember your hat and drink bottle."
    else:
        clothing = "It sounds like a good day for comfy clothes."

    return condition, min_temp, max_temp, rain, clothing

def get_afl_update():
    try:
        year = datetime.now(ZoneInfo("Australia/Melbourne")).year

        url = f"https://api.squiggle.com.au/?q=games;year={year}"

        games = requests.get(url, timeout=20).json().get("games", [])

        finished = [
            g for g in games
            if g.get("complete") == 100 and g.get("hteam") and g.get("ateam")
        ]

        if not finished:
            return "No AFL scores today."

        latest = sorted(finished, key=lambda g: g.get("date", ""))[-1]

        hteam = latest["hteam"]
        ateam = latest["ateam"]

        hscore = latest.get("hscore")
        ascore = latest.get("ascore")

        if hscore > ascore:
            return f"{hteam} had a great win against {ateam}!"
        elif ascore > hscore:
            return f"{ateam} had a great win against {hteam}!"
        else:
            return f"{hteam} and {ateam} had a draw!"

    except Exception:
        return "The AFL update is having a rest today."

def letter_number_of_day(today):
    day_of_year = int(today.strftime("%j"))

    letter = chr(ord("A") + ((day_of_year - 1) % 26))
    number = ((day_of_year - 1) % 20) + 1

    return letter, number

def build_script():
    today = datetime.now(ZoneInfo("Australia/Melbourne"))

    day_name = today.strftime("%A")
    date_text = today.strftime("%d %B").lstrip("0")

    condition, min_temp, max_temp, rain, clothing = get_weather()

    afl = get_afl_update()

    today_events = get_calendar_events()

    tomorrow_events = get_tomorrow_events()
    
    letter, number = letter_number_of_day(today)

    greeting = random.choice(GREETINGS)

    animal, fact = random.choice(ANIMALS)

    joke_q, joke_a = random.choice(JOKES)

    movement = random.choice(MOVEMENTS)

    catchphrase = random.choice(CATCHPHRASES)

    if today_events:
        event_text = "Today you have " + ", and ".join(today_events) + "."
    else:
        event_text = "Today looks like a nice calm day."
        birthday_events = [
    e for e in today_events if "birthday" in e.lower()
]

if birthday_events:
    event_text = (
        "Oooh! Today is a very special day! "
        + ", and ".join(birthday_events)
        + "!"
    )

elif today_events:
    event_text = "Today you have " + ", and ".join(today_events) + "."

    return f"""

    if tomorrow_events:
        tomorrow_text = (
            "Tomorrow you have "
            + ", and ".join(tomorrow_events)
            + "."
    )
    else:
        tomorrow_text = ""

if is_friday:
    friday_text = (
        "It’s Friday dance party day! "
        "Make sure you have a little wiggle today!"
    )
else:
    friday_text = ""
    
{greeting}

Good Morning!

Today is {day_name}, the {date_text}.

Wake up everyone, it’s time to start the day.

{PAUSE_MEDIUM}

{event_text}

{PAUSE_MEDIUM}

In Bendigo today, it will be {condition}, with a low of {min_temp} degrees and a top of {max_temp} degrees.

There is about a {rain} percent chance of rain.

{clothing}

{friday_text}

{PAUSE_MEDIUM}

Today’s letter is {letter}.

Can you think of something that starts with the letter {letter}?

{PAUSE_LONG}

Today’s number is {number}.

Can you clap {number} times?

{PAUSE_MEDIUM}

Today’s Australian animal is the {animal}.

Did you know?

{fact}

AFL update!

{afl}

Now it’s time for today’s joke.

{joke_q}

{PAUSE_LONG}

{joke_a}

Movement challenge!

{movement}

{PAUSE_LONG}

Before we go...

Take a big deep breath in...

{PAUSE_MEDIUM}

...and out.

{PAUSE_MEDIUM}

{catchphrase}

Have a kind, curious, adventurous day.

{PAUSE_MEDIUM}

{tomorrow_text}

See you tomorrow!
""".strip()

async def make_audio(text):
    os.makedirs("docs/audio", exist_ok=True)

    speech_file = "docs/audio/speech.mp3"
    final_file = "docs/audio/latest.mp3"

    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(speech_file)

    intro = AudioSegment.from_mp3("intro.mp3")

    speech = AudioSegment.from_mp3(speech_file)

    # Lower intro volume slightly
    intro = intro - 12

    # First 5 seconds of intro underneath speech
    overlay = intro.overlay(speech)

    # Then continue remaining speech
    combined = overlay + speech[len(intro):]

    combined.export(final_file, format="mp3")

def make_rss(script):
    now = datetime.now(ZoneInfo("Australia/Melbourne"))

    pub_date = now.strftime("%a, %d %b %Y %H:%M:%S %z")

    title = f"Good Morning Australia - {now.strftime('%d %B %Y')}"

    base_url = f"https://shaymareelowry-source.github.io/{REPO_NAME}"

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Good Morning Australia</title>
<link>{base_url}</link>
<description>Daily Australian preschool breakfast radio.</description>
<language>en-au</language>

<item>
<title>{html.escape(title)}</title>
<description>{html.escape(script[:500])}</description>
<pubDate>{pub_date}</pubDate>

<guid>{base_url}/audio/latest.mp3?date={now.strftime('%Y%m%d')}</guid>

<enclosure
url="{base_url}/audio/latest.mp3"
length="1000000"
type="audio/mpeg"/>
</item>

</channel>
</rss>
"""

    with open("docs/feed.xml", "w", encoding="utf-8") as f:
        f.write(rss)

async def main():
    script = build_script()

    with open("docs/latest-script.txt", "w", encoding="utf-8") as f:
        f.write(script)

    await make_audio(script)

    make_rss(script)

if __name__ == "__main__":
    asyncio.run(main())
