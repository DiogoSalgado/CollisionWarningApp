import random
import paho.mqtt.client as mqtt
import ssl
import json
import threading

broker = '192.68.221.36'
port = 1883

topic = "isel/cam"

class MQTTClient():

    mqtt_connection = None

    def __init__(self):
        self.mqtt_connection = self.connect()
        pass
        
    def connect(self):

        client_id = f'python-mqtt-{random.randint(0, 1000)}'

        client = mqtt.Client(client_id)
        client.on_connect       = self.on_connect
        client.on_disconnect    = self.on_disconnect

        client.connect(broker, port)
        client.subscribe(topic)

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
        
    def sendMessage(self, message, info):
        try:
            msg = '''{"stationId": "%s", "payload":"%s"}''' % (info["stationId"], message)
            
            print("------------------")
            print("Sent message via MQTT")

            self.mqtt_connection.publish(topic, msg, qos=0)

        except Exception as e:
            print('Connection with server closed (Receive): (%s)' % e)
            return
    
    
    
    # def orderToSend(self, message, topic):
    #     if topic == topic_cam:
    #         msg = '''{"msg-etsi":[{"payload":"%s","gn":{"scf":false,"offload":false,"lifetime":10000,"transport":"SHB","chan":"CCH","tc":0},"encoding":"UPER","btp":{"type":"CAM"}}],"token":"token1"}''' % message
    #     elif topic == topic_denm:
    #         msg = '''{"msg-etsi":[{"payload":"%s","gn":{"scf":false,"offload":false,"lifetime":30000,"transport":"GBC","chan":"CCH","tc":0},"encoding":"UPER","btp":{"type":"DENM"}}],"token":"token2"}''' % message

    #     #print(msg)
    #     loop_mqtt = asyncio.new_event_loop()
    #     asyncio.set_event_loop(loop_mqtt)
        
    #     loop_mqtt.run_until_complete(ws_client.sendMessage(msg))