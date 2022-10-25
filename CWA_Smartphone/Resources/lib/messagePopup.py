from Resources.dialogs.camDialog    import CamDialog
from Resources.dialogs.cursorDialog   import CursorDialog

class MessagePopupCam(CamDialog):

    stationTypes = {
        0: "Unknown",
        1: "Pedestrian",
        2: "Cyclist",
        3: "Moped",
        4: "Motorcycle",
        5: "Passenger Car",
        6: "Bus",
        7: "Light Truck",
        8: "Heavy Truck",
        9: "Trailer",
        10: "Special Vehicle",
        11: "Tram",
        15: "RSU"
    }

    vehicleRoles = {
        0: "Default",
        1: "Public Transport",
        2: "Special Transport",
        3: "Dangerous Goods",
        4: "RoadWork",
        5: "Rescue",
        6: "Emergency",
        7: "Safety Car",
        8: "Agriculture",
        9: "Commercial",
        10: "Military",
        11: "Road Operator",
        12: "Taxi"
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def changeParameters(self, message):

        self.title = "CAM Information"

        if "stationID"      in message: self.stationId      = str(message["stationID"])       
        if "stationType"    in message:  

            if message["stationType"] in self.stationTypes:
                self.stationType    = self.stationTypes[message["stationType"]]
            else:
                self.stationType = "Station Type undefined (" + str(message["stationType"]) + ")"

        if "latitude"       in message: self.latitude       = str(message["latitude"])
        if "longitude"      in message: self.longitude      = str(message["longitude"])
        if "altitude"       in message: self.altitude       = str(message["altitude"]) + " meters"
        if "heading"        in message: self.heading        = str(message["heading"]) + " degrees"
        if "speed"          in message: self.speed          = str(round(message["speed"]/1000*3600, 2)) + " km/h"
        #if "vehicleRole" in message:    self.vehicleRole    = self.vehicleRoles[message["vehicleRole"]]

class MessagePopupCursor(CursorDialog):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def changeParameters(self, info):

        self.title = "Self Information"

        self.stationId  = str(info["stationId"])
        self.latitude   = str(info["lat"]) 
        self.longitude  = str(info["lon"])
        self.altitude   = str(info["alt"])      + " meters"
        self.speed      = str(round(info["speed"]/1000*3600, 2))    + " km/h"
        self.heading    = str(info["heading"])  + " degrees"