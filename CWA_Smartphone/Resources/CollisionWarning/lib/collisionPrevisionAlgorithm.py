import math
from kivy.app           import App
from kivy.clock         import Clock
import copy
import time

from functools          import partial

'''
self_information        = { "id": id, "info": {"latitude": lat, "longitude": lon, "speed": speed, "heading": heading}}
neighbors_information   = { id: {"latitude": lat, "longitude": lon, "speed": speed (m/h), "heading": heading (degrees), "x_coord": x, "y_coord": y},
                            id: {"latitude": lat, "longitude": lon, "speed": speed, "heading": heading, "x_coord": x, "y_coord": y}
                          }
'''

class CollisionPrevisionAlgorithm():

    self_information        = None
    neighbors_information   = None

    collisionDetected       = False
    caller                  = None

    def __init__(self) -> None:
        pass

    def run(self, self_information, neighbors_information, caller):
        self.caller = caller
        self.self_information       = copy.deepcopy(self_information)
        self.neighbors_information  = copy.deepcopy(neighbors_information)

        removable = []
        for x in self.neighbors_information:
            if "x_coord" not in self.neighbors_information[x]: removable.append(x)

        for key in removable: self.neighbors_information.pop(key)
        if len(self.neighbors_information) > 0: self.main()

    def main(self):

        # Variables
        safety_zone_limits      = {}    # { id: {"lf": lf, "le": le, "wr": wr, "wl": wl}}
        vehicles_safety_zone    = {}    # { id: {"A": [x,y], "B": [x,y], "C": [x,y], "D": [x,y], "E": [x,y]}}
        distance                = {}    # { id: distance}

        removable_keys = []
        refresh_rate = 1

        # Change self information
        self.self_information["info"]["heading"]  = float(math.radians(self.self_information["info"]["heading"]))
        self.self_information["info"]["x_coord"]    = 0
        self.self_information["info"]["y_coord"]    = 0

        safety_zone_limits      [self.self_information["id"]]   = self.vehicleSafetyLimits()
        
        if self.self_information["info"]["speed"] != 0.0:
            refresh_rate                                        = 6/self.self_information["info"]["speed"]

        # Get safety zone size
        # Calculate refresh_rate
        for key in self.neighbors_information:
            self.neighbors_information[key]["heading"] = float(math.radians(self.neighbors_information[key]["heading"])) 

            safety_zone_limits[key]     = self.vehicleSafetyLimits()
            
            distance[key] = math.sqrt((self.neighbors_information[key]["x_coord"] - self.self_information["info"]["x_coord"])**2 + (self.neighbors_information[key]["y_coord"]-self.self_information["info"]["y_coord"])**2)
            distance[key] = round(distance[key], 2)
            
            if self.neighbors_information[key]["speed"] != 0.0:
                rate = 6/self.neighbors_information[key]["speed"]

                if rate < refresh_rate: refresh_rate = rate

        # 1 - Get safety zone limits for every vehicle
        # 2 - Calculate safety zone
        # 3 - Detect Collisions
        # 4 - Predict Next Positions
        # 5 - Calculate distance between vehicles

        # Max TTC = 7s

        totalIterations = 7/refresh_rate
        nIterations     = 1
        
        while len(distance)>0:
            
            if nIterations == totalIterations: break 
     
            removable_keys.clear()
            
            # Calculate self vehicle's safety zone
            vehicles_safety_zone[self.self_information["id"]] = self.calculateZone(self.self_information["info"], safety_zone_limits[self.self_information["id"]])

            
            for key in distance:
                
                # Calculate neighbor Safety Zone
                vehicles_safety_zone[key] = self.calculateZone(self.neighbors_information[key], safety_zone_limits[key])
                
                # Detect Collision
                warning = self.collisionWarning(vehicles_safety_zone[self.self_information["id"]], vehicles_safety_zone[key])
                    
                if warning: # Collision Detected, dont predict again
                
                    if self.caller == "self": timestamp = self.self_information["time"]
                    else: timestamp = self.neighbors_information[key]["time"]

                    app = App.get_running_app()
                    Clock.schedule_once(partial(app.root.ids.mapview.show_alert, timestamp, key))
                    
                    # print("Collision Detected: " + str((time.time() - self.neighbors_information[key]["time"])))
                    removable_keys.append(key)
                    self.collisionDetected = True
                    
                    continue

            if removable_keys:
                for key in removable_keys: distance.pop(key)
                removable_keys.clear()

            # Self Movement Prediction
            self.predictMovement(self.self_information["info"], refresh_rate)
            
            for key in distance:    
                # Neighbors Movement Prediction
                self.predictMovement(self.neighbors_information[key], refresh_rate)

                # Calculate distance between vehicles
                actual_distance = math.sqrt((self.neighbors_information[key]["x_coord"] - self.self_information["info"]["x_coord"])**2 + (self.neighbors_information[key]["y_coord"]-self.self_information["info"]["y_coord"])**2)
                actual_distance = round(actual_distance, 2)

                if distance[key] <= actual_distance: removable_keys.append(key)
                
            for key in removable_keys: distance.pop(key)


        if not self.collisionDetected:
            app = App.get_running_app()
            Clock.schedule_once(app.root.ids.mapview.remove_alert)
            print("COllision not detected")
            

####################### Auxiliary Functions #################################

    '''
    Function: calculateZone(self, vehicle, limits)
    Params:
        dictionary  vehicle -> vehicle information: coordinates, speed and heading
            {"latitude": lat, "longitude": lon, "speed": speed, "heading": heading, "x_coord": x, "y_coord": y}
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

        coord["B"][0] = vehicle["x_coord"] + limits["lf"]*math.cos(vehicle["heading"]) - limits["wl"]*math.sin(vehicle["heading"])  # Bx = Ax + Lf cos(0) - Wl sin(0)
        coord["B"][1] = vehicle["y_coord"] + limits["lf"]*math.sin(vehicle["heading"]) + limits["wl"]*math.cos(vehicle["heading"])  # By = Ay + Lf sin(0) + Wl cos(0)

        coord["C"][0] = vehicle["x_coord"] + limits["lf"]*math.cos(vehicle["heading"]) + limits["wr"]*math.sin(vehicle["heading"])  # Cx = Ax + Lf cos(0) + Wr sin(0)
        coord["C"][1] = vehicle["y_coord"] + limits["lf"]*math.sin(vehicle["heading"]) - limits["wl"]*math.cos(vehicle["heading"])  # Cy = Ay + Lf sin(0) - Wl cos(0)

        coord["D"][0] = vehicle["x_coord"] - limits["le"]*math.cos(vehicle["heading"]) + limits["wr"]*math.sin(vehicle["heading"])  # Dx = Ax - Le cos(0) + Wr sin(0)
        coord["D"][1] = vehicle["y_coord"] - limits["le"]*math.sin(vehicle["heading"]) - limits["wr"]*math.cos(vehicle["heading"])  # Dy = Ay - Le sin(0) - Wr cos(0)
                        
        coord["E"][0] = vehicle["x_coord"] - limits["le"]*math.cos(vehicle["heading"]) - limits["wl"]*math.sin(vehicle["heading"])  # Ex = Ax - Le cos(0) - Wl sin(0)
        coord["E"][1] = vehicle["y_coord"] - limits["le"]*math.sin(vehicle["heading"]) + limits["wr"]*math.cos(vehicle["heading"])  # Ey = Ay - Le sin(0) + Wr cos(0)         
            
        return coord

    '''
    Function: predictMovement(vehicle, rate)
    Params:
        Dictionary vehicle -> vehicle information
             {"latitude": lat, "longitude": lon, "speed": speed, "heading": heading, "x_coord": x, "y_coord": y}
        float rate -> refresh rate

    Description: Predict vehicle's next movement
    '''

    def predictMovement(self, vehicle, rate):
        vehicle["x_coord"]      = vehicle["x_coord"] + vehicle["speed"] * math.cos(vehicle["heading"]) * rate         # Xk+1 = Xk + Vk cos(0)T
        vehicle["y_coord"]      = vehicle["y_coord"] + vehicle["speed"] * math.sin(vehicle["heading"]) * rate         # Xk+1 = Xk + Vk cos(0)T


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
    def vehicleSafetyLimits(self):
        limits = {"lf": 3, "le": 3, "wr": 1.5, "wl": 1.5}
        return limits


####################### Tests #################################

if __name__ == "__main__":

    sInformation = {"id": "0", "info": {"latitude": 38.759300, "longitude": -9.114964, "speed": 50, "heading": 0}}
    nInfos = {"1": {"latitude": 0, "longitude": 0, "speed": 0, "heading": 0, "x_coord": 20, "y_coord": 0}}

    CollisionPrevisionAlgorithm(sInformation, nInfos)