import time
import serial
from curses import ascii
import meteblueAPI
import database_avalanche

def initialize_phone():
    """Initializes the phone connection via serial port."""
    phone = serial.Serial("/dev/ttyS0", 115200, timeout=1)
    phone.write(b'ATZ\r')
    print(phone.readall().decode())
    phone.write(b"AT+CMGF=1\r")
    print(phone.readall().decode())
    return phone

def read_unread_messages(phone):
    """Reads unread messages from the phone."""
    phone.write(b'AT+CMGL="REC UNREAD"\r')
    return phone.readall().decode()

def parse_messages(data):
    """Parses the raw data from the phone into individual messages."""
    messages = []
    parts = data.split("+CMGL:")
    for part in parts[1:]:
        lines = part.splitlines()
        if len(lines) >= 2:
            header = lines[0].split(",")
            cmglID = header[0].strip()
            num = header[2].replace('"', '').strip()
            message = lines[1].strip()
            messages.append((cmglID, num, message))
    return messages

def send_message(phone, num, response):
    """Sends a message response to a given phone number."""
    phone.write(b'AT+CMGS="' + num.encode() + b'"\r')
    time.sleep(0.5)
    phone.write(response.encode() + b"\r")
    time.sleep(0.5)
    phone.write(ascii.ctrl('z').encode())
    time.sleep(2)
    print("Response sent:")

def delete_message(phone, cmglID):
    """Deletes a message with the given cmglID."""
    phone.write(b"AT+CMGD=" + str(cmglID).encode() + b"\r")

def handle_message(phone, num, cmglID, message):
    """Handles the incoming message and sends an appropriate response."""
    print("Received unread message from:", num)
    print("Message content:", message)
    
    if message == "7":
        responses = database_avalanche.format_text_avalanche(1)
        for response in responses:
            send_message(phone, num, response)
            time.sleep(20)  # Ensure phone is ready for the next message
    else:
        if len(message) > 2:
            # Split the message at the comma
            parts = message.split(",")
            if len(parts) >= 2:
                # Extract latitude and longitude
                lat, lon = parts[:2]
                # Call format_data function with lat and lon
                sms_data = meteblueAPI.format_data(lat.strip(), lon.strip())
                # Send the formatted data as an SMS response
                send_message(phone, num, sms_data)
                time.sleep(15)  # Ensure phone is ready for the next message
            else:
                send_message(phone, num, """
Coords: Decimal Degrees
LAT,LON
S & W as negatives
e.g -34.532,25.432

Avalanche Advisory:
7: Aoraki / Mt Cook""")
                time.sleep(15)  # Ensure phone is ready for the next message
        else:
            # Respond with instructions for longer input
            send_message(phone, num, """
Coords: Decimal Degrees
LAT,LON
S & W as negatives
e.g -34.532,25.432

Avalanche Advisory:
7: Aoraki / Mt Cook                         
""")
            time.sleep(15)  # Ensure phone is ready for the next message
    
    delete_message(phone, cmglID)


def check_for_messages(phone):
    """Continuously checks for and processes unread messages."""
    while True:
        print("### Checking for SMS ###")
        data = read_unread_messages(phone)
        messages = parse_messages(data)
        
        for cmglID, num, message in messages:
            handle_message(phone, num, cmglID, message)
        
        time.sleep(5)
