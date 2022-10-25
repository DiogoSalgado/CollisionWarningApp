import math
from numpy import * 

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
    vehicles_safety_limits = [3,3,1.5,1.5] 
    return vehicles_safety_limits

def main(neighbors_information, self_information):
    
    # Variables
    safety_zone_limits = {}
    vehicles_safety_zone = {}
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


    for key in neighbors_information:
        safety_zone_limits[key] = vehicleSafetyLimits(neighbors_information[key][2])
        neighbors_information[key][3] = float(math.radians(neighbors_information[key][3])) 
        distance[key] = 0
        vehicles_safety_zone[key] = calculateZone(neighbors_information[key], safety_zone_limits[key])

    removable_keys = []

    while len(distance)>0:
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
                else: # Collision not detected, continue avaluating
                    neighbors_information[key] = predictMovement(neighbors_information[key],0.1)
                    vehicles_safety_zone[key] = calculateZone(neighbors_information[key], safety_zone_limits[key])

            else: removable_keys.append(key)
        
        for key in removable_keys: distance.pop(key)

        self_information[1] = predictMovement(self_information[1], 0.1)
        vehicles_safety_zone[self_information[0]] = calculateZone(self_information[1], safety_zone_limits[self_information[0]])


####################### Tests #################################

if __name__ == "__main__":

    self_information = list(["0", [20,15,120,90]])
    neighbors_infos = {"1": [20,50,0,90], "2": [20,90,0,0]}

    main(neighbors_infos, self_information)