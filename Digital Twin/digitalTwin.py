import asyncio
import threading
import os


from lib.websocketclient    import WebSocketClient
from lib.sender             import Sender
from lib.mqttclient         import MQTTClient

# RSU Information
path = "wss://10.64.10.18:443/xfer"
# path = "wss://10.0.0.1:443/xfer"

isRunning = True

mqtt_client = None
ws_client   = None

if __name__ == '__main__':
  
    while True:
        try:
            
            flag = input("Use MQTT(1) or RSU(2)?: ")
            if flag == "1": flag = True
            else:           flag = False
            
            if not flag:                ws_client   = WebSocketClient(path)
            if flag:                    mqtt_client = MQTTClient()

            messageSender   = Sender(ws_client, mqtt_client, flag)
            t1 = threading.Thread(target = messageSender.run, daemon = True)
            t1.start()

            if not flag:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(ws_client.receiveMessage())

            while(True):
                input()
        except KeyboardInterrupt:
            input("Application terminated. Press a key to finish...\n")
            os._exit(1)
