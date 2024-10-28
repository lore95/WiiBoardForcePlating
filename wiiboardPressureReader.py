import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import re
from collections import deque
import json
from datetime import datetime
import time

# Configure the serial connection
portName = input("provide yur device name eg: /dev/cu.usbmodem11101 \n")
ser = serial.Serial(
    port=portName,         # Set to the appropriate COM port
    baudrate=9600,       # Adjust to match your device's baud rate
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1            # Timeout for reading (in seconds)
)


# Initialize deques to store recent data points
t_data = []
v1_data = []    # Stores V1 values, up to 100 points
v2_data = []   # Stores V2 values, up to 100 points
v3_data = []    # Stores V3 values, up to 100 points
v4_data = []  # Stores V4 values, up to 100 points

# Create a figure and axis for plotting
fig, ax = plt.subplots()
line1, = ax.plot([], [], 'r-', label='V1')
line2, = ax.plot([], [], 'g-', label='V2')
line3, = ax.plot([], [], 'b-', label='V3')
line4, = ax.plot([], [], 'y-', label='V4')

# Example usage to get individual variables
V1Slope, V2Slope, V3Slope, V4Slope, V1Intercept, V2Intercept, V3Intercept, V4Intercept = getSlopes()


# Fonction pour enregistrer les données en JSON après avoir collecté toutes les valeurs
def save_data_to_json(t, v1, v2, v3, v4, timestamp):
    try:
        file_name = input("Veuillez entrer le nom du fichier (par défaut: sensor_data.json) : ")
        # Ajoute un horodatage pour chaque enregistrement
        timestamps = [datetime.now() for _ in range(len(t))]

        # Crée une liste de dictionnaires pour chaque entrée de données
        data = [
            {
                'timestamp': timestamps[i],
                'T': t[i],
                'V1': v1[i],
                'V2': v2[i],
                'V3': v3[i],
                'V4': v4[i]
            }
            for i in range(len(t))
        ]

        # Lecture du fichier existant ou création s'il n'existe pas
        try:
            with open(file_name + '.json', 'r') as file:
                data_list = json.load(file)  # Charger les données existantes
        except (FileNotFoundError, json.JSONDecodeError):
            data_list = []  # Si le fichier n'existe pas ou est vide

        # Ajoute les nouvelles données collectées
        data_list.extend(data)

        # Écriture dans le fichier JSON (avec indentation pour lisibilité)
        with open(file_name + '.json', 'w') as file:
            json.dump(data_list, file, indent=4)

    except Exception as e:
        print(f"Erreur lors de l'enregistrement des données : {e}")


def init():
    ax.set_xlim(0, 100)  # Set x-axis limit (number of data points)
    ax.set_ylim(-1000000, 1000)  # Set y-axis limit (adjust as needed)
    ax.set_xlabel('Sample Number')
    ax.set_ylabel('Values')
    ax.legend(loc='upper left')
    return line1, line2, line3, line4

def getPressure():
    line = ser.readline().decode('utf-8').strip()
    match = re.match(r'Time:(-?\d+),V1:(-?\d+),V2:(-?\d+),V3:(-?\d+),V4:(-?\d+)', line)
    if match:
        _, v1, v2, v3, v4 = map(int, match.groups())
        return (v1, v2, v3, v4)


def update(frame):
    line = ser.readline().decode('utf-8').strip()
    # t0 = time.time()
    match = re.match(r'Time:(-?\d+),V1:(-?\d+),V2:(-?\d+),V3:(-?\d+),V4:(-?\d+)', line)
    if match:
        t, v1, v2, v3, v4 = map(int, match.groups())
        # print(f'V1, V2, V3, V4:{v1, v2, v3, v4}')
        print(f"Time:{t/24000000}")
        print(getWeight(v1))
        t_data.append(t)
        v1_data.append(v1)
        v2_data.append(v2)
        v3_data.append(v3)
        v4_data.append(v4)

        # save_data_to_json(v1, v2, v3, v4)
        
        # Update plot data
        x = range(len(v1_data))  # X-axis represents sample index
        line1.set_data(x, v1_data)
        line2.set_data(x, v2_data)
        line3.set_data(x, v3_data)
        line4.set_data(x, v4_data)

        ax.set_xlim(max(0, len(v1_data) - 100), len(v1_data))
        # t1 = time.time()
        # print(f'Time:{t1-t0}')
        return line1, line2, line3, line4 #timestamp

sensor_labels = ['V1', 'V2', 'V3', 'V4']  # Assuming these are the sensor labels

def getSlopes(sps=640, gain=128):
    """
    Get the slope and intercept values from the regression JSON files for each sensor.
    
    Args:
    sps (int): Samples per second, default is 640.
    gain (int): Gain value, default is 128.
    
    Returns:
    tuple: A tuple containing all slope and intercept values for V1, V2, V3, and V4.
    """
    slopes = []
    intercepts = []
    
    for label in sensor_labels:
        # input_file = 'regression_' + label + '_' + str(sps) + '_' + str(gain) + '.json'
        if _conf == "MAC":
            input_file = f'sensor_data/results/regression_{label}_{sps}_{gain}.json'
        else:
            input_file = f'sensor_data\\results\\regression_{label}_{sps}_{gain}.json'
        
        try:
            # Open and load the JSON file
            with open(input_file, 'r') as f:
                data = json.load(f)
                # Extract the slope and intercept values
                slope = data[0]['slope']
                intercept = data[0]['intercept']
                
                slopes.append(slope)
                intercepts.append(intercept)
        
        except FileNotFoundError:
            print(f"File not found: {input_file}")
        except json.JSONDecodeError:
            print(f"Error decoding JSON file: {input_file}")
        except (KeyError, IndexError):
            print(f"Error reading slope/intercept from: {input_file}")
    
    # Unpack the slopes and intercepts and return as separate variables
    return (*slopes, *intercepts)

def getWeight(v1,v2,v3,v4):
    weightedV1 = V1Slope * v1 + V1Intercept
    weightedV2 = V2Slope * v2 + V2Intercept
    weightedV3 = V3Slope * v3 + V3Intercept
    weightedV4 = V4Slope * v4 + V4Intercept
    return (weightedV1,weightedV2,weightedV3,weightedV4)
    
if __name__ == '__main__':
    # Set up animation
    ani = animation.FuncAnimation(fig, update, init_func=init, blit=True, interval=0.001)


    plt.show()

    save_data_to_json(t_data, v1_data, v2_data, v3_data, v4_data)


    # Close the serial port after closing the plot window
    ser.close()

