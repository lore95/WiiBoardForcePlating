import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import re
import time
import threading

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

# Shared data
data_buffer = []
buffer_lock = threading.Lock()
previous_values = None  # Store last valid values

# Define max allowable jump
MAX_JUMP = 5000 # Adjust as per expected sensor variation

# Function to read and store data with jump detection
def read_data():
    global data_buffer, previous_values
    while True:
        line = ser.readline().decode('utf-8').strip()
        match = re.match(r'Time:(-?\d+),V1:(-?\d+),V2:(-?\d+),V3:(-?\d+),V4:(-?\d+)', line)
        if match:
            _, v1, v2, v3, v4 = map(int, match.groups())

            # Check for sudden jumps
            if previous_values:
                prev_v1, prev_v2, prev_v3, prev_v4 = previous_values
                if any(abs(new - old) > MAX_JUMP for new, old in zip((v1, v2, v3, v4), previous_values)):
                    print(f"⚠️ Sudden jump detected! Prev: {previous_values}, New: {v1, v2, v3, v4}")
                    continue  # Ignore this reading

            # Update previous values
            previous_values = (v1, v2, v3, v4)

            # Store valid data
            with buffer_lock:
                data_buffer.append((v1, v2, v3, v4))
            time.sleep(0.1)  # Adjust sampling rate

# Function to plot data
def update_plot(frame):
    global data_buffer
    with buffer_lock:
        if len(data_buffer) >= 10:
            v1, v2, v3, v4 = data_buffer.pop(0)  # Pop first element

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
    ax.plot(v1_data, label='V1', color='r')
    ax.plot(v2_data, label='V2', color='g')
    ax.plot(v3_data, label='V3', color='b')
    ax.plot(v4_data, label='V4', color='y')
    ax.legend()
    ax.set_title("Live Sensor Data")
    ax.set_xlabel("Time (Arbitrary Units)")
    ax.set_ylabel("Voltage")

# Start the reading thread
reading_thread = threading.Thread(target=read_data, daemon=True)
reading_thread.start()

# Initialize Matplotlib plot
fig, ax = plt.subplots()
v1_data, v2_data, v3_data, v4_data = [], [], [], []

# Start the animation loop
ani = animation.FuncAnimation(fig, update_plot, interval=200)

plt.show()