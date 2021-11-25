import os
import json
import random
import logging
import datetime

import requests

from dotenv import load_dotenv
from telegram import Update, ParseMode
from telegram.ext import Updater
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

load_dotenv()


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

LATITUDE = 50.0980
LONGITUDE = 19.950
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AIRLY_API_KEY = os.getenv("AIRLY_API_KEY")
ACCUWEATHER_API_KEY = os.getenv("ACCUWEATHER_API_KEY")

daily_weather_forecast_time = datetime.datetime.strptime("05:30", "%H:%M").time()
daily_morning_airly_time = datetime.datetime.strptime("6:00", "%H:%M").time()


def start(update: Update, context: CallbackContext):
    try:
        chat_id = update.message.chat_id
        remove_job_if_exists(f"{chat_id}_1", context)
        remove_job_if_exists(f"{chat_id}_2", context)
        remove_job_if_exists(f"{chat_id}_3", context)

        context.job_queue.run_daily(
            send_daily_weather_forecast,
            daily_weather_forecast_time,
            name=f"{chat_id}_1",
            context=chat_id,
        )

        context.job_queue.run_daily(
            send_daily_airly_update,
            daily_morning_airly_time,
            name=f"{chat_id}_4",
            context=chat_id,
        )
        msg = """
<b>Program</b>
<code>
     6:30 - Poranek z Sharkiem z Wall Street
     7:00 - Czy warto wyjść na zewnątrz?
     8:00 - Crypto z rana jak śmietana.
    12:00 - W samo południe! Przegląd kursów.
    16:00 - Co w giełdzie Crypto i Walutach piszczy.
</code>
"""
        context.bot.send_message(
            chat_id=update.effective_chat.id, text=msg, parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(e)


def remove_job_if_exists(name: str, context: CallbackContext) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


def get_accuweather_forecast():
    params = {"apikey": ACCUWEATHER_API_KEY, "language": "pl", "metric": True}
    req = requests.get(
        "http://dataservice.accuweather.com/forecasts/v1/daily/1day/2-274455_1_AL",
        params=params,
        headers={"Accept": "application/json"},
    )
    json_data = req.json()
    good_morning_songs = [
        "https://www.youtube.com/watch?v=6CHs4x2uqcQ",
        "https://www.youtube.com/watch?v=7KSNmziMqog",
        "https://www.youtube.com/watch?v=N5xMlDeGFBU",
        "https://www.youtube.com/watch?v=h6Ol3eprKiw",
        "https://www.youtube.com/watch?v=-uXoRU-i3R4",
        "https://www.youtube.com/watch?v=CPsWGut8SeM",
        "https://www.youtube.com/watch?v=CiIkBT-HFOA",
        "https://www.youtube.com/watch?v=YDu93pdyBDE",
    ]

    random_song = random.choice(good_morning_songs)
    daily_forecasts = json_data["DailyForecasts"][0]
    return f"""<b>GOOOOD MORNING!</b>
<a href="{random_song}">Filmik na dziś!</a>
<code>
Prognoza na dzisiaj:
Temperatura:
    min: {daily_forecasts['Temperature']['Minimum']['Value']:4.2f} °C
    max: {daily_forecasts['Temperature']['Maximum']['Value']:4.2f} °C

Pogoda:
    dzień: {daily_forecasts["Day"]["IconPhrase"]}
    noc:  {daily_forecasts["Night"]["IconPhrase"]}
</code>
<a href="{daily_forecasts["Link"]}">Link do AccuWeather</a>
"""


def send_weather_forecast(update: Update, context: CallbackContext):
    msg = get_accuweather_forecast()
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=msg, parse_mode=ParseMode.HTML
    )


def get_airly_measurement():
    req = requests.get(
        f"https://airapi.airly.eu/v2/measurements/point?lat={LATITUDE}&lng={LONGITUDE}",
        headers={"Accept": "application/json", "apikey": AIRLY_API_KEY},
    )
    json_data = req.json()
    current = json_data["current"]
    values = current["values"]
    pm1, pm25, pm10, pressure, humidity, temperature, so2, co = values
    msg = "\n<b> AIRLY - KRAKÓW</b>\n"

    msg += f"""<code>
PYŁY
-------------------------------
PM 10  : {pm10['value']:3.0f} µg/m³
Norma Airly CAQI (dobowa): 50 µg/m³

PM 2.5 : {pm25['value']:3.0f} µg/m³
Norma Airly CAQI (dobowa): 25 µg/m³

PM 1   : {pm1['value']:3.0f} µg/m³
--------------------------------
GAZY
--------------------------------
SO₂ : {so2['value']:3.0f} µg/m³
Norma Airly CAQI (dobowa): 350 µg/m³

CO  : {co['value']:5.0f} µg/m³
Norma Airly CAQI (godzinowa): 30000 µg/m³
--------------------------------
DANE POGODOWE
--------------------------------
Temperatura : {temperature['value']:3.0f} °C
Wilgotność  : {humidity['value']:3.0f} %
Ciśnienie   : {pressure['value']:4.0f} hPa
</code>
"""
    msg += "\n"
    return msg
  

def send_daily_airly_update(context: CallbackContext):
    msg = get_airly_measurement()
    job = context.job
    context.bot.send_message(job.context, text=msg, parse_mode=ParseMode.HTML)


def send_daily_weather_forecast(context: CallbackContext):
    msg = get_accuweather_forecast()
    job = context.job
    context.bot.send_message(job.context, text=msg, parse_mode=ParseMode.HTML)


def send_airly_update(update: Update, context: CallbackContext):
    msg = get_airly_measurement()
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=msg, parse_mode=ParseMode.HTML
    )


if __name__ == "__main__":
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler("start", start)
    airly_handler = CommandHandler("air", send_airly_update)
    accuweather_handler = CommandHandler("weather", send_weather_forecast)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(airly_handler)
    dispatcher.add_handler(accuweather_handler)
    updater.start_polling()
    updater.idle()
