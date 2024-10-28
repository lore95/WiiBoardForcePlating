import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import re
from collections import deque
import json
from datetime import datetime
import time
import threading

# Configure the serial connection
_conf = input("Which system are u using? MAC or WIN \n").upper()

# Configure the serial connection
portName = input("provide yur device name eg: for mac /dev/cu.usbmodem11101 or for windows COM6 \n")
ser = serial.Serial(
    port=portName,         # Set to the appropriate COM port
    baudrate=9600,       # Adjust to match your device's baud rate
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1            # Timeout for reading (in seconds)
)

file_name = input("What name do you want to give you json file with the pressure readings? default name will be: sensor_data.json) : ")
# Array to store the uncomputed data read from COM or dev/cu port
uncomputedData = []
threadFinished = False
fileIsSaved = False
# Initialize deques to store recent data points
t0 = 0 
t_data = []
v1_data = []    # Stores V1 values, up to 100 points
v2_data = []   # Stores V2 values, up to 100 points
v3_data = []    # Stores V3 values, up to 100 points
v4_data = []  # Stores V4 values, up to 100 points


# Fonction pour enregistrer les données en JSON après avoir collecté toutes les valeurs
def save_data_to_json():
    try:
        print('test')
        for i in range(len(v1_data)):
            # Crée une liste de dictionnaires pour chaque entrée de données
            data = [
                {
                    'T': t_data[i],
                    'V1': v1_data[i],
                    'V2': v2_data[i],
                    'V3': v3_data[i],
                    'V4': v4_data[i]
                }
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


def readFromSerialPort():
    """Thread function to read data from COM port and append it to uncomputedData array."""
    while threadFinished == False:
        # Read a line from the serial port
        raw_data = ser.read(ser.in_waiting or 1).decode('utf-8').strip()
        lines = raw_data.split('\n')  # Split data into individual lines
        for line in lines:
            # Use regex to match the expected format for each line
            match = re.match(r'Time:(-?\d+),V1:(-?\d+),V2:(-?\d+),V3:(-?\d+),V4:(-?\d+)', line.strip())
            if match:
                # Append the line to uncomputedData if it matches the format
                uncomputedData.append(line.strip())
        
def elaboarteData():
    global t0
    while uncomputedData:
        # Get the first item (FIFO approach)
        line = uncomputedData.pop(0)
        # Match the expected format again to extract values
        match = re.match(r'Time:(-?\d+),V1:(-?\d+),V2:(-?\d+),V3:(-?\d+),V4:(-?\d+)', line)
        if match:
            # Pass the extracted values to computingData
            t0 = t0 + int(match.group(1))/2400000
            t_data.append(t0)
            v1_data.append(getWeight(1,int(match.group(2))))
            v2_data.append(getWeight(2,int(match.group(3))))
            v3_data.append(getWeight(3,int(match.group(4))))
            v4_data.append(getWeight(4,int(match.group(5))))
            print(match.group(2), match.group(3), match.group(4), match.group(5))
        else:
            print("the line: " + line + " did not match the format and has been removed")
    
    print("all read data has been elaborated, quitting threads and executing the save to json operation")
    save_data_to_json()
    fileIsSaved = True

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
    sensor_labels = ['V1', 'V2', 'V3', 'V4']
    for label in sensor_labels:
        # input_file = 'regression_' + label + '_' + str(sps) + '_' + str(gain) + '.json'
        if _conf == "MAC":
            input_file = f'reading/regression_{label}_{sps}_{gain}.json'
        else:
            input_file = f'readings\\regression_{label}_{sps}_{gain}.json'
        
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

def getWeight(sensorNumber, sensorValue):
    if(sensorNumber ==1):
        return( V1Slope * sensorValue + V1Intercept)
    elif(sensorNumber == 2):
        return(V2Slope * sensorValue + V2Intercept)
    elif(sensorNumber == 3):
        return(V3Slope * sensorValue + V3Intercept)
    elif(sensorNumber == 4):
        return(V4Slope * sensorValue + V4Intercept)

# Example usage to get individual variables
V1Slope, V2Slope, V3Slope, V4Slope, V1Intercept, V2Intercept, V3Intercept, V4Intercept = getSlopes()

# Creating threads
thread1 = threading.Thread(target=readFromSerialPort)
thread2 = threading.Thread(target=elaboarteData)

# Start threads
thread1.start()
print("waiting for sesor data before elaborating it")
time.sleep(1) #I wait one second before starting to elaborate data
thread2.start()
input("Press the enter key when you are done reading")

threadFinished = True
# Close the serial port after closing the plot window
while(fileIsSaved == False ):
    time.sleep(1) # I was for a second to see if the file has been saved and I can now join the threads
thread1.Join()
thread2.Join()
ser.close()

print("file has been saved at " + file_name + " hope you get all u need from it sincerely DataFusion")

