from kivymd.uix.dialog import BaseDialog
from kivy.properties import StringProperty
from kivymd import images_path

from kivy.lang import Builder
from kivymd.theming import ThemableBehavior
from kivy.uix.modalview import ModalView

Builder.load_string(
    """

#:import webbrowser webbrowser
#:import parse urllib.parse
<ThinLabel@MDLabel>:
    size_hint: 1, None
    valign: 'middle'
    height: self.texture_size[1]

<ThinLabelButton@ThinLabel+MDTextButton>:
    size_hint_y: None
    valign: 'middle'
    height: self.texture_size[1]

<ThinBox@BoxLayout>:
    size_hint_y: None
    height: self.minimum_height
    padding: dp(0), dp(0), dp(10), dp(0)
    
<CursorDialog>
    title: root.title        
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(15)
        spacing: dp(10)
        
        # MDFlatButton:
        #     id: button
        #     text: 'Ignore'
        #     halign: 'right'
        #     valign: 'top'
        
        MDLabel:
            id: title
            text: root.title
            font_style: 'H6'
            halign: 'left' if not root.device_ios else 'center'
            valign: 'top'
            size_hint_y: None
            text_size: self.width, None
            height: self.texture_size[1]
    
        ScrollView:
            id: scroll
            size_hint_y: None
            height:
                root.height - (title.height + dp(48)\
                + sep.height)
    
            canvas:
                Rectangle:
                    pos: self.pos
                    size: self.size
                    #source: '{}dialog_in_fade.png'.format(images_path)
                    source: '{}transparent.png'.format(images_path)
    
            MDList:
                id: list_layout
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(15)
                canvas.before:
                    Rectangle:
                        pos: self.pos
                        size: self.size
                    Color:
                        rgba: [1,0,0,.5]   
                ThinBox:
                    ThinLabel:
                        text: "Station Id: "
                    ThinLabelButton:
                        text: root.stationId
                ThinBox:
                    ThinLabel:
                        text: "Latitude: "
                    ThinLabelButton:
                        text: root.latitude
                ThinBox:
                    ThinLabel:
                        text: "Longitude: "
                    ThinLabelButton:
                        text: root.longitude
                ThinBox:
                    ThinLabel:
                        text: "Altitude: "
                    ThinLabelButton:
                        text: root.altitude
                ThinBox:
                    ThinLabel:
                        text: "Heading: "
                    ThinLabelButton:
                        text: root.heading
                ThinBox:
                    ThinLabel:
                        text: "Speed : "
                    ThinLabelButton:
                        text: root.speed
                            
        MDSeparator:
            id: sep

"""
)

class CursorDialog(ThemableBehavior, ModalView):

    title = StringProperty("Missing Data")
    stationId = StringProperty("Missing Data")
    latitude =  StringProperty("Missing Data")
    longitude = StringProperty("Missing Data")
    altitude = StringProperty("Missing Data")
    heading = StringProperty("Missing Data")
    speed = StringProperty("Missing Data")
    background = StringProperty('{}ios_bg_mod.png'.format(images_path))
