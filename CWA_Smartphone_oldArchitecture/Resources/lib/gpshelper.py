from kivy.app import App
from kivy.utils import platform

from kivymd.uix.button import MDIconButton

from plyer import gps


class GpsHelper(MDIconButton):
    has_centered_map = False
    # my_lat = None
    # my_lon = None
    current_lat = None
    current_lon = None

    def run(self):
        # Get a reference to GpsBlinker, then call blink()
        gps_blinker = App.get_running_app().root.ids.mapview.ids.blinker
        # Start blinking the GpsBlinker
        gps_blinker.blink()
        gps_blinker.on_press = gps_blinker.show_popup

    def update_blinker_position(self, lat, lon):
        my_lat = lat
        my_lon = lon

        self.current_lat = my_lat
        self.current_lon = my_lon

        # Update GpsBlinker position
        gps_blinker = App.get_running_app().root.ids.mapview.ids.blinker
        gps_blinker.lat = my_lat
        gps_blinker.lon = my_lon

        #center map on GPS
        if not self.has_centered_map:
            self.center_with_gps()

    def center_with_gps(self):
        map = App.get_running_app().root.ids.mapview
        map.center_on(self.current_lat, self.current_lon)
        #self.has_centered_map = True
