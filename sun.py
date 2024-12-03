import streamlit as st
from astral.sun import sun
from astral import LocationInfo
from datetime import date, timedelta, datetime
import ephem
import pytz
import geocoder
import requests

# List of major cities in Pakistan with their latitude, longitude, and timezone
city_coordinates = {
    "Karachi": (24.8607, 67.0011, "Asia/Karachi"),
    "Lahore": (31.5497, 74.3436, "Asia/Karachi"),
    "Islamabad": (33.6844, 73.0479, "Asia/Karachi"),
    "Peshawar": (34.0151, 71.5249, "Asia/Karachi"),
    "Quetta": (30.1798, 66.9750, "Asia/Karachi"),
    "Multan": (30.1575, 71.5249, "Asia/Karachi"),
    "Faisalabad": (31.4181, 73.0776, "Asia/Karachi"),
    "Rawalpindi": (33.5651, 73.0169, "Asia/Karachi"),
    "Sialkot": (32.4927, 74.5313, "Asia/Karachi"),
    "Hyderabad": (25.3960, 68.3773, "Asia/Karachi"),
}

# WeatherAPI key
API_KEY = "9f7b971b9cca41bca6172414240312"


# Helper function to get weather data
def get_weather(lat, lon, api_key):
    url = (
        f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={lat},{lon}&aqi=no"
    )
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather = {
            "temperature": data["current"]["temp_c"],
            "humidity": data["current"]["humidity"],
            "description": data["current"]["condition"]["text"],
            "wind_speed": data["current"]["wind_kph"],
        }
        return weather
    else:
        return None


# Helper function to get sunrise and sunset
def get_sunrise_sunset(lat, lon, tz_name, given_date):
    location = LocationInfo(latitude=lat, longitude=lon, timezone=tz_name)
    sun_data = sun(location.observer, date=given_date)
    tz = pytz.timezone(tz_name)
    sunrise = sun_data["sunrise"].astimezone(tz)
    sunset = sun_data["sunset"].astimezone(tz)
    return sunrise, sunset


# Helper function to get moon phase
def get_moon_phase(given_date):
    moon = ephem.Moon()
    moon.compute(given_date)
    phase = moon.phase / 100
    return phase


def get_visible_planets(lat, lon, input_date, sunset, sunrise):
    # Convert sunrise and sunset to UTC for comparison
    observer = ephem.Observer()
    observer.lat, observer.lon = str(lat), str(lon)
    observer.elevation = 0  # Set observer elevation to 0 for horizon calculations
    observer.date = ephem.Date(input_date)

    # Convert times to ephem.Date in UTC
    ephem_sunset = ephem.Date(sunset.astimezone(pytz.UTC))
    ephem_sunrise = ephem.Date(sunrise.astimezone(pytz.UTC))

    # Planets to check
    planets = [
        ephem.Mercury(),
        ephem.Venus(),
        ephem.Mars(),
        ephem.Jupiter(),
        ephem.Saturn(),
    ]
    visible_planets = []


def get_visible_planets(lat, lon, input_date, sunset, sunrise):
    import pytz

    observer = ephem.Observer()
    observer.lat, observer.lon = str(lat), str(lon)
    observer.date = ephem.Date(input_date)  # Convert input_date to ephem.Date
    planets = [
        ephem.Mercury(),
        ephem.Venus(),
        ephem.Mars(),
        ephem.Jupiter(),
        ephem.Saturn(),
    ]
    visible_planets = []

    # Convert sunset and sunrise to ephem.Date for comparison
    ephem_sunset = ephem.Date(sunset.astimezone(pytz.UTC))  # Ensure UTC timezone
    ephem_sunrise = ephem.Date(sunrise.astimezone(pytz.UTC))  # Ensure UTC timezone

    # Debug: Log sunset and sunrise times
    print(f"DEBUG: Sunset (UTC): {ephem_sunset}")
    print(f"DEBUG: Sunrise (UTC): {ephem_sunrise}")

    for planet in planets:
        planet.compute(observer)
        # Debug: Log planet data
        print(f"DEBUG: Planet: {planet.name}")
        print(f"DEBUG: Rise Time (UTC): {planet.rise_time}")
        print(f"DEBUG: Set Time (UTC): {planet.set_time}")
        print(f"DEBUG: Altitude: {planet.alt}")

        # Check visibility based on rise/set times and altitude
        if (
            planet.rise_time < ephem_sunrise
            and planet.set_time > ephem_sunset
            or planet.alt > 0  # Already above the horizon at sunset
        ):
            print(f"DEBUG: {planet.name} is visible!")
            visible_planets.append(planet.name)
        else:
            print(f"DEBUG: {planet.name} is not visible.")

    # Debug: Log visible planets
    print(f"DEBUG: Visible Planets: {visible_planets}")

    return visible_planets


def get_first_viewable_time(
    lat, lon, input_date, sunset, sunrise, elevation_threshold=15
):
    import pytz

    observer = ephem.Observer()
    observer.lat, observer.lon = str(lat), str(lon)
    observer.elevation = 0  # Set observer elevation to sea level
    observer.date = ephem.Date(sunset.astimezone(pytz.UTC))  # Start at sunset (UTC)

    planets = [
        ephem.Mercury(),
        ephem.Venus(),
        ephem.Mars(),
        ephem.Jupiter(),
        ephem.Saturn(),
    ]

    viewable_times = {}

    # Loop through each planet
    for planet in planets:
        current_time = ephem.Date(sunset.astimezone(pytz.UTC))  # Start at sunset
        found = False  # Track if the planet is found viewable

        # Check planet visibility iteratively
        while current_time <= ephem.Date(sunrise.astimezone(pytz.UTC)):
            observer.date = current_time
            planet.compute(observer)

            # If planet's altitude is above threshold
            if planet.alt > ephem.degrees(elevation_threshold):
                viewable_times[planet.name] = current_time
                found = True
                break  # Exit loop for this planet

            current_time += ephem.minute * 10  # Increment by 10 minutes

        # If the planet is already above the threshold at sunset
        observer.date = ephem.Date(sunset.astimezone(pytz.UTC))
        planet.compute(observer)
        if not found and planet.alt > ephem.degrees(elevation_threshold):
            viewable_times[planet.name] = ephem.Date(sunset.astimezone(pytz.UTC))

        # If the planet is never viewable during the night
        if planet.name not in viewable_times:
            viewable_times[planet.name] = None

    return viewable_times


# Streamlit UI
st.set_page_config(page_title="Sunrise, Sunset, Planets, and Weather", layout="wide")
st.title("🌞 Sunrise, Sunset, Moon Phase, Weather, and Visible Planets")

# User Inputs on Main Page
city = st.selectbox("Select a City", options=list(city_coordinates.keys()), index=0)

use_location = st.checkbox("Use My Location Instead")

if use_location:
    user_location = geocoder.ip("me")
    if user_location.ok:
        latitude, longitude = user_location.latlng
        timezone = "Asia/Karachi"
        st.success(f"Detected location: Latitude {latitude}, Longitude {longitude}")
    else:
        st.error("Could not fetch your location. Please try again or select a city.")
        latitude, longitude, timezone = None, None, None
else:
    latitude, longitude, timezone = city_coordinates[city]

date_option = st.radio(
    "Choose Date", options=["Today", "Tomorrow", "Custom Date"], index=0
)

if date_option == "Today":
    input_date = date.today()
elif date_option == "Tomorrow":
    input_date = date.today() + timedelta(days=1)
else:
    input_date = st.date_input("Select Custom Date", value=date.today())

# Calculate results only if coordinates are available
if latitude and longitude:
    sunrise, sunset = get_sunrise_sunset(latitude, longitude, timezone, input_date)
    moon_phase = get_moon_phase(input_date)
    weather = get_weather(latitude, longitude, API_KEY)
    visible_planets = get_visible_planets(
        latitude, longitude, input_date, sunset, sunrise
    )

    # Display Results
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🌅 Sunrise")
        st.markdown(
            f"<div style='text-align: left; font-size: 1.2em;'>{sunrise.strftime('%I:%M %p')}</div>",
            unsafe_allow_html=True,
        )

    with col2:
        st.subheader("🌇 Sunset")
        st.markdown(
            f"<div style='text-align: left; font-size: 1.2em;'>{sunset.strftime('%I:%M %p')}</div>",
            unsafe_allow_html=True,
        )

    with col3:
        st.subheader("🌕 Moon Phase")
        phase_description = (
            "New Moon"
            if moon_phase == 0
            else (
                "Full Moon"
                if moon_phase == 0.5
                else "Waxing" if moon_phase < 0.5 else "Waning"
            )
        )
        st.markdown(
            f"<div style='text-align: left; font-size: 1.2em;'>{phase_description} ({moon_phase * 100:.1f}%)</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # Display Weather Data
    if weather:
        st.subheader("☁️ Weather")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Temperature**: {weather['temperature']}°C")
            st.markdown(f"**Condition**: {weather['description']}")

        with col2:
            st.markdown(f"**Humidity**: {weather['humidity']}%")
            st.markdown(f"**Wind Speed**: {weather['wind_speed']} kph")
    else:
        st.warning("Weather data could not be fetched. Please try again later.")

    # Compute first viewable times
    viewable_times = get_first_viewable_time(
        latitude, longitude, input_date, sunset, sunrise
    )

    # # Display Visible Planets and Viewable Times
    # st.divider()
    # st.subheader("🪐 Visible Planets and Viewable Times")
    # for planet, viewable_time in viewable_times.items():
    #     if viewable_time:
    #         st.markdown(
    #             f"**{planet}**: Viewable after {ephem.localtime(viewable_time).strftime('%I:%M %p')}"
    #         )
    #     else:
    #         st.markdown(f"**{planet}**: Not visible tonight")

    # Display Visible Planets
    st.divider()
    st.subheader("🪐 Visible Planets in the Night Sky")
    if visible_planets:
        st.markdown(", ".join(visible_planets))
    else:
        st.markdown("No planets are visible tonight.")
else:
    st.warning("Please select a valid city or enable location access.")
