#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

#include <stdbool.h>
#include <unistd.h>
#include <time.h>
#include <sys/stat.h>
#include <math.h>

#include <netinet/in.h>
#include <sys/socket.h>

#include "error_code_user.h"
#include "poti_caster_service.h"
#include "itsg5_caster_service.h"
#include "itsmsg.h"
#include "itsmsg_codec.h"

#include "../inc/collisionPrevisionAlg.h"
#include "../inc/auxFunctions.h"
#include "../inc/frozen.h"

static bool collisionWarning(vehicle_t *vehicle1, vehicle_t *vehicle2);
static void calculateZone(vehicle_t *vehicle, float *zone_limits);
static void predictMoviment(vehicle_t *vehicle, float rate);

static float getMin_solo(safetyZone_t *vehicle, bool variable);
static float getMin_global(safetyZone_t *vehicle1, safetyZone_t *vehicle2, bool variable);

static float getMax_solo(safetyZone_t *vehicle, bool variable);
static float getMax_global(safetyZone_t *vehicle1, safetyZone_t *vehicle2, bool variable);

// SafetyZone measures ["lf", "le", "wr", "wl"]
float limits[] = {3.0,3.0,1.5,1.5};

/**
 * @brief  Collision Prevision Algorithm
 * @note   
 * @param  args: Self and neighboring information
 * @retval None
 */
void* collisionPrevisionAlgorithm(void* args){
    // printf("Algorithm Running\n");
    algorithmParams_t *params = args;

    vehicle_t *sVehicle_a = malloc(sizeof(vehicle_t));
    vehicle_t *nVehicle_a = malloc(50*sizeof(vehicle_t));
    
    sVehicle_a->information = malloc(sizeof(vehicleInformation_t));
    sVehicle_a->zone        = malloc(sizeof(safetyZone_t));

    deepCopy_struct(sVehicle_a->information, params->sInformation);
    
    int nNumber = 0;
    
    for(int i = 0; i<50; i++){

        if(params->nInformation[i].stationID != 0 && params->nInformation[i].x_coord != 0.0){
            nVehicle_a[nNumber].information = malloc(sizeof(vehicleInformation_t));
            nVehicle_a[nNumber].zone        = malloc(sizeof(safetyZone_t));

            deepCopy_struct(nVehicle_a[nNumber].information, &(params->nInformation[i]));

            nNumber++;
        }
    }
    
    // The algorithm ends if no neighbors have been detected
    if(nNumber == 0){ return NULL; }

    // Algorithm Start

    bool algorithmRunning = true;

    float refresh_rate = -1.0;
    float rate = 0.0;

    // Process self and neighboring information
    // Converting heading from degrees to radians
    // Calculating refresh_rate

    sVehicle_a->information->heading = radians(sVehicle_a->information->heading);

    if(sVehicle_a->information->speed != 0.0){
        refresh_rate = 6/sVehicle_a->information->speed;
    }

    for(int i=0; i<nNumber; i++){

        nVehicle_a[i].information->heading = radians(nVehicle_a[i].information->heading);

        // Initial distance calculation
        nVehicle_a[i].distance = sqrt(powerOf(nVehicle_a[i].information->x_coord - sVehicle_a->information->x_coord,2) + powerOf(nVehicle_a[i].information->y_coord - sVehicle_a->information->y_coord,2));
        nVehicle_a[i].distance = round(nVehicle_a[i].distance*100.0)/100.0;

        if (nVehicle_a[i].information->speed != 0.0){
            rate = 6/nVehicle_a[i].information->speed;

            if(rate<refresh_rate || refresh_rate == -1.0){ refresh_rate = rate; }
        }
    }

    // Considering a maximum TTC - Time To Collision = 7s
    int totalIterations = 7/refresh_rate;
    int nIterations     = 1;
    
    int vNumber = nNumber;

    /*
        ALgorithm's execution flow:

        1 - Get safety zone limits for every vehicle
        2 - Calculate safety zone
        3 - Detect Collisions
        4 - Predict next positions
        5 - Calculate distance between vehicles
    */

    while(algorithmRunning){

        // If all the vehicles have been analyzed or the maximum iterations has been reached
        // The algorithm is terminated
        if(vNumber <= 0 || nIterations == totalIterations){ 
            break;
        }

        // Self vehicle's safety zone calculation
        calculateZone(sVehicle_a, limits);

        // Iteration for each neighboring vehicle
        for(int i = 0; i<nNumber; i++){
            
            // If the distance is set to -1.0 (Meaning that this vehicle's analyze is terminated)
            if(nVehicle_a[i].distance == -1.0){
                continue;
            }

            // Calculate neighbor's safety zone
            calculateZone(&nVehicle_a[i], limits);

            // Detect Collision
            bool warning = collisionWarning(sVehicle_a, &nVehicle_a[i]);

            // In case of collision, terminate the neighbor analyze 
            if(warning){
                printf( "-------------------------------\n"
                        "Collision Detected between %d and %d\n"
                        "-------------------------------\n",
                        sVehicle_a->information->stationID, 
                        nVehicle_a[i].information->stationID);


                nVehicle_a[i].distance = -1.0;
                vNumber--;
            }
        }

        // Self vehicle's movement prediction (Based on refresh rate)
        predictMoviment(sVehicle_a, refresh_rate);

        // For each neighboring vehicle, calculate it's movement 
        // Calculate the distance between vehicle's projections
        for(int i = 0; i<nNumber; i++){

            if(nVehicle_a[i].distance == -1.0){ continue; }

            predictMoviment(&nVehicle_a[i], refresh_rate);
        
            float dst = sqrt(powerOf(nVehicle_a[i].information->x_coord - sVehicle_a->information->x_coord,2) + powerOf(nVehicle_a[i].information->y_coord - sVehicle_a->information->y_coord,2));

            // If the distance is getting higher, the analyze ends
            if(nVehicle_a[i].distance <= dst){
                
                nVehicle_a[i].distance = -1.0;
                vNumber--;
            } else {
                nVehicle_a[i].distance = dst;
            }
        }

        nIterations++;
    }

    // Free Variables

    for(int i=0; i<nNumber; i++){
        free(nVehicle_a[i].information);
        free(nVehicle_a[i].zone);
    }

    free(sVehicle_a->information);
    free(sVehicle_a->zone);
    free(sVehicle_a);
    free(nVehicle_a);

    return NULL;
}

/**
 * @brief Calculate safety zone limits
 * 
 * @param vehicle: vehicle's information
 * @param zone_limits: Safety zone size ["lf", "le", "wr", "wl"]
 */
static void calculateZone(vehicle_t *vehicle, float *limits){
    
    vehicle->zone->A[0] = vehicle->information->x_coord;
    vehicle->zone->A[1] = vehicle->information->y_coord;

    vehicle->zone->B[0] = vehicle->zone->A[0] + limits[0] * cos(vehicle->information->heading) - limits[3] * sin(vehicle->information->heading);  // Bx = Ax + Lf cos(0) - Wl sin(0)
    vehicle->zone->B[1] = vehicle->zone->A[1] + limits[0] * sin(vehicle->information->heading) + limits[3] * cos(vehicle->information->heading);  // By = Ay + Lf sin(0) + Wl cos(0)

    vehicle->zone->C[0] = vehicle->zone->A[0] + limits[0] * cos(vehicle->information->heading) + limits[2] * sin(vehicle->information->heading);  // Cx = Ax + Lf cos(0) + Wr sin(0)
    vehicle->zone->C[1] = vehicle->zone->A[1] + limits[0] * sin(vehicle->information->heading) - limits[3] * cos(vehicle->information->heading); // Cy = Ay + Lf sin(0) - Wl cos(0)

    vehicle->zone->D[0] = vehicle->zone->A[0] - limits[1] * cos(vehicle->information->heading) + limits[2] * sin(vehicle->information->heading);  // Dx = Ax - Le cos(0) + Wr sin(0)
    vehicle->zone->D[1] = vehicle->zone->A[1] - limits[1] * sin(vehicle->information->heading) - limits[2] * cos(vehicle->information->heading);  // Dy = Ay - Le sin(0) - Wr cos(0)
                    
    vehicle->zone->E[0] = vehicle->zone->A[0] - limits[1] * cos(vehicle->information->heading) - limits[3] * sin(vehicle->information->heading);  // Ex = Ax - Le cos(0) - Wl sin(0)
    vehicle->zone->E[1] = vehicle->zone->A[1] - limits[1] * sin(vehicle->information->heading) + limits[2] * cos(vehicle->information->heading);  // Ey = Ay - Le sin(0) + Wr cos(0)         

}

/**
 * @brief  Movement prediction
 * @note   
 * @param  *vehicle: Vehicle's information
 * @param  rate: Refresh rate
 * @retval None
 */
static void predictMoviment(vehicle_t *vehicle, float rate){
    vehicle->information->x_coord   = vehicle->information->x_coord + vehicle->information->speed * cos(vehicle->information->heading) * rate;
    vehicle->information->y_coord   = vehicle->information->y_coord + vehicle->information->speed * sin(vehicle->information->heading) * rate;
}

/**
 * @brief  Collision situation analyze
 * @note   
 * @param  *vehicle1: Vehicle 1 information
 * @param  *vehicle2: Vehicle 2 information
 * @retval Collision warning situation (True: yes, False: no)
 */
static bool collisionWarning(vehicle_t *vehicle1, vehicle_t *vehicle2){

    float l1x = getMax_solo(vehicle1->zone, true)   - getMin_solo(vehicle1->zone, true);
    float l1y = getMax_solo(vehicle1->zone, false)  - getMin_solo(vehicle1->zone, false);
    float l2x = getMax_solo(vehicle2->zone, true)   - getMin_solo(vehicle2->zone, true);
    float l2y = getMax_solo(vehicle2->zone, false)  - getMin_solo(vehicle2->zone, false);

    float lx = fabs(getMax_global(vehicle1->zone, vehicle2->zone, true) - getMin_global(vehicle1->zone, vehicle2->zone, true));
    float ly = fabs(getMax_global(vehicle1->zone, vehicle2->zone, false) - getMin_global(vehicle1->zone, vehicle2->zone, false));

    float sx = lx - (l1x + l2x);
    float sy = ly - (l1y + l2y);

    if(sx > 0.0 || sy > 0.0){     return false;
    } else {                      return true; }
}

/**
 * @brief  Calculate the max value among the X or Y values of one vehicle
 * @note   
 * @param  *vehicle: Vehicle's information
 * @param  variable: flag to analyze x or y variables
 * @retval Return the max value
 */
static float getMax_solo(safetyZone_t *vehicle, bool variable){
    
    float max = 0.0;

    if(variable){
        max = vehicle->B[0];
        if      (vehicle->C[0] > max) max = vehicle->C[0];
        else if (vehicle->D[0] > max) max = vehicle->D[0];
        else if (vehicle->E[0] > max) max = vehicle->E[0];
    } else {
        max = vehicle->B[1];
        if      (vehicle->C[1] > max) max = vehicle->C[1];
        else if (vehicle->D[1] > max) max = vehicle->D[1];
        else if (vehicle->E[1] > max) max = vehicle->E[1];
    }

    return max;
}

/**
 * @brief  Calculate the min value among the X or Y values of one vehicle
 * @note   
 * @param  *vehicle: Vehicle's information
 * @param  variable: flag to analyze x or y variables
 * @retval Return the min value
 */
static float getMin_solo(safetyZone_t *vehicle, bool variable){
    
    float min = 0.0;

    if(variable){
        min = vehicle->B[0];
        if      (vehicle->C[0] < min) min = vehicle->C[0];
        else if (vehicle->D[0] < min) min = vehicle->D[0];
        else if (vehicle->E[0] < min) min = vehicle->E[0];
    } else {
        min = vehicle->B[1];
        if      (vehicle->C[1] < min) min = vehicle->C[1];
        else if (vehicle->D[1] < min) min = vehicle->D[1];
        else if (vehicle->E[1] < min) min = vehicle->E[1];
    }

    return min;
}

/**
 * @brief  Calculate the max value among the X or Y values of two vehicles
 * @note   
 * @param  *vehicle1: vehicle 1 information
 * @param  *vehicle2: vehicle 2 information
 * @param  variable:  flag to analyze x or y variables
 * @retval Returns the max value
 */
static float getMax_global(safetyZone_t *vehicle1, safetyZone_t *vehicle2, bool variable){
    float max_1 = getMax_solo(vehicle1, variable);
    float max_2 = getMax_solo(vehicle2, variable);
    
    if(max_1 > max_2){
        return max_1;
    } else {
        return max_2;
    }
}

/**
 * @brief  Calculate the min value among the X or Y values of two vehicles
 * @note   
 * @param  *vehicle1: vehicle 1 information
 * @param  *vehicle2: vehicle 2 information
 * @param  variable:  flag to analyze x or y variables
 * @retval Returns the min value
 */
static float getMin_global(safetyZone_t *vehicle1, safetyZone_t *vehicle2, bool variable){

    float min_1 = getMin_solo(vehicle1, variable);
    float min_2 = getMin_solo(vehicle2, variable);

    if(min_1 < min_2){
        return min_1;
    } else {
        return min_2;
    }
}
