import kivy.app
import threading
import asn1tools
import random
import kivy.clock

from kivymd.app         import MDApp
from kivy.core.window   import Window
from kivy.app           import App
from kivy.clock         import Clock
from kivy.utils         import platform

## Screens 
from Resources.views.itsMapView         import ITSMapView

from Resources.lib.gpshelper            import GpsHelper
from Resources.lib.mqttConnect          import MQTTConnect


# CWA Parts
from Resources.CollisionWarning.sendInformation                import SendInformation 
from Resources.CollisionWarning.receiveInformation             import ReceiveInformation

class CollisionWarningApp():
    cam_its = asn1tools.compile_files(['Resources/files/its.asn', 'Resources/files/cam.asn'], 'uper')
    mqtt    = None

    sendInformation     = None
    receiveInformation  = None
    collPrevManagement  = None

    def __init__(self):

        self.sendInformation    = SendInformation()
        self.receiveInformation = ReceiveInformation()

        # GPS Permissions
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION], self.sendInformation.permissionCallback)
            print("Permissions Granted")
        else: print("Platform not android")
        
        pass

    def run(self):

        self.mqtt = MQTTConnect()

        # Random station id generation
        station_id = random.randint(0,4294967295)

        self_information = {"id": station_id, "info": {}}
        neighbors_information = dict()

        # Send Information Part
        taskSend = threading.Thread(target=self.sendInformation.run, args =(self_information, neighbors_information, self.cam_its, self.mqtt, ), daemon=True)
        taskSend.start()

        # Receive Information Part
        taskReceive = threading.Thread(target=self.receiveInformation.run, args=(self_information, neighbors_information, self.cam_its, self.mqtt, ), daemon=True)
        taskReceive.start()

        
class MainApp(MDApp):

    gps_center_btn = None

    def on_start(self):
        # Window.maximize()

        self.theme_cls.primary_palette = 'BlueGray'
        self.theme_cls.primary_hue = "500"
        self.theme_cls.theme_style = "Light"

        # initialize GPS
        GpsHelper().run()

    def on_stop(self):
        kivy.app.stopTouchApp()

    def testFunction(self): return

if __name__ == "__main__":
    CollisionWarningApp().run()
    MainApp().run()
