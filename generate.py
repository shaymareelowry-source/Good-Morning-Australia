import asyncio
import html
import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import edge_tts
import requests

REPO_NAME = "good-morning-australia"

# Bendigo-ish coordinates
LAT = -36.7570
LON = 144.2794

VOICE = "en-AU-NatashaNeural"

ANIMALS = [
    ("wombat", "Wombats do cube-shaped poos. Scientists think it helps stop them rolling away."),
    ("echidna", "Echidnas have long sticky tongues to catch ants and termites."),
    ("platypus", "Platypuses close their eyes, ears and nose when they swim underwater."),
    ("kangaroo", "Kangaroos cannot walk backwards very well."),
    ("kookaburra", "Kookaburras laugh to tell other birds, this is my territory."),
    ("emu", "Emus can run very fast, but they cannot fly."),
    ("bilby", "Bilbies have huge ears that help them hear insects underground."),
    ("koala", "Koalas sleep for many hours because gum leaves do not give them much energy."),
]

JOKES = [
    ("What do you call a sleeping bull?", "A bulldozer!"),
    ("Why did the kangaroo stop drinking coffee?", "It made him too jumpy!"),
    ("What do you call a dinosaur that crashes his car?", "Tyrannosaurus wrecks!"),
    ("Why did the banana go to the doctor?", "Because it was not peeling well!"),
    ("What do clouds wear under their raincoats?", "Thunderwear!"),
]

MOVEMENTS = [
    "Can you hop like a kangaroo ten times?",
    "Can you stomp like a wombat?",
    "Can you flap your wings like a kookaburra?",
    "Can you stretch up tall like a gum tree?",
    "Can you waddle like an echidna?",
]

def get_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        "&current=temperature_2m,weather_code"
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
            return "There are no finished AFL games to report yet."

        latest = sorted(finished, key=lambda g: g.get("date", ""))[-1]
        hteam = latest["hteam"]
        ateam = latest["ateam"]
        hscore = latest.get("hscore")
        ascore = latest.get("ascore")

        if hscore is None or ascore is None:
            return "The AFL scores are still being updated."

        if hscore > ascore:
            return f"In the AFL, {hteam} beat {ateam}, {hscore} to {ascore}."
        elif ascore > hscore:
            return f"In the AFL, {ateam} beat {hteam}, {ascore} to {hscore}."
        else:
            return f"In the AFL, {hteam} and {ateam} had a draw, {hscore} all."
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
    letter, number = letter_number_of_day(today)
    animal, fact = random.choice(ANIMALS)
    joke_q, joke_a = random.choice(JOKES)
    movement = random.choice(MOVEMENTS)

    return f"""
Good morning Australia!

Today is {day_name}, the {date_text}.

In Bendigo today, it will be {condition}, with a low of {min_temp} degrees and a top of {max_temp} degrees.
There is about a {rain} percent chance of rain.
{clothing}

Today’s letter is {letter}.
Can you think of something that starts with {letter}?

Today’s number is {number}.
Can you clap {number} times?

Today’s Australian animal is the {animal}.
Did you know? {fact}

AFL update!
{afl}

Today’s joke.
{joke_q}
{joke_a}

Movement challenge!
{movement}

That’s your Good Morning Australia update.
Have a kind, curious, adventurous day.
See you tomorrow!
""".strip()

async def make_audio(text):
    os.makedirs("docs/audio", exist_ok=True)
    output = "docs/audio/latest.mp3"
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output)
    return output

def make_rss(script):
    now = datetime.now(ZoneInfo("Australia/Melbourne"))
    pub_date = now.strftime("%a, %d %b %Y %H:%M:%S %z")
    title = f"Good Morning Australia - {now.strftime('%d %B %Y')}"
    base_url = f"https://YOUR_GITHUB_USERNAME.github.io/{REPO_NAME}"

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Good Morning Australia</title>
<link>{base_url}</link>
<description>A daily preschool morning update for Yoto.</description>
<language>en-au</language>
<item>
<title>{html.escape(title)}</title>
<description>{html.escape(script[:500])}</description>
<pubDate>{pub_date}</pubDate>
<guid>{base_url}/audio/latest.mp3?date={now.strftime('%Y%m%d')}</guid>
<enclosure url="{base_url}/audio/latest.mp3" length="1000000" type="audio/mpeg"/>
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
