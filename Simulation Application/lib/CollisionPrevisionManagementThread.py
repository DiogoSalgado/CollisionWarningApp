import threading
import time
import copy

# Collision Prevision Algorithm
import lib.CollisionPrevisionAlgorithm as CollisionPrevisionAlgorithm

def main(self_information, neighbors_information):

    while True:
        if not bool(neighbors_information):
            time.sleep(1)
            continue

        # Get neighbors information
        nInformation = copy.deepcopy(neighbors_information)

        # Get self information
        sInformation = copy.deepcopy(self_information)

        # Collision Prevision Thread
        thread = threading.Thread(target=CollisionPrevisionAlgorithm.main, args=(nInformation, sInformation, ), daemon=True)
        thread.start()

        if self_information[1][2] != 0: refresh_rate = 6 / self_information[1][2]   # Refresh_rate with 6meters per iteraction
        else: refresh_rate = 1
        
        #refresh_rate = 5

        time.sleep(5)


