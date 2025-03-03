import streamlit as st
from twilio.rest import Client
import googlemaps
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_location_name(api_key):
    # Initialize Google Maps client~
    gmaps = googlemaps.Client(key=api_key)
    
    # Get current location
    geocode_result = gmaps.geolocate()
    location = gmaps.reverse_geocode((geocode_result['location']['lat'], geocode_result['location']['lng']))
    location_name = location[0]['formatted_address'] if location else "Unknown Location"
    
    return location_name

def make_call_and_send_message(user_name, age, health_condition, blood_group):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    to_number = os.getenv("TO_NUMBER")
    from_number = os.getenv("FROM_NUMBER")
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    client = Client(account_sid, auth_token)
    
    # Get dynamic location
    location_name = get_location_name(api_key)
    
    # Construct the message
    message_body = (f"Emergency - Patient: {user_name}, Age: {age}, Health Condition: {health_condition}, "
                     f"Blood Group: {blood_group}, Location: {location_name}")
    
    # Make a call
    call = client.calls.create(
        twiml=f'<Response><Say>{message_body}</Say></Response>',
        to=to_number,
        from_=from_number
    )
    st.success("Call initiated. Call SID: " + call.sid)
    
    # Send a message
    message = client.messages.create(
        to=to_number,
        from_=from_number,
        body=message_body
    )
    st.success("Message sent. Message SID: " + message.sid)

def main():
    st.title("Emergency Alert System")
    
    # User input fields
    user_name = st.text_input("Enter Patient Name:", "John Doe")
    age = st.number_input("Enter Age:", min_value=1, max_value=120, value=25)
    health_condition = st.text_input("Health Condition:", "Critical")
    blood_group = st.text_input("Blood Group:", "O+")
    
    if st.button("Send Emergency Alert"):
        if all([user_name, age, health_condition, blood_group]):
            make_call_and_send_message(user_name, age, health_condition, blood_group)
        else:
            st.error("Please fill in all fields.")
    
if __name__ == "__main__":
    main()