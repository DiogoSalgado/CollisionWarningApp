import copy 
import time

def main(self_information, neighbors_information, processed_information):
    mac = self_information[0]
    
    while True:

        # print("Neighbors (RT): " + str(neighbors_information) + " | " + str(id(neighbors_information)))
        # print("Processed (RT): " + str(processed_information) + " | " + str(id(processed_information)))
        
        if not bool(processed_information): 
            time.sleep(1)
            continue
        
        # Get Neighbors information

        nInformation = processed_information[mac].copy()

        for key in nInformation:
            neighbors_information[key] = nInformation[key]

        time.sleep(1)
    