import time
import serial
from curses import ascii
import meteblueAPI
import logging

# Configure logging
logging.basicConfig(filename='sms_app.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


def initialize_phone():
    """Initializes the phone connection via serial port."""
    try:
        phone = serial.Serial("/dev/serial0", 9600, timeout=1)
        phone.write(b'ATZ\r')
        logging.info(f"ATZ response: {phone.readall().decode()}")
        phone.write(b"AT+CMGF=1\r")
        logging.info(f"AT+CMGF=1 response: {phone.readall().decode()}")
        logging.info("*** Phone Initalized ***")
        return phone
    except serial.SerialException as e:
        logging.error(f"Error initializing phone: {e}")
        raise

def read_unread_messages(phone):
    """Reads unread messages from the phone."""
    try:
        phone.write(b'AT+CMGL="REC UNREAD"\r')
        return phone.readall().decode()
    except serial.SerialException as e:
        logging.error(f"Error reading unread messages: {e}")
        return ""

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
    try:
        phone.write(b'AT+CMGS="' + num.encode() + b'"\r')
        time.sleep(0.5)
        phone.write(response.encode() + b"\r")
        time.sleep(0.5)
        phone.write(ascii.ctrl('z').encode())
        time.sleep(2)
        logging.info(f"Response sent to {num}: {response}")
    except serial.SerialException as e:
        logging.error(f"Error sending message to {num}: {e}")

def delete_message(phone, cmglID):
    """Deletes a message with the given cmglID."""
    try:
        phone.write(b"AT+CMGD=" + str(cmglID).encode() + b"\r")
        logging.info(f"Deleted message with CMGL ID: {cmglID}")
    except serial.SerialException as e:
        logging.error(f"Error deleting message with CMGL ID {cmglID}: {e}")

def handle_message(phone, num, cmglID, message):
    """Handles the incoming message and sends an appropriate response."""
    logging.info(f"Received unread message from: {num}")
    logging.info(f"Message content: {message}")

    try:
        if 2 < len(message) < 20:
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
        # elif len(message) > 20:
        #     decode_pdu(message)
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
    except Exception as e:
        logging.error(f"Error handling message from {num} (CMGL ID: {cmglID}): {e}")

def check_for_messages(phone):
    """Continuously checks for and processes unread messages."""
    while True:
        try:
            logging.info("### Checking for SMS ###")
            data = read_unread_messages(phone)
            if data: #Only proceed if data is not empty (i.e. no error reading messages)
                messages = parse_messages(data)
                
                for cmglID, num, message in messages:
                    handle_message(phone, num, cmglID, message)
            
            time.sleep(5)
        except Exception as e:
            logging.critical(f"Unhandled exception in check_for_messages loop: {e}", exc_info=True)
            # Potentially add a longer sleep here or a mechanism to alert if loop keeps failing
            time.sleep(60) # Sleep longer if a critical error occurs


def decode_pdu(pdu):
    """Decodes a PDU (Protocol Data Unit) formatted SMS message into readable text.

    This function handles a specific PDU format and may need adjustments
    if the PDU structure from the modem changes.
    It assumes the actual message content starts after a 12-character header.
    The message is then decoded from hexadecimal pairs to ASCII characters.

    Args:
        pdu (str): The PDU string received from the modem.

    Returns:
        str: The decoded text message.
    """
    # PDU decoding can be complex and modem-specific.
    # This is a basic implementation assuming a common structure.
    # Remove header part of the PDU
    message_data = pdu[12:]  # The first 12 characters are often metadata (SMSC, sender, etc.)
    
    # Convert PDU to text
    decoded_message = ''
    try:
        for i in range(0, len(message_data), 2):
            decoded_message += chr(int(message_data[i:i+2], 16))
        logging.info(f"Decoded PDU message: {decoded_message}")
    except ValueError as e:
        logging.error(f"Error decoding PDU message: {e}. PDU data: {pdu}")
        return "Error decoding message"
    return decoded_message
