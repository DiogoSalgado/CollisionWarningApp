from kivy_garden.mapview import MapMarker
from kivy.animation import Animation

from Resources.lib.messagePopup import MessagePopupCursor

# Faz o botao blinkar

class GpsBlinker(MapMarker):

    popup = None
    info = None

    def blink(self):

        # Animation that changes the blink size and opacity
        anim = Animation(outer_opacity=0, blink_size=50)
        anim.bind(on_complete=self.reset)
        anim.start(self)

    # When the animation completes, reset the animation, then repeat
    def reset(self, *args):
        self.outer_opacity = 1
        self.blink_size = self.default_blink_size
        self.blink()

    def show_popup(self):
        if self.popup:
           self.popup.open()
           return 
        
        self.popup = MessagePopupCursor()
        self.popup.changeParameters(self.info)
        self.popup.size_hint = [.7, .43]
        self.popup.open()
    
    def changeParameters(self, info):
        self.info = info

        if self.popup: self.popup.changeParameters(info)

    