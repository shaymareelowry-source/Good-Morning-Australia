
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
SHOW_NAME = "Good Morning Family"

# Bendigo coordinates
LAT = -36.7570
LON = 144.2794

VOICE = "en-AU-NatashaNeural"

CURRENT_CONDITION = "sunny"
CURRENT_IS_FRIDAY = False

SOUND_MARKERS = {
    "[WEATHER_SOUND]": "weather.mp3",
    "[LETTER_SOUND]": "letter.mp3",
    "[ANIMAL_SOUND]": "animal.mp3",
    "[AFL_SOUND]": "afl.mp3",
    "[JOKE_SOUND]": "joke.mp3",
    "[MOVEMENT_SOUND]": "movement.mp3",
    "[BIRTHDAY_SOUND]": "birthday.mp3",
    "[FRIDAY_SOUND]": "friday.mp3",
}

PAUSE_SHORT = ". . . . ."
PAUSE_MEDIUM = ". . . . . . . . ."
PAUSE_LONG = ". . . . . . . . . . . . . ."

GREETINGS = [
    "Good morning Darcy, Spencer and Neve!",
    "Wake up Darcy, Spencer and Neve!",
    "Wakey Wakey breakfast crew!",
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
        api_key = os.environ.get("ODDS_API_KEY")

        if not api_key:
            return "The AFL update is not connected yet."

        url = "https://api.the-odds-api.com/v4/sports/aussierules_afl/scores"

        params = {
            "apiKey": api_key,
            "daysFrom": 3,
            "dateFormat": "iso",
        }

        data = requests.get(url, params=params, timeout=20).json()

        finished_games = []

        for game in data:
            if not game.get("completed"):
                continue

            scores = game.get("scores") or []

            if len(scores) < 2:
                continue

            home_team = game.get("home_team")
            away_team = game.get("away_team")

            score_map = {
                s.get("name"): int(s.get("score", 0))
                for s in scores
            }

            if home_team not in score_map or away_team not in score_map:
                continue

            game_time = datetime.fromisoformat(
                game["commence_time"].replace("Z", "+00:00")
            )

            finished_games.append({
                "time": game_time,
                "home": home_team,
                "away": away_team,
                "home_score": score_map[home_team],
                "away_score": score_map[away_team],
            })

        if not finished_games:
            return "There were no AFL scores from last night."

        latest = sorted(finished_games, key=lambda g: g["time"])[-1]

        margin = abs(latest["home_score"] - latest["away_score"])

        if latest["home_score"] > latest["away_score"]:
            return f"{latest['home']} beat {latest['away']} by {margin} points."

        elif latest["away_score"] > latest["home_score"]:
            return f"{latest['away']} beat {latest['home']} by {margin} points."

        else:
            return f"{latest['home']} and {latest['away']} had a draw."

    except Exception as e:
        print("ODDS AFL ERROR:", e)
        return "The AFL update is having a little rest today."
        
def letter_number_of_day(today):
    day_of_year = int(today.strftime("%j"))

    letter = chr(ord("A") + ((day_of_year - 1) % 26))
    number = ((day_of_year - 1) % 20) + 1

    return letter, number

def build_script():
    today = datetime.now(ZoneInfo("Australia/Melbourne"))

    is_friday = today.weekday() == 4
    global CURRENT_IS_FRIDAY
    CURRENT_IS_FRIDAY = is_friday
    day_name = today.strftime("%A")
    date_text = today.strftime("%d %B").lstrip("0")
    
    condition, min_temp, max_temp, rain, clothing = get_weather()
    global CURRENT_CONDITION
    CURRENT_CONDITION = condition

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
        event_text = (
            "Today you have "
            + ", and ".join(today_events)
            + "."
        )

    else:
        event_text = "Today looks like a nice calm day."

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
            "[FRIDAY_SOUND]\n\n"
            "It’s Friday dance party day! "
            "Make sure you have a little wiggle today!"
        )
    else:
        friday_text = ""

    return f"""
   
{greeting}

Hello everyone!

Today is {day_name}, the {date_text}.

Wake up everyone, it’s time to start the day.

{PAUSE_MEDIUM}

{event_text}

{PAUSE_MEDIUM}

[WEATHER_SOUND]

In Bendigo today, it will be {condition}, with a low of {min_temp} degrees and a top of {max_temp} degrees.

There is about a {rain} percent chance of rain.

{clothing}

{friday_text}

{PAUSE_MEDIUM}

[LETTER_SOUND]

Today’s letter is {letter}.

Can you think of something that starts with the letter {letter}?

{PAUSE_LONG}

[NUMBER_SOUND]

Today’s number is {number}.

Can you clap {number} times?

{PAUSE_MEDIUM}

[ANIMAL_SOUND]

Today’s Australian animal is the {animal}.

Did you know?

{fact}

[AFL_SOUND]

AFL update!

{afl}

[JOKE_SOUND]

Now it’s time for today’s joke.

{joke_q}

{PAUSE_LONG}

{joke_a}

[MOVEMENT_SOUND]

Movement challenge!

{movement}

{PAUSE_LONG}

Before we go...

Take a big deep breath in...

{PAUSE_MEDIUM}

...and out.

{PAUSE_MEDIUM}

{catchphrase}

Have a kind and wonderful day.

{PAUSE_MEDIUM}

{tomorrow_text}

See you tomorrow!
""".strip()

def get_weather_sound(condition):
    condition = condition.lower()

    if "storm" in condition:
        return "storm.mp3"

    elif "rain" in condition:
        return "rain.mp3"

    elif "cloud" in condition:
        return "cloudy.mp3"

    else:
        return "birds.mp3"
        
async def make_audio(text):
    os.makedirs("docs/audio", exist_ok=True)

    today_stamp = datetime.now(ZoneInfo("Australia/Melbourne")).strftime("%Y-%m-%d")
    final_file = f"docs/audio/{today_stamp}.mp3"

    final_audio = AudioSegment.silent(duration=500)

    if os.path.exists("intro.mp3"):
        intro = AudioSegment.from_mp3("intro.mp3") - 3
        final_audio += intro

    parts = []
    remaining = text

    while remaining:
        marker_positions = [
            (remaining.find(marker), marker)
            for marker in SOUND_MARKERS
            if remaining.find(marker) != -1
        ]

        if not marker_positions:
            parts.append(("text", remaining))
            break

        marker_pos, marker = min(marker_positions, key=lambda x: x[0])

        before = remaining[:marker_pos]
        after = remaining[marker_pos + len(marker):]

        if before.strip():
            parts.append(("text", before))

        parts.append(("sound", SOUND_MARKERS[marker]))
        remaining = after

    chunk_number = 0

    for part_type, content in parts:
        if part_type == "sound":
            if os.path.exists(content):
                sound = AudioSegment.from_mp3(content) - 4
                final_audio += AudioSegment.silent(duration=250)
                final_audio += sound
                final_audio += AudioSegment.silent(duration=250)
            continue

        chunk_text = content.strip()

        if not chunk_text:
            continue

        chunk_file = f"docs/audio/chunk_{chunk_number}.mp3"

        communicate = edge_tts.Communicate(chunk_text, VOICE)
        await communicate.save(chunk_file)

        speech = AudioSegment.from_mp3(chunk_file)
        final_audio += speech
        final_audio += AudioSegment.silent(duration=300)

        chunk_number += 1

    if os.path.exists("intro.mp3"):
        outro = AudioSegment.from_mp3("intro.mp3") - 12
        outro = outro[:5000]
        final_audio += AudioSegment.silent(duration=300)
        final_audio += outro.fade_out(2000)

    final_audio.export(final_file, format="mp3")

def clean_rss_description(script):
    cleaned = script

    for marker in SOUND_MARKERS:
        cleaned = cleaned.replace(marker, "")

    return cleaned[:500]
    
def make_rss(script):
    now = datetime.now(ZoneInfo("Australia/Melbourne"))

    pub_date = now.strftime("%a, %d %b %Y %H:%M:%S %z")

    title = f"Good Morning Family - {now.strftime('%d %B %Y')}"
    
    audio_filename = now.strftime("%Y-%m-%d") + ".mp3"

    base_url = f"https://shaymareelowry-source.github.io/{REPO_NAME}"

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
<image>
    <url>{base_url}/podcast.png</url>
    <title>Good Morning Family</title>
    <link>{base_url}/feed.xml</link>
</image>

<itunes:image href="{base_url}/podcast.png"/>
<title>Good Morning Family</title>
<link>{base_url}</link>
<description>Daily Australian preschool breakfast radio.</description>
<language>en-au</language>

<item>
<title>{html.escape(title)}</title>
<description>{html.escape(clean_rss_description(script))}</description>
<pubDate>{pub_date}</pubDate>

<guid>{base_url}/audio/{audio_filename}</guid>

<enclosure
url="{base_url}/audio/{audio_filename}"
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
