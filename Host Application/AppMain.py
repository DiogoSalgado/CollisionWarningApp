import websockets
import asyncio
import ssl
import json
import paho.mqtt.client as mqtt
import random
import threading
import os

# RSU Information
path = "wss://10.64.10.18:443/xfer"
# path = "wss://10.0.0.1:443/xfer"

# Import Certificates
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.load_cert_chain("Certs\\xfer-pub.crt", "Certs\\xfer.key")
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# MQTT Broker Information (@ISEL)
broker = '192.68.221.36'
port = 1883

topic_cam = "isel/cam"
topic_denm = "isel/denm"

filename = os.path.basename(__file__)
isRunning = True

class WebSocketClient():

    def __init__(self):
        pass

    async def connect(self):
        '''
            Connecting to RSU
        '''
        return await websockets.connect(path, ssl=ssl_context)

    async def sendMessage(self, message):
        '''
            Sending a message to RSU
        '''
        try:
            await ws_connection.send(message)
        except websockets.exceptions.ConnectionClosedError:
            return
            

    async def heartbeat(self):
        '''
        Sending heartbeat to server every 5 seconds
        Ping - pong messages to verify connection is alive
        '''
        while True:
            try:
                await ws_connection.send('''{"echo":"Ping"}''')
                await asyncio.sleep(5) 
            except websockets.exceptions.ConnectionClosedError:
                return
            except Exception as e:
                print('Connection with server closed (Heartbeat): (%s)' % e)
                return
                
    async def receiveMessage(self):
        '''
            Receiving all RSU messages and handling them
        '''
        while True:
            # Message received from RSU 
            try:
                message = await ws_connection.recv()
            except websockets.exceptions.ConnectionClosedError:
                print("Connection Closed, reconnecting...")
                return 

            threading.Thread(target=self.proccessMessage, args=(message,)).start()
            
    def proccessMessage(self, message):
        
        try:
            # # Convert message in JSON
            msg_json = json.loads(message)
            # print(msg_json)
            
            if 'success' in msg_json: return
            elif 'error' in msg_json: print("RSU returned error message: %s" % msg_json['error'])
           
            payload = ""

            # Handle Message
            if 'msg-etsi' in msg_json: 
                payload = msg_json['msg-etsi'][0]["payload"]

            elif 'echo' in msg_json: 
                payload = msg_json["echo"]
                if payload == "Ping": return

            else: return

            msg_type = msg_json['msg-etsi'][0]['btp']['type']

            msg = '''{"stationId": "Host", "payload":"%s"}''' % payload
            
            print("------------------")
            print("Received Message from RSU. Sent via MQTT")

            if msg_type == 'CAM':
                mqtt_connection.publish(topic_cam, msg, qos=0)
            elif msg_type == 'DENM':
                mqtt_connection.publish(topic_denm, msg, qos=0)

        except Exception as e:
            print('Connection with server closed (Receive): (%s)' % e)
            return

class MQTTClient():

    def __init__(self):
        pass
        
    def connect(self):

        client_id = f'python-mqtt-{random.randint(0, 1000)}'

        client = mqtt.Client(client_id)
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.on_disconnect = self.on_disconnect

        client.connect(broker, port)
        client.subscribe(topic_cam)
        client.subscribe(topic_denm)

        return client

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    def on_disconnect(self, client, userdata, rc=0):
        client.loop_stop()

    # Order RSU to send message
    def on_message(self, client, userdata, message):

        #msg = json.loads(message)
        topic = message.topic
        m = message.payload.decode("utf-8")
        message = json.loads(m)

        if message["stationId"] != "Host":
            print("------------------")
            print("Received Message from MQTT. Sent to RSU: " + str(message["stationId"]))
            threading.Thread(target=self.orderToSend, args=(message["payload"],topic, ), daemon=True).start()
        
    def orderToSend(self, message, topic):
        if topic == topic_cam:
            msg = '''{"msg-etsi":[{"payload":"%s","gn":{"scf":false,"offload":false,"lifetime":10000,"transport":"SHB","chan":"CCH","tc":0},"encoding":"UPER","btp":{"type":"CAM"}}],"token":"token1"}''' % message
        elif topic == topic_denm:
            msg = '''{"msg-etsi":[{"payload":"%s","gn":{"scf":false,"offload":false,"lifetime":30000,"transport":"GBC","chan":"CCH","tc":0},"encoding":"UPER","btp":{"type":"DENM"}}],"token":"token2"}''' % message

        #print(msg)
        loop_mqtt = asyncio.new_event_loop()
        asyncio.set_event_loop(loop_mqtt)
        
        loop_mqtt.run_until_complete(ws_client.sendMessage(msg))

if __name__ == '__main__':
    
    while True:
        try:

            choice = input("Forward received(1) or sent(2) messages, or both(3)?: ")

            # Creating Web Socket Client object
            ws_client = WebSocketClient()
            loop = asyncio.get_event_loop()

            # # Connect to RSU
            
            ws_connection = loop.run_until_complete(ws_client.connect())

            if choice=="1": # Upstream (Received)
                loop.run_until_complete(ws_client.sendMessage('''{"subscribe":{"reg-etsi":[{"msg":"ALL"}]}}'''))
            elif choice=="2": # Downstream (Sent)
                loop.run_until_complete(ws_client.sendMessage('''{"subscribe":{"reg-etsi":[{"loop":"ALL"}]}}'''))
            elif choice=="3":
                loop.run_until_complete(ws_client.sendMessage('''{"subscribe":{"reg-etsi":[{"loop":"ALL"}, {"msg":"ALL"}]}}'''))
                # loop.run_until_complete(ws_client.sendMessage('''{"subscribe":{"reg-etsi":[{"msg":"ALL"}]}}'''))
            else: continue

            # Connect to MQTT Broker
            mqtt_client = MQTTClient()

            mqtt_connection = mqtt_client.connect()
            mqtt_connection.loop_start()

            print("Waiting for messages...\n")

            loop.run_until_complete(asyncio.wait([  ws_client.receiveMessage(),
                                                    ws_client.heartbeat()]))

            mqtt_connection.loop_stop()
        except KeyboardInterrupt:
            mqtt_connection.loop_stop()
            input("Application terminated. Press a key to finish...\n")
            os._exit(1)
