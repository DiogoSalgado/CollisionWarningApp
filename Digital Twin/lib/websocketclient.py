import websockets
import ssl
import asyncio
import time

class WebSocketClient():

    ssl_context = None
    path = None
    ws_connection = None

    def __init__(self, path):

        # Import Certificates
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.ssl_context.load_cert_chain("certs\\xfer-pub.crt", "certs\\xfer.key")
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        self.path = path

        loop = asyncio.get_event_loop()
        self.ws_connection = loop.run_until_complete(self.connect())

        pass

    async def connect(self):
        '''
            Connecting to RSU
        '''
        return await websockets.connect(self.path, ssl=self.ssl_context)

    async def sendMessage(self, message):
        '''
            Sending a message to RSU
        '''
        try:
            await self.ws_connection.send(message)
        except websockets.exceptions.ConnectionClosedError:
            return
    
    async def sendCamMessage(self, camMessage):
        try:
            message = '''{"msg-etsi":[{"payload":"%s","gn":{"scf":false,"offload":false,"lifetime":10000,"transport":"SHB","chan":"CCH","tc":0},"encoding":"UPER","btp":{"type":"CAM"}}],"token":"token1"}''' % camMessage
            await self.ws_connection.send(message)
        except websockets.exceptions.ConnectionClosedError:
            return

    async def heartbeat(self):
        '''
        Sending heartbeat to server every 5 seconds
        Ping - pong messages to verify connection is alive
        '''
        while True:
            try:
                await self.send('''{"echo":"Ping"}''')
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
                message = await self.ws_connection.recv()
                print(message)
            except websockets.exceptions.ConnectionClosedError:
                print("Connection Closed, reconnecting...")
                return 