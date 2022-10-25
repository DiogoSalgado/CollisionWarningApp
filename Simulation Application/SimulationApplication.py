import threading
import os
import signal

import lib.VehicleThread                    as VehicleThread
import lib.InformationManagementThread      as InformationManagementThread

# Number of vehicles (Number of Vehicle Threads)
th_number = 3

# Information to be exchanged between vehicles
# Structure: vehicles_information   = {"mac_address": [x, y, speed, direction]}
# Structure: processed_information  = {"mac_address": vehicles_information}

vehicles_information    = dict()
processed_information   = dict()
latencyValues = {"0": 1, "1": 2, "2": 3, "3": 4, "4": 5}

if __name__ == "__main__":
    
    try:

        print("Simulation application started. Press Enter to stop...")

        # Information Management Thread initiation
        thread = threading.Thread(target=InformationManagementThread.main, args=(vehicles_information, processed_information, latencyValues, ), daemon=True)
        thread.start()
        
        # Vehicle Threads initiation, based on th_number  
        for index in range(th_number):
            
            thread = threading.Thread(target=VehicleThread.main, args=(str(index), vehicles_information, processed_information, ), daemon=True)
            thread.start()

        input()
    except KeyboardInterrupt:
        input("Application terminated. Press any key to exit...\n")
        os.kill(os.getpid(), signal.SIGTERM)

    