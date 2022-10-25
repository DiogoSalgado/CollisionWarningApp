from kivy_garden.mapview            import MapMarker
from kivy.app                       import App

from Resources.dialogs.camDialog    import CamDialog
from Resources.lib.messagePopup     import MessagePopupCam

import Resources.lib.auxiliarFunctions as Aux

class MessageMarker(MapMarker):
    type        = None
    message     = []
    popup       = None
    
    def __init__(self, msg_type, message):

        self.type = msg_type
        self.message = message

        if msg_type == "cam":
            sourceImg = Aux.getImage("cam", message)
            self.on_press = self.press_cam


        super().__init__(lat=message["latitude"], lon=message["longitude"], source=sourceImg)
        
    def changeProperties(self, message):

        self.message = message
        self.lat = message["latitude"]
        self.lon = message["longitude"]

        if self.popup:
            self.popup.changeParameters(self.message)

    def press_cam(self):
        if self.popup:
            self.popup.open()
            return

        self.popup = MessagePopupCam()
        self.popup.changeParameters(self.message)
        self.popup.size_hint = [.7, .43]
        self.popup.open()



        