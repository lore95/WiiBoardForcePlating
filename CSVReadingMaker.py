import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import re
import time
import threading
import json
import csv

_conf = "MAC"

portName = "/dev/tty.usbmodem2101"

ser = serial.Serial(
    port=portName,         
    baudrate=9600,       
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1            
)

buffer_lock = threading.Lock()
data_buffer = []
previous_values = [0, 0, 0, 0]  # Stores previous values for V1-V4
stop_event = threading.Event()  # Event to stop the thread

# Function to read and store data with jump detection
def read_data():
    global data_buffer, previous_values
    index = 0  # Track the row index

    while not stop_event.is_set():  # Check for stop signal
        line = ser.readline().decode('utf-8').strip()
        match = re.match(r'Time:(-?\d+),V1:(-?\d+),V2:(-?\d+),V3:(-?\d+),V4:(-?\d+)', line)
        if match:
            _, v1, v2, v3, v4 = map(int, match.groups())
            print(index, v1, v2, v3, v4)
            new_values = [index, v1, v2, v3, v4]
            data_buffer.append(new_values)  # Store filtered values
            index += 1  # Increment index

# Function to save data buffer to a CSV file
def save_to_csv(filename="data_output1.csv"):
    with buffer_lock:
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Index", "V1", "V2", "V3", "V4"])  # Header
            writer.writerows(data_buffer)  # Write data
    print(f"Data saved to {filename}")

# Function to listen for user input (Enter key) and stop the thread
def stop_on_enter():
    input("Press Enter to stop and save data...\n")
    stop_event.set()  # Signal the thread to stop
    ser.close()  # Close serial connection
    save_to_csv()  # Save data to CSV

# Start the reading thread
reading_thread = threading.Thread(target=read_data, daemon=True)
reading_thread.start()

# Start the input listener thread
input_thread = threading.Thread(target=stop_on_enter)
input_thread.start()

# Wait for both threads to finish
input_thread.join()
reading_thread.join()

print("Data collection stopped.")