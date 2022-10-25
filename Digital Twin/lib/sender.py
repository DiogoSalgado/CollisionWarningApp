from lib.generateMessage import GenerateMessage
import time
import asn1tools
import asyncio

from lib.mqttclient import MQTTClient

class Sender():

    # ISEL Positions
    # pos =   [[387561140, -91164880], [387560740, -91163480], [387560340, -91162110], 
    #         [387559880, -91160740], [387559250, -91158520], [387558750, -91156850], [387558500, -91156450],
    #         [387558110, -91154900], [387557540, -91153290], [387557040, -91151810]]

    # head = [1110,1110]
    
    # House Positions

    information = {
        "pos":[[387564127, -91160546], [387564127, -91160546]],
        "heading":[1200, 1200], # degrees * 10 (120º -> 1200)
        "stationId": 500,         
        "speed": 2000           # cm/s
    }

    pos = []
  
    head = [1200, 1200]

    flag = False

    cam_its = None
    ws_client = None
    mqtt_client = None

    mode = None

    def __init__(self, ws_client, mqtt_client, flag) -> None:
        self.cam_its = asn1tools.compile_files(['files/its.asn', 'files/cam.asn'], 'uper')
        self.ws_client = ws_client
        self.mqtt_client = mqtt_client

        self.mode = flag

        pass

    def run(self):

        index = 0

        while True:
            latitude   = self.information["pos"][index][0]
            longitude  = self.information["pos"][index][1]

            if not self.flag:
                heading = self.information["heading"][0]
                index = index + 1
                if index == len(self.information["pos"]):
                    index = index - 1
                    self.flag = True
        
            else:
                index = index - 1
                heading = self.information["heading"][1]
                if index < 0:
                    index = index + 1
                    self.flag = False

            msg = GenerateMessage(self.cam_its, latitude, longitude, heading, self.information).message()

            if not self.mode:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                loop.run_until_complete(self.ws_client.sendCamMessage(msg))
            else:
                self.mqtt_client.sendMessage(msg, self.information)


            time.sleep(1)