import time
import math 

pos_array = {   
            "0": [20,15,120,90],
            "1": [20,45,0,90],
            "2": [20,90,0,0]
        }

def main(self_information, vehicles_information):
    # print("self id: " + str(id(self_information)))
    while True:
        
        # Movement simulation
        newInformation = movementSimulation(self_information[0])

        # Change information on arrays
        self_information[1] = newInformation
        vehicles_information[self_information[0]] = newInformation
        
        time.sleep(1/10)


def movementSimulation(mac):
    newPos = pos_array[mac]
    return newPos

def predict_moviment_func(vehicle, rate):
    vehicle[0]      = vehicle[0] + (vehicle[2]*1000/3600) * math.cos(vehicle[3]) * rate         # Xk+1 = Xk + Vk cos(0)T
    vehicle[1]      = vehicle[1] + (vehicle[2]*1000/3600) * math.sin(vehicle[3]) * rate         # Xk+1 = Xk + Vk cos(0)T

    return vehicle
