import time
import threading

from kivy.app           import App

from kivy.utils         import platform
from plyer              import gps
from kivy.clock         import Clock
from functools          import partial
from math               import *

from Resources.CollisionWarning.lib.generateMessage             import GenerateMessage
from Resources.CollisionWarning.lib.collisionPrevisionAlgorithm import CollisionPrevisionAlgorithm


class SendInformation():

    self_information        = None
    neighbors_information   = None
    cam_its                 = None
    mqtt                    = None

    latitude    = 0
    longitude   = 0
    altitude    = 0
    speed       = 0
    heading     = 0
    bearing     = 0

    camMessage = None

    nIteration = 0
    averageLat = 0

    def __init__(self):
        pass

    def run(self, self_information, neighbors_information, cam_its, mqtt):

        self.self_information       = self_information
        self.neighbors_information  = neighbors_information
        self.cam_its                = cam_its
        self.mqtt                   = mqtt

        self.sendInformation()

    
    def sendInformation(self):
        """ Function sending periodic CAM messages, via MQTT
        """
        
        self.self_information["info"]["x_coord"] = 0
        self.self_information["info"]["y_coord"] = 0

        while(self.camMessage == None): time.sleep(1)

        while(True):
            
            t = time.time()
            message = self.generateMessageAdjust(t)

            # message = self.camMessage

            msg = '''{"stationId": "%s", "payload":"%s"}''' % (self.self_information["id"], message)
            self.mqtt.client.publish("isel/cam", msg)

            
            latency = time.time()-t
            self.nIteration = self.nIteration+1
            self.averageLat = (self.averageLat*(self.nIteration-1)+latency)/self.nIteration

            time.sleep(1/10)
    
    
    def permissionCallback(self, permission, results):
        """Function executed when GPS permission is granted

        Args:
            permission: Permissions granted
        """
        if all([res for res in results]):            
            try:
                gps.configure(on_location=self.on_location)
                gps.start(minTime=1000, minDistance=1)
            except NotImplementedError:
                print()

            print ("Got All permissions")
        else:
            print("Did not got all permissions")

    # Function executed when location is obtained
    def on_location(self, **kwargs):
        """
            Function executed when location is obtained
            kwargs: GPS information
        """

        print("On_Location:" + str(kwargs))
        print("Coordinate Adj. Latency: " + str(self.averageLat))

        self.latitude   = kwargs['lat']                 
        self.longitude  = kwargs['lon']
        self.altitude   = round(kwargs['altitude'], 2)  # meters      
        self.speed      = round(kwargs['speed'], 2)     # m/s
        self.bearing    = round(kwargs['bearing'],2)    # north: 0º, east: 90º, south: 180º, west: 270º
        
        # Hard-Coded information

        # self.latitude   = 38.7806045
        # self.longitude  = -9.1606960
        # self.altitude   = 0    
        # self.speed      = 13.90                         # m/s
        # self.bearing    = 0                             # north: 0º, east: 90º, south: 180º, west: 270º

        # Information format changing
        # Heading format changing
        
        if      self.bearing == 0:                              self.heading = 90
        elif    self.bearing == 90:                             self.heading = 0
        elif    self.bearing == 180:                            self.heading = 270
        elif    self.bearing == 270:                            self.heading = 180
        elif    self.bearing > 0      and self.bearing < 90:    self.heading = -self.bearing % 90
        elif    self.bearing > 270    and self.bearing < 360:   self.heading = (-self.bearing % 90) + 90
        elif    self.bearing > 180    and self.bearing < 270:   self.heading = (-self.bearing % 90) + 180
        elif    self.bearing > 90     and self.bearing < 180:   self.heading = (-self.bearing % 90) + 270

        information = {"latitude": self.latitude, "longitude": self.longitude, "speed": self.speed, "heading": self.heading, "bearing": self.bearing}
            
        self.self_information["info"] = information
        self.self_information["time"] = time.time()

        # Run the algorithm

        alg = CollisionPrevisionAlgorithm()

        thread = threading.Thread(target=alg.run, args=(self.self_information, self.neighbors_information, "self", ), daemon=True)
        thread.start()

        # Change screen information

        app = App.get_running_app()
        Clock.schedule_once(partial(app.root.ids.mapview.refresh_cursor, self.latitude, self.longitude))

        info = {"stationId":    self.self_information["id"],
                "lat":          self.latitude,
                "lon":          self.longitude,
                "alt":          self.altitude,
                "speed":        self.speed,
                "heading":      self.heading}

        app.root.ids.mapview.ids.blinker.changeParameters(info)
        
        # Message Generation

        self.generateMessage()


    def generateMessage(self):
        """CAM message generation
        """

        # Fields format
        lat     = int(self.latitude*(10**7))
        lon     = int(self.longitude*(10**7))
        alt     = int(self.altitude / (0.01))
        speed   = int(self.speed*100)
        heading = int(self.bearing*10)

        self.camMessage = GenerateMessage(lat, lon, alt, speed, heading, self.self_information["id"], self.cam_its).run()


    
    def generateMessageAdjust(self, tmstp):
        """ Function that, given the current timestamp, calculates the current position based on last position information

        Args:
            tmstp (number): actual timestamp 

        Returns:
            Encoded CAM message
        """

        t = tmstp - self.self_information["time"]

        if t>1: 
            self.self_information["time"] = tmstp
            return self.camMessage

        
        heading     = radians(self.self_information["info"]["bearing"])

        d = t * self.speed
        
        d = d/1000
        earth_radius = 6371.0


        lat = radians(self.latitude)
        lon = radians(self.longitude)

        lat_r = asin(sin(lat)*cos(d/earth_radius)+cos(lat)*sin(d/earth_radius)*cos(heading))
        lon_r = lon + atan2(sin(heading)*sin(d/earth_radius)*cos(lat), cos(d/earth_radius)-sin(lat)*sin(lat))

        lat_r = degrees(lat_r)
        lon_r = degrees(lon_r)


        lat     = int(lat_r*(10**7))
        lon     = int(lon_r*(10**7))
        alt     = int(self.altitude / (0.01))
        speed   = int(self.speed*100)
        heading = int(self.bearing*10)

        return GenerateMessage(lat, lon, alt, speed, heading, self.self_information["id"], self.cam_its).run()
