import binascii
import json
from math import *
import time
from kivy.clock             import Clock
import threading

from kivy.app           import App
from functools          import partial
import Resources.lib.auxiliarFunctions as Aux

from Resources.CollisionWarning.lib.collisionPrevisionAlgorithm import CollisionPrevisionAlgorithm

class ReceiveInformation():
    
    self_information        = None
    neighbors_information   = None
    cam_its                 = None
    mqtt                    = None
    earth_radius            = 6371.0

    def __init__(self) -> None:
        pass

    def run(self, self_information, neighbors_information, cam_its, mqtt):
        self.self_information       = self_information
        self.neighbors_information  = neighbors_information
        self.cam_its                = cam_its
        self.mqtt                   = mqtt

        mqtt.client.on_message = self.receiveInformation
        

    def receiveInformation(self, client, userdata, message):
        """Function that waits for MQTT messages, and process the received information
            Defined as the callback for received messages via MQTT

        Args:
            client: MQTTClient
            userdata
            message: MQTT message 
        """

        # Message Received

        # If self information is not available, dont process message (Neighbors information depends on self information)
        if self.self_information["info"] == {}:
            return
    
        # Process Information
        
        msg = message.payload.decode("utf-8")
        msg = json.loads(msg)

        # Discard sent messages
        if str(msg["stationId"]) == str(self.self_information["id"]): return

        payload = binascii.unhexlify(msg["payload"])
        
        cam = self.cam_its.decode("CAM", payload)

        # Fields format adjustments
        stationId   = cam["header"]["stationID"]
        latitude    = cam["cam"]["camParameters"]["basicContainer"]["referencePosition"]["latitude"] / 10000000
        longitude   = cam["cam"]["camParameters"]["basicContainer"]["referencePosition"]["longitude"] / 10000000
        speed       = cam["cam"]["camParameters"]["highFrequencyContainer"][1]["speed"]["speedValue"] / 100
        heading     = cam["cam"]["camParameters"]["highFrequencyContainer"][1]["heading"]["headingValue"] / 10

        if str(stationId) == str(self.self_information["id"]):  return
        if latitude == 0 or longitude == 0:                     return
        
        # Heading converting

        if      heading == 0:                           heading = 90
        elif    heading == 90:                          heading = 0
        elif    heading == 180:                         heading = 270
        elif    heading == 270:                         heading = 180
        elif    heading > 0      and heading < 90:      heading = -heading % 90
        elif    heading > 270    and heading < 360:     heading = (-heading % 90) + 90
        elif    heading > 180    and heading < 270:     heading = (-heading % 90) + 180
        elif    heading > 90     and heading < 180:     heading = (-heading % 90) + 270
        
        speed   = round(speed, 2)
        heading = round(heading, 2)

        # Change Array information
        
        self.neighbors_information[str(stationId)] = {"latitude": latitude, "longitude": longitude, "speed": speed, "heading": heading, "time": time.time()}

        # Change coordinate system
        try:
            self.convertCoordinates(self.neighbors_information[str(stationId)])
        except:
            print("Something went wrong converting coordinates!")
            return

        # Run Collision Prevision Algorithm

        alg = CollisionPrevisionAlgorithm()
        thread = threading.Thread(target=alg.run, args=(self.self_information, self.neighbors_information, "neighbor", ), daemon=True)
        thread.start()

        # Change screen information

        app = App.get_running_app()
        if app.root == None: return

        msg["info"] = Aux.extractParameters(cam)
        msg["time"] = time.time()

        app.root.ids.mapview.add_neighbor(msg)


    def convertCoordinates(self, information):
        """Function that converts geographical coordinates into a Cartesian Coordinate system

        Args:
            information: vehicle information
        """

        lat         = self.self_information["info"]["latitude"]
        lon         = self.self_information["info"]["longitude"]

        lat_r = radians(lat)
        lon_r = radians(lon)

        lat_e = radians(information["latitude"])
        lon_e = radians(information["longitude"])

        delta = acos(sin(lat_e)*sin(lat_r) + cos(lat_e)*cos(lat_r)*cos(lon_e-lon_r))

        if delta == 0.0:
            information["x_coord"] = 0.0
            information["y_coord"] = 0.0
            return

        alpha = acos((sin(lat_e)-sin(lat_r)*cos(delta))/(sin(delta)*cos(lat_r)))

        if lon_r >= lon_e:  alpha_re = 2*pi - alpha
        else:               alpha_re = alpha

        distance = self.earth_radius * delta    # Kilometers
        distance = distance * 1000              # Meters

        alpha_re = ((360.0 - degrees(alpha_re)) + 90.0) % 360.0

        x_coord = cos(radians(alpha_re)) * distance
        y_coord = sin(radians(alpha_re)) * distance

        information["x_coord"] = x_coord
        information["y_coord"] = y_coord


################ Coordinate Conversion Test ############################

if __name__ == "__main__":

    self_information = {"id": "0", "info": {"latitude": -9.110415, "longitude": 38.765960, "speed": 120, "heading": 90}}

    neighbors_infos = { "1": {"latitude":-9.110302, "longitude": 38.766699, "speed": 0, "heading": 90}, 
                        "2": {"latitude": -9.109631, "longitude": 38.766802, "speed": 0, "heading": 0},
                        "3": {"latitude": -9.109429, "longitude": 38.765765, "speed": 0, "heading": 0},
                        "4": {"latitude": -9.110415, "longitude": 38.765960, "speed": 0, "heading": 0},
                        "5": {"latitude": -9.110415, "longitude": 38.766960, "speed": 0, "heading": 0}}

    ReceiveInformation(self_information, neighbors_infos, None, None).convertCoordinates(neighbors_infos["5"])