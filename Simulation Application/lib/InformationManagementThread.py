import copy
import time
import threading

'''
Para cada veiculo de vehicles_information, aplicar a limitação. Portanto um LOOP para cada veiculo e chamar o
apply limitation em cada um. É melhor criar uma thread para cada veiculo.
'''

def threadExecution(mac, vehicles_information, processed_information, latency):
    last_vehicles_information = dict()
    messages_recv_timestamp = dict()
    while True:
        
        info = copy.deepcopy(vehicles_information)
        info.pop(mac)

        for key in info:
            if(key not in last_vehicles_information):
                messages_recv_timestamp[key] = time.time()*1000.0
            else:
                if(info[key]==last_vehicles_information[key]):
                    passedTime = time.time()*1000.0 - messages_recv_timestamp[key]
                    if(passedTime >= latency * 1000):
                        processed_information[mac][key] = info[key]
                    else: continue
                else:
                    messages_recv_timestamp[key] = time.time()*1000.0
        

        last_vehicles_information = copy.deepcopy(info)


def main(vehicles_information, processed_information, latencyValues):

    vehiclesRunning = list()

    while True:
        # Update information
        for key in vehicles_information:
            if key not in vehiclesRunning:
                vehiclesRunning.append(key)

                processed_information[key] = dict()

                thread = threading.Thread(target=threadExecution, args=(str(key), vehicles_information, processed_information, latencyValues[key], ), daemon=True)
                thread.start()
        
        for vehicle in vehiclesRunning:
            if vehicle not in vehicles_information: vehiclesRunning.pop(vehicle)

        time.sleep(0.01)


######################## Test Function #####################

if __name__ == "__main__":

    vehicles_information = {"0": [10, 10, 50, 0], "1": [10, 10, 50, 0], "2": [10, 10, 50, 0], "3": [10, 10, 50, 0]}
    latencyValues = {"0": 10, "1": 5, "2": 15, "3": 30, "4": 2}
    processed_information = dict()

    main(vehicles_information, processed_information, latencyValues)