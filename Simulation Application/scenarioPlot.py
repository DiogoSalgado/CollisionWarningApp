import math
from numpy import * 
import matplotlib.pyplot as plt

def calculateZone(vehicle, limits):

    coord = [] 

    coord.append([  vehicle[0] + limits[0]*math.cos(vehicle[3]) - limits[3]*math.sin(vehicle[3]),   # XB = XA + Lf cos(0) - Wl sin(0)
                    vehicle[0] + limits[0]*math.cos(vehicle[3]) + limits[2]*math.sin(vehicle[3]),   # XC = XA + Lf cos(0) + Wr sin(0)
                    vehicle[0] - limits[1]*math.cos(vehicle[3]) + limits[2]*math.sin(vehicle[3]),   # XD = XA - Le cos(0) + Wr sin(0)
                    vehicle[0] - limits[1]*math.cos(vehicle[3]) - limits[3]*math.sin(vehicle[3])])  # XE = XA - Le cos(0) - Wl sin(0)

    coord.append([  vehicle[1] + limits[0]*math.sin(vehicle[3]) + limits[3]*math.cos(vehicle[3]),  # YB = YA + Lf sin(0) + Wl cos(0)
                    vehicle[1] + limits[0]*math.sin(vehicle[3]) - limits[3]*math.cos(vehicle[3]),  # YC = YA + Lf sin(0) - Wl cos(0)
                    vehicle[1] - limits[1]*math.sin(vehicle[3]) - limits[2]*math.cos(vehicle[3]),  # YD = YA - Le sin(0) - Wr cos(0)
                    vehicle[1] - limits[1]*math.sin(vehicle[3]) + limits[2]*math.cos(vehicle[3])]) # YE = YA - Le sin(0) + Wr cos(0)         

    return coord

def predictMovement(vehicle, rate):
    vehicle[0]      = vehicle[0] + (vehicle[2]*1000/3600) * math.cos(vehicle[3]) * rate         # Xk+1 = Xk + Vk cos(0)T
    vehicle[1]      = vehicle[1] + (vehicle[2]*1000/3600) * math.sin(vehicle[3]) * rate         # Xk+1 = Xk + Vk cos(0)T

    return vehicle

def collisionWarning(vehicle1, vehicle2):

    vehicle1_x = vehicle1[0]
    vehicle1_y = vehicle1[1]
    vehicle2_x = vehicle2[0]
    vehicle2_y = vehicle2[1]

    sx = (max(vehicle1_x + vehicle2_x) - min(vehicle1_x + vehicle2_x)) - ((max(vehicle1_x) - min(vehicle1_x)) + (max(vehicle2_x) - min(vehicle2_x)))
    sy = (max(vehicle1_y + vehicle2_y) - min(vehicle1_y + vehicle2_y)) - ((max(vehicle1_y) - min(vehicle1_y)) + (max(vehicle2_y) - min(vehicle2_y)))

    if sx < 0.0 and sy < 0.0:   return True
    else:                       return False

# Possibility of defining the safety zone based on vehicle speed
def vehicleSafetyLimits(speed):
    vehicles_safety_limits = [6,6,3,3] 
    return vehicles_safety_limits

def plot(neighbors_information, self_information):
    plt.ion()

    fig, ax = plt.subplots()

    ax.set_xlim([0,100])
    ax.set_ylim([0,100])

    # Variables
    safety_zone_limits = {}
    vehicles_safety_zone = {}
    
    beg_safety_zones = {}
    beg_init_coords = {}

    distance = {}

    # 1 - Get safety zone limits for every vehicle
    # 2 - Calculate safety zone
    # 3 - Calculate distance between vehicles
    # 4 - Detect collisions
    # 5 - Predict next position

    # Change self information
    safety_zone_limits[self_information[0]] = vehicleSafetyLimits(self_information[1][2])
    self_information[1][3] = float(math.radians(self_information[1][3]))
    vehicles_safety_zone[self_information[0]] = calculateZone(self_information[1], safety_zone_limits[self_information[0]])
    beg_safety_zones[self_information[0]] = calculateZone(self_information[1], safety_zone_limits[self_information[0]])
    beg_init_coords[self_information[0]] = self_information[1].copy()

    for key in neighbors_information:
        beg_init_coords[key] = neighbors_information[key].copy()
        safety_zone_limits[key] = vehicleSafetyLimits(neighbors_information[key][2])
        neighbors_information[key][3] = float(math.radians(neighbors_information[key][3])) 
        distance[key] = 0
        vehicles_safety_zone[key] = calculateZone(neighbors_information[key], safety_zone_limits[key])
        beg_safety_zones[key] = calculateZone(neighbors_information[key], safety_zone_limits[key])
        


    letters = ['B', 'C', 'D', 'E']

    
    removable_keys = []
    collisionFlag = False
    plot_title = ""

    while True:
        ax.set_title(plot_title)
        if collisionFlag == True:
            ax.fill((10, 90, 50),(10, 10, 90), "r")
            ax.fill((48, 52, 52, 48),(35, 35, 75, 75), "w")
            ax.fill((48, 52, 52, 48),(20, 20, 25, 25), "w")

    
            plt.pause(2)
            break

        for x in range(len(vehicles_safety_zone)):
            if str(x) not in distance and str(x) != "0": continue

            vehicleCoord = vehicles_safety_zone[str(x)]

            if str(x) == "0":   ax.fill(vehicleCoord[0], vehicleCoord[1], "darkgray")
            elif str(x) == "1": ax.fill(vehicleCoord[0], vehicleCoord[1], "darkgray")
            elif str(x) == "2": ax.fill(vehicleCoord[0], vehicleCoord[1], "darkgray")
            elif str(x) == "3": ax.fill(vehicleCoord[0], vehicleCoord[1], "darkgray")
            else:               ax.fill(vehicleCoord[0], vehicleCoord[1], "darkgray")

            if str(x) == self_information[0]:
                plt.text(self_information[1][0]-1, self_information[1][1]-1, "V"+ str(self_information[0]) + " Projection")
            else:
                plt.text(neighbors_information[str(x)][0]-1, neighbors_information[str(x)][1]-1, "V"+ str(x) + " Projection")

            # for x in range(len(letters)):
            #     plt.text(vehicleCoord[0][x], vehicleCoord[1][x], letters[x])

            for x in range(len(beg_safety_zones)):
                vehicleCoord = beg_safety_zones[str(x)]

                if str(x) == "0":   ax.fill(vehicleCoord[0], vehicleCoord[1], "limegreen")
                elif str(x) == "1": ax.fill(vehicleCoord[0], vehicleCoord[1], "limegreen")
                elif str(x) == "2": ax.fill(vehicleCoord[0], vehicleCoord[1], "limegreen")
                elif str(x) == "3": ax.fill(vehicleCoord[0], vehicleCoord[1], "limegreen")
                else:               ax.fill(vehicleCoord[0], vehicleCoord[1], "limegreen")

                plt.text(beg_init_coords[str(x)][0]-1, beg_init_coords[str(x)][1]-1, "V"+str(x))


        if len(distance) == 0: 
            plt.pause(2)
            break

        removable_keys.clear()
        # Calculate distance beetween vehicles (if is getting bigger, stop calculating)
        for key in distance:
            
            actual_distance = math.sqrt((neighbors_information[key][0]-self_information[1][0])**2 + (neighbors_information[key][1]-self_information[1][1])**2)

            if distance[key] == 0 or distance[key] > actual_distance:
                distance[key] = actual_distance
                warning = collisionWarning(vehicles_safety_zone[self_information[0]], vehicles_safety_zone[key])
                
                if warning: # Collision Detected, dont predict again
                    print("\nVehicle " + str(self_information[0]) + ": Collision detected with vehicle " + str(key))
                    #distance.pop(key)
                    removable_keys.append(key)
                    # ax.set_title("Collision detected beetween vehicle " + str(self_information[0]) + " and vehicle " + key)
                    plot_title = "Collision detected beetween vehicle " + str(self_information[0]) + " and vehicle " + key
                    ax.set_title(plot_title)
                    collisionFlag = True
                else: # Collision not detected, continue avaluating
                    neighbors_information[key] = predictMovement(neighbors_information[key], 1)
                    vehicles_safety_zone[key] = calculateZone(neighbors_information[key], safety_zone_limits[key])

            else: removable_keys.append(key)
        
        for key in removable_keys: distance.pop(key)

        self_information[1] = predictMovement(self_information[1], 1)
        vehicles_safety_zone[self_information[0]] = calculateZone(self_information[1], safety_zone_limits[self_information[0]])

        plt.pause(0.3)
        plt.cla()
        plt.draw()
        
        ax.set_xlim([0,100])
        ax.set_ylim([0,100]) 

####################### Tests #################################

if __name__ == "__main__":

    self_information = list(["0", [50,50,20,270]])
    neighbors_infos = {"1": [10,10,20,0]}

    plot(neighbors_infos, self_information)