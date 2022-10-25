import paho.mqtt.client as mqtt

broker = "192.68.221.36"
port = 1883

class MQTTConnect():

    client = None

    def __init__(self):
        
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        self.client.connect(broker, port)
        self.client.loop_start()
        self.client.subscribe("isel/cam")

    def on_connect(self, client, userdata, flags, rc):
        if rc==0:
            print("Connected to MQTT Broker")
        else:
            print("Bad connection! Returned code:", rc)

    def on_disconnect(self, client, userdata, flags, rc=0):
        print("Disconnected, result code: ", str(rc))
