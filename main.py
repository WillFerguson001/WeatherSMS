import threading
import sms_handler


def main():
    """Main function to initialize phone and start checking for messages."""
    phone = sms_handler.initialize_phone()
    try:
        # Start SMS handling and web scraping in separate threads
        sms_thread = threading.Thread(target=sms_handler.check_for_messages, args=(phone,))
        # web_scrape_thread = threading.Thread(target=webScrape_avalanche.time_to_scrape)
        
        sms_thread.start()
        # web_scrape_thread.start()
        
        # Wait for both threads to finish (which will never happen since they run indefinitely)
        sms_thread.join()
        # web_scrape_thread.join()
    finally:
        # Close the phone connection when done
        phone.close()

if __name__ == "__main__":
    main()
