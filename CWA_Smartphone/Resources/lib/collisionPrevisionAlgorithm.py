import math
from kivy.app           import App
from kivy.clock         import Clock

'''
self_information        = { "id": id, "info": {"latitude": lat, "longitude": lon, "speed": speed, "direction": direction}}
neighbors_information   = { id: {"latitude": lat, "longitude": lon, "speed": speed, "direction": direction, "x_coord": x, "y_coord": y},
                            id: {"latitude": lat, "longitude": lon, "speed": speed, "direction": direction, "x_coord": x, "y_coord": y}
                          }
'''

class CollisionPrevisionAlgorithm():

    self_information        = None
    neighbors_information   = None

    collisionDetected       = False

    def __init__(self, self_information, neighbors_information) -> None:

        self.self_information       = self_information
        self.neighbors_information  = neighbors_information

        self.main()


    def main(self):
        
        # Variables
        safety_zone_limits      = {}    # { id: {"lf": lf, "le": le, "wr": wr, "wl": wl}}
        vehicles_safety_zone    = {}    # { id: {"A": [x,y], "B": [x,y], "C": [x,y], "D": [x,y], "E": [x,y]}}
        distance                = {}    # { id: distance}

        removable_keys = []

        # 1 - Get safety zone limits for every vehicle
        # 2 - Calculate safety zone
        # 3 - Calculate distance between vehicles
        # 4 - Detect collisions
        # 5 - Predict next position

        # Change self information
        self.self_information["info"]["direction"]  = float(math.radians(self.self_information["info"]["direction"]))
        self.self_information["info"]["x_coord"]    = 0
        self.self_information["info"]["y_coord"]    = 0

        safety_zone_limits      [self.self_information["id"]]   = self.vehicleSafetyLimits(self.self_information["info"]["speed"])
        vehicles_safety_zone    [self.self_information["id"]]   = self.calculateZone(self.self_information["info"], safety_zone_limits[self.self_information["id"]])

        # Get information from neighbors

        for key in self.neighbors_information:
            self.neighbors_information[key]["direction"] = float(math.radians(self.neighbors_information[key]["direction"])) 

            safety_zone_limits[key]     = self.vehicleSafetyLimits(self.neighbors_information[key]["speed"])
            vehicles_safety_zone[key]   = self.calculateZone(self.neighbors_information[key], safety_zone_limits[key])
            
            distance[key] = 0

        while len(distance)>0:
            print(vehicles_safety_zone)
            removable_keys.clear()

            # Calculate distance beetween vehicles (if is getting bigger, stop calculating)
            for key in distance:
                actual_distance = math.sqrt((self.neighbors_information[key]["x_coord"] - self.self_information["info"]["x_coord"])**2 + (self.neighbors_information[key]["y_coord"]-self.self_information["info"]["y_coord"])**2)

                if distance[key] == 0 or distance[key] > actual_distance:
                    distance[key] = actual_distance
                    warning = self.collisionWarning(vehicles_safety_zone[self.self_information["id"]], vehicles_safety_zone[key])
                    
                    if warning: # Collision Detected, dont predict again
                        print("\nVehicle " + str(self.self_information["id"]) + ": Collision detected with vehicle " + str(key))
                        removable_keys.append(key)

                        # Action to show the collision warning to the driver
                        app = App.get_running_app()
                        Clock.schedule_once(app.root.ids.mapview.addAlert)

                        self.collisionDetected = True

                    else: # Collision not detected, continue avaluating
                        self.predictMovement(self.neighbors_information[key], 0.1)
                        vehicles_safety_zone[key] = self.calculateZone(self.neighbors_information[key], safety_zone_limits[key])

                else: removable_keys.append(key)
            
            for key in removable_keys: distance.pop(key)

            self.predictMovement(self.self_information["info"], 0.1)
            vehicles_safety_zone[self.self_information["id"]] = self.calculateZone(self.self_information["info"], safety_zone_limits[self.self_information["id"]])

        
        if not self.collisionDetected: 
            app = App.get_running_app()
            Clock.schedule_once(app.root.ids.mapview.removeAlert)

####################### Auxiliary Functions #################################

    '''
    Function: calculateZone(self, vehicle, limits)
    Params:
        dictionary  vehicle -> vehicle information: coordinates, speed and direction
            {"latitude": lat, "longitude": lon, "speed": speed, "direction": direction, "x_coord": x, "y_coord": y}
        dictionary  limits  -> safety zone limits size
            {"lf", "le", "wr", "wl"}
    Return value:
        dictionary zone_coord -> Safety zone edges coordinates, based on coordinates 
            {"A": [x,y], "B": [x,y], "C": [x,y], "D": [x,y], "E": [x,y]}

    Description: Calculate safety zone edges
    '''

    def calculateZone(self, vehicle, limits):

        coord = {"A": [vehicle["x_coord"], vehicle["y_coord"]],
                 "B": [0,0],
                 "C": [0,0],
                 "D": [0,0],
                 "E": [0,0]
                }

        coord["B"][0] = vehicle["x_coord"] + limits["lf"]*math.cos(vehicle["direction"]) - limits["wl"]*math.sin(vehicle["direction"])  # Bx = Ax + Lf cos(0) - Wl sin(0)
        coord["B"][1] = vehicle["y_coord"] + limits["lf"]*math.sin(vehicle["direction"]) + limits["wl"]*math.cos(vehicle["direction"])  # By = Ay + Lf sin(0) + Wl cos(0)

        coord["C"][0] = vehicle["x_coord"] + limits["lf"]*math.cos(vehicle["direction"]) + limits["wr"]*math.sin(vehicle["direction"])  # Cx = Ax + Lf cos(0) + Wr sin(0)
        coord["C"][1] = vehicle["y_coord"] + limits["lf"]*math.sin(vehicle["direction"]) - limits["wl"]*math.cos(vehicle["direction"])  # Cy = Ay + Lf sin(0) - Wl cos(0)

        coord["D"][0] = vehicle["x_coord"] - limits["le"]*math.cos(vehicle["direction"]) + limits["wr"]*math.sin(vehicle["direction"])  # Dx = Ax - Le cos(0) + Wr sin(0)
        coord["D"][1] = vehicle["y_coord"] - limits["le"]*math.sin(vehicle["direction"]) - limits["wr"]*math.cos(vehicle["direction"])  # Dy = Ay - Le sin(0) - Wr cos(0)
                        
        coord["E"][0] = vehicle["x_coord"] - limits["le"]*math.cos(vehicle["direction"]) - limits["wl"]*math.sin(vehicle["direction"])  # Ex = Ax - Le cos(0) - Wl sin(0)
        coord["E"][1] = vehicle["y_coord"] - limits["le"]*math.sin(vehicle["direction"]) + limits["wr"]*math.cos(vehicle["direction"])  # Ey = Ay - Le sin(0) + Wr cos(0)         
            
        return coord

    '''
    Function: predictMovement(vehicle, rate)
    Params:
        Dictionary vehicle -> vehicle information
             {"latitude": lat, "longitude": lon, "speed": speed, "direction": direction, "x_coord": x, "y_coord": y}
        float rate -> refresh rate

    Description: Predict vehicle's next movement
    '''

    def predictMovement(self, vehicle, rate):
        vehicle["x_coord"]      = vehicle["x_coord"] + (vehicle["speed"]*1000/3600) * math.cos(vehicle["direction"]) * rate         # Xk+1 = Xk + Vk cos(0)T
        vehicle["y_coord"]      = vehicle["y_coord"] + (vehicle["speed"]*1000/3600) * math.sin(vehicle["direction"]) * rate         # Xk+1 = Xk + Vk cos(0)T


    '''
    Function: collisionWarning(vehicle1, vehicle2)
    Params:
        Dictionary vehicle1 -> Information of vehicle1
            {"A": [x,y], "B": [x,y], "C": [x,y], "D": [x,y], "E": [x,y]
        Dictionary vehicle2 -> Information of vehicle2
            {"A": [x,y], "B": [x,y], "C": [x,y], "D": [x,y], "E": [x,y]
    Return value:
        Boolean

    Description: Detects an overlapping of vehicles, based on their position
    '''

    def collisionWarning(self, vehicle1, vehicle2):

        vehicle1_x = [vehicle1["B"][0], vehicle1["C"][0], vehicle1["D"][0], vehicle1["E"][0]]
        vehicle1_y = [vehicle1["B"][1], vehicle1["C"][1], vehicle1["D"][1], vehicle1["E"][1]]

        vehicle2_x = [vehicle2["B"][0], vehicle2["C"][0], vehicle2["D"][0], vehicle2["E"][0]]
        vehicle2_y = [vehicle2["B"][1], vehicle2["C"][1], vehicle2["D"][1], vehicle2["E"][1]]

        sx = (max(vehicle1_x + vehicle2_x) - min(vehicle1_x + vehicle2_x)) - ((max(vehicle1_x) - min(vehicle1_x)) + (max(vehicle2_x) - min(vehicle2_x)))
        sy = (max(vehicle1_y + vehicle2_y) - min(vehicle1_y + vehicle2_y)) - ((max(vehicle1_y) - min(vehicle1_y)) + (max(vehicle2_y) - min(vehicle2_y)))

        if sx < 0.0 and sy < 0.0:   return True
        else:                       return False


    '''
    Function: vehicleSafetyLimits(speed)
    Params:
        float speed -> vehicle's speed
    Return value:
        Dictionary limits -> limits of safety zone
            {"lf": lf, "le": le, "wr": wr, "wl": wl}

    Description -> Definition of vehicle's safety zone limits based on speed
    '''
    def vehicleSafetyLimits(self, speed):
        limits = {"lf": 3, "le": 3, "wr": 1.5, "wl": 1.5}
        return limits

    
####################### Tests #################################

if __name__ == "__main__":

    sInformation = {"id": "0", "info": {"latitude": 38.759300, "longitude": -9.114964, "speed": 50, "direction": 0}}
    nInfos = {"1": {"latitude": 0, "longitude": 0, "speed": 0, "direction": 0, "x_coord": 20, "y_coord": 0}}

    CollisionPrevisionAlgorithm(sInformation, nInfos)