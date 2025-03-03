import streamlit as st
from twilio.rest import Client
import googlemaps
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Debugging prints (remove these in production)
print(f"Account SID: {TWILIO_ACCOUNT_SID}")
print(f"Auth Token: {TWILIO_AUTH_TOKEN[:5]}********")  # Hide full token for security
print(f"Twilio Phone Number: {TWILIO_PHONE_NUMBER}")
print(f"Google Maps API Key Loaded: {'Yes' if GOOGLE_MAPS_API_KEY else 'No'}")

def get_location_name():
    """Get the user's current location name using Google Maps API."""
    try:
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        geocode_result = gmaps.geolocate()
        lat, lng = geocode_result['location']['lat'], geocode_result['location']['lng']
        location = gmaps.reverse_geocode((lat, lng))
        return location[0]['formatted_address'], (lat, lng)
    except Exception as e:
        st.error(f"Error fetching location: {e}")
        return "Unknown Location", (0, 0)

def get_nearest_hospital_coordinates(lat, lng):
    """Find the nearest hospital using Google Maps Places API."""
    try:
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        places_result = gmaps.places_nearby(location=(lat, lng), radius=5000, type='hospital')
        if places_result['results']:
            hospital = places_result['results'][0]
            hospital_coordinates = hospital['geometry']['location']
            return hospital_coordinates['lat'], hospital_coordinates['lng']
    except Exception as e:
        st.error(f"Error finding hospital: {e}")
    return None

def get_directions(origin, destination):
    """Fetch driving directions from the current location to the hospital."""
    try:
        gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        directions_result = gmaps.directions(origin, destination, mode="driving")
        return directions_result
    except Exception as e:
        st.error(f"Error fetching directions: {e}")
        return None

def make_call_and_send_message(patient_name, age, health_condition, blood_group, to_number):
    """Make an emergency call and send an SMS with patient details."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # Get location details
        location_name, coordinates = get_location_name()

        # Construct message
        message_body = (f"🚨 Emergency 🚨\n"
                        f"Patient: {patient_name}\n"
                        f"Age: {age}\n"
                        f"Condition: {health_condition}\n"
                        f"Blood Group: {blood_group}\n"
                        f"Location: {location_name}")

        # Make a voice call
        call = client.calls.create(
            twiml=f'<Response><Say>{message_body}</Say></Response>',
            to=to_number,
            from_=TWILIO_PHONE_NUMBER
        )
        st.success(f"Call placed successfully! Call SID: {call.sid}")

        # Send an SMS
        message = client.messages.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            body=message_body
        )
        st.success(f"SMS sent successfully! Message SID: {message.sid}")

        # Get directions to the nearest hospital
        hospital_coordinates = get_nearest_hospital_coordinates(*coordinates)
        if hospital_coordinates:
            directions_result = get_directions(coordinates, hospital_coordinates)
            if directions_result:
                st.write("📍 Directions to the nearest hospital:")
                for step in directions_result[0]['legs'][0]['steps']:
                    st.write(step['html_instructions'])
        else:
            st.error("No nearby hospitals found.")
    except Exception as e:
        st.error(f"Error making call or sending message: {e}")

def main():
    """Streamlit UI for emergency alert system."""
    st.title("🚑 Emergency Alert System")
    st.write("Enter patient details and send an emergency alert.")

    patient_name = st.text_input("Patient Name")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    health_condition = st.text_input("Health Condition")
    blood_group = st.text_input("Blood Group")
    emergency_contact = st.text_input("Emergency Contact Number", placeholder="+91XXXXXXXXXX")

    if st.button("🚨 Send Emergency Alert"):
        if not emergency_contact.startswith("+"):
            st.error("Please enter a valid phone number in international format (e.g., +91XXXXXXXXXX).")
        else:
            make_call_and_send_message(patient_name, age, health_condition, blood_group, emergency_contact)

if __name__ == "__main__":
    main()
