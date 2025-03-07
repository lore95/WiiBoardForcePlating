import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import re
import time
import threading
import json


# # Load regression coefficients for each sensor
# def load_regression(file_name):
#     with open(file_name, "r") as file:
#         regression_data = json.load(file)
#     return regression_data[0]["slope"], regression_data[0]["intercept"]

# # Load individual slopes and intercepts for V1, V2, V3, V4
# slope_v4, intercept_v4 = load_regression("readings/regression_V1_640_128.json")
# slope_v3, intercept_v3 = load_regression("readings/regression_V2_640_128.json")
# slope_v2, intercept_v2 = load_regression("readings/regression_V3_640_128.json")
# slope_v1, intercept_v1 = load_regression("readings/regression_V4_640_128.json")

# Configure the serial connection
_conf = input("Which system are u using? MAC or WIN \n").upper()

# Configure the serial connection
portName = input("Provide your device name (e.g., for Mac /dev/cu.usbmodem11101 or for Windows COM6) \n")
ser = serial.Serial(
    port=portName,         
    baudrate=9600,       
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1            
)

def correct_bit_errors(n_channels, prior, current):
    corrected = False

    for i in range(n_channels):
        min_error = abs(current[i] - prior[i])  # Initial error value
        best_correction = current[i]

        # Check flipping 1, 2, or 3 consecutive bits (from bit 23 down to bit 10)
        for j in range(23, 9, -1):  
            for num_bits in range(1, 4):  # Flip 1 to 3 bits
                mask = sum(1 << (j - k) for k in range(num_bits))  # Generate mask for num_bits
                modified_value = current[i] ^ mask  # Apply bit flip

                # Check if new value is closer to the prior value
                if abs(modified_value - prior[i]) < min_error:
                    min_error = abs(modified_value - prior[i])
                    best_correction = modified_value
                    corrected = True

        # Apply the best correction found
        current[i] = best_correction

    return corrected

buffer_lock = threading.Lock()

# Data storage
data_buffer = []
previous_values = [0, 0, 0, 0]  # Stores previous values for V1-V4

# Function to read and store data with jump detection
def read_data():
    global data_buffer, previous_values
    while True:
        line = ser.readline().decode('utf-8').strip()
        match = re.match(r'Time:(-?\d+),V1:(-?\d+),V2:(-?\d+),V3:(-?\d+),V4:(-?\d+)', line)
        if match:
            _, v1, v2, v3, v4 = map(int, match.groups())
            print(v1, v2, v3, v4)
            new_values = [v1, v2, v3, v4]

            # Apply bit error correction
            correct_bit_errors(len(new_values), previous_values, new_values)

            with buffer_lock:
                previous_values = new_values.copy()  # Update previous values
                data_buffer.append(new_values)  # Store filtered values


# Function to convert raw sensor values to weight
def convert_to_weight(raw_value, slope, intercept):
    return slope * raw_value + intercept

# Function to plot data
def update_plot(frame):
    global data_buffer
    with buffer_lock:
        if len(data_buffer) >= 10:
            v1, v2, v3, v4 = data_buffer.pop(0)  # Pop first element

            # # Convert raw values to weight using respective regression models
            # v1_weight = convert_to_weight(v1, slope_v1, intercept_v1)
            # v2_weight = convert_to_weight(v2, slope_v2, intercept_v2)
            # v3_weight = convert_to_weight(v3, slope_v3, intercept_v3)
            # v4_weight = convert_to_weight(v4, slope_v4, intercept_v4)

            v1_data.append(v1)
            v2_data.append(v2)
            v3_data.append(v3)
            v4_data.append(v4)

            # Maintain a fixed window size for better visualization
            if len(v1_data) > 50:
                v1_data.pop(0)
                v2_data.pop(0)
                v3_data.pop(0)
                v4_data.pop(0)

    ax.clear()
    ax.plot(v1_data, label='V1 (Weight)', color='r')
    ax.plot(v2_data, label='V2 (Weight)', color='g')
    ax.plot(v3_data, label='V3 (Weight)', color='b')
    ax.plot(v4_data, label='V4 (Weight)', color='y')
    ax.legend()
    ax.set_title("Live Sensor Data (Converted to Weight)")
    ax.set_xlabel("Time (Arbitrary Units)")
    ax.set_ylabel("Weight (kg)")  # Adjust units if necessary

# Start the reading thread
reading_thread = threading.Thread(target=read_data, daemon=True)
reading_thread.start()

# Initialize Matplotlib plot
fig, ax = plt.subplots()
v1_data, v2_data, v3_data, v4_data = [], [], [], []

# Start the animation loop
ani = animation.FuncAnimation(fig, update_plot, interval=200)

plt.show()