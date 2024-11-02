from flask import Flask, request, render_template, redirect, send_file, flash
import requests
import unittest
from googletrans import Translator
import datetime
import logging
from decimal import Decimal
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
EMAIL_SERVICE_URL = os.getenv("EMAIL_SERVICE_URL")
BUCKET = os.getenv("BUCKET")
IMAGE = os.getenv("IMAGE")
def get_weather_results(location, key, unit):
    try:
        api_url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/next6days?unitGroup={unit}&key={key}&contentType=json"
        with requests.get(api_url) as r:
            data = r.json()
        next_week_weather = []
        translator = Translator()

        country = data.get('resolvedAddress', '')
        translated_country = translator.translate(country, dest='en').text
        for day in data['days']:
            next_week_weather.append({
                "date": day["datetime"],
                "day_temperature": Decimal(str(day.get("tempmax"))),
                "night_temperature": Decimal(str(day.get("tempmin"))),
                "humidity": Decimal(str(day.get("humidity")))
            })

        return {
            "location": translated_country,
            "weather": next_week_weather,
            "origin_language": country,
            "unit": unit
        }
    except Exception as e:
        logger.error(f"Error occurred while fetching weather data: {e}")
        return None


@app.route("/", methods=["GET", "POST"])
def home_page():
    weather_info = None
    if request.method == "POST":
        location = request.form.get("location")
        email = request.form.get("email")
        unit = request.form.get("unit", "metric")
        action = request.form.get("action")

        logger.info(f"Form submission received. Action: {action}, Location: {location}, Email: {email}")

        if action == "download":
            return redirect("/download-image")

        if location:
            weather_info = get_weather_results(location, WEATHER_API_KEY, unit)
            if weather_info is None:
                weather_info = {"location": location, "error": "Could not retrieve weather information."}
            else:
                weather_info["display_location"] = weather_info["origin_language"] if action == "origin_language" else \
                weather_info["location"]

                if action == "subscribe" and email:
                    logger.info("Preparing to send subscription request to email microservice.")

                    avg_temp = round(float(
                        sum(day['day_temperature'] for day in weather_info['weather']) / len(weather_info['weather'])),
                                     1)
                    subscription_data = {
                        "email": email,
                        "location": weather_info["display_location"],
                        "temperature": avg_temp
                    }
                    logger.info(f"Subscription data prepared: {subscription_data}")

                    try:
                        response = requests.post(EMAIL_SERVICE_URL, json=subscription_data)
                        logger.info(
                            f"Response from email microservice: Status Code {response.status_code}, Response Text: {response.text}")
                        if response.status_code == 200:
                            flash("Subscription successful! Daily emails will be sent.")
                        else:
                            flash("Subscription failed. Could not send email.")
                    except Exception as e:
                        logger.error(f"Failed to send subscription request: {e}")
                        flash("Subscription failed. Could not connect to email service.")

    return render_template("index.html", weather_info=weather_info)


@app.route("/download-image", methods=["GET"])
def download_image():
    s3_url = BUCKET
    local_filename = IMAGE

    with requests.get(s3_url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return send_file(local_filename, as_attachment=True)


class Testing(unittest.TestCase):
    def test_connectivity(self):
        with app.test_client() as client:
            response = client.options('/')
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    test_loader = unittest.TestLoader()
    test_suite = test_loader.loadTestsFromTestCase(Testing)
    test_result = unittest.TextTestRunner().run(test_suite)

    if test_result.wasSuccessful():
        app.run()
    else:
        print("Unittests failed")
        exit(1)
