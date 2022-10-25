import threading

import lib.SendInformationThread              as SendInformationThread
import lib.ReceiveInformationThread             as ReceiveInformationThread
import lib.CollisionPrevisionManagementThread   as CollisionPrevisionManagementThread


'''
    Thread to be running for each vehicle

'''

def main(mac, vehicles_information, processed_information):
    
    # Array to store the information about this vehicle [mac, [x,y,speed,direction]]
    # self_information
    arr = [mac, []]
    self_information        = list(arr)                   

    # Information available from the neighbors {"mac" : [x,y,speed,direction]}
    # neighbors_informaiton
    neighbors_information   = dict() 

    # Creation of threads

    # Creation of Send Information Thread
    thread = threading.Thread(target=SendInformationThread.main,                args=(self_information, vehicles_information, ), daemon=True)
    thread.start()

    # Creation of Receive Information Thread
    thread = threading.Thread(target=ReceiveInformationThread.main,             args=(self_information, neighbors_information, processed_information, ), daemon=True)
    thread.start()

    # Creation of Collision Prevision Management Thread
    thread = threading.Thread(target=CollisionPrevisionManagementThread.main,   args=(self_information, neighbors_information, ), daemon=True)
    thread.start()

