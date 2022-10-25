from kivy.core.window       import Window
from kivy.app               import App

from kivy.clock             import Clock, mainthread
from kivy.uix.image         import Image

from kivy.uix.popup         import Popup
from kivy.uix.label         import Label

from kivy_garden.mapview    import MapView

from functools              import partial

import time
import math

# Screens
from Resources.lib.messageMarker    import MessageMarker
from Resources.lib.gpshelper        import GpsHelper
import Resources.lib.auxiliarFunctions as Aux

class ITSMapView(MapView):

    alert           = None
    alert2          = None

    alertState      = {"state": False, "warn": ""}
    alertState2     = {"state": False, "warn": ""}

    '''
    cams: {
        key: {  "info": info,
                "time": time,
                "marker": marker
              },
        key: ...
    }
    '''

    cams            = dict()
    
    current_pos     = [0,0]

    popup = None
    popupState = False

    nIterations = 0
    averageLat  = 0


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.alert          = Image(size=(450,450)) # Load the image.
        self.alert2         = Image(size=(450,450), pos=(600,0)) # Load the image.

        self.popup = Popup(title="GPS Error", content=Label(text= "GPS coordinates not found"), 
                size_hint=(None, None), 
                size=(800,500)).open()

        Clock.schedule_interval(self.callbackNeighbors, 0.1)
    

    def callbackNeighbors(self, dt):
        """ Function that updates screen information

        Args:
            dt (_type_): _description_
        """

        for key in self.cams:
            if not self.cams[key]["actFlag"]: continue

            if self.cams[key]["marker"] != None:
                self.remove_widget(self.cams[key]["marker"])

            marker = MessageMarker(msg_type= "cam", message=self.cams[key]["info"])
            self.add_marker(marker)
            self.cams[key]["marker"] = marker
            self.cams[key]["actFlag"] = False
            
    
    # Functions

    def add_neighbor(self, information):
        """Function to add neighbor's information to he screen information

        Args:
            information
        """

        key = information["info"]["stationID"]

        if key in self.cams:
            if self.cams[key]["info"] == information: return
            self.cams[key]["info"] = information["info"]
            self.cams[key]["actFlag"] = True
            self.cams[key]["time"] = information["time"]

        else:
            self.cams[key] = {"info": information["info"], "actFlag": True, "time": information["time"], "marker" : None}

    
    def show_alert(self, recvTime, stationId, dt):
        """Function responsible for showing the alert on screen

        Args:
            recvTime
            stationId
            dt
        """

        if str(stationId) == "1500":
            if not self.alertState2["state"]:
                self.alert2.source = "Resources/img/CollisionWarning.png"
                self.add_widget(self.alert2)

                self.alertState2["state"] = True
                self.alertState2["warn"] = "normal"
            
            latency = time.time()-recvTime
            self.nIterations = self.nIterations+1
            self.averageLat = (self.averageLat*(self.nIterations-1)+latency)/self.nIterations

            print("Processing Average Latency: " + str(self.averageLat))
        
        else:
            if not self.alertState["state"]:
                
                self.alert.source = "Resources/img/CollisionWarning.png"
                self.add_widget(self.alert)

                self.alertState["state"] = True
                self.alertState["warn"] = "normal"
            
            latency = time.time()-recvTime
            self.nIterations = self.nIterations+1
            self.averageLat = (self.averageLat*(self.nIterations-1)+latency)/self.nIterations

            print("Processing Average Latency: " + str(self.averageLat))

    def remove_alert(self, dt):
        """Function responsilbe for removing the screen alert

        Args:
            dt
        """

        if self.alertState["state"]:
            self.remove_widget(self.alert)
            self.alertState["state"] = False

        if self.alertState2["state"]:
            self.remove_widget(self.alert2)
            self.alertState2["state"] = False


    def refresh_cursor(self, longitude, latitude, dt):
        """Function responsible for refreshing the application cursor, based on current location

        Args:
            longitude
            latitude
            dt
        """

        if self.popup != None:
            self.popup.dismiss()
            self.popup = None

        self.current_pos[0] = latitude
        self.current_pos[1] = longitude

        App.get_running_app().root.ids.mapview.ids.gpsbutton.update_blinker_position(longitude, latitude)
