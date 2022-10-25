#define _GNU_SOURCE
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>

#include <stdbool.h>
#include <unistd.h>
#include <math.h>
#include <time.h>
#include <sys/stat.h>

#include <netinet/in.h>
#include <sys/socket.h>

#include "error_code_user.h"
#include "poti_caster_service.h"
#include "itsg5_caster_service.h"
#include "itsmsg.h"
#include "itsmsg_codec.h"

#include "../inc/auxFunctions.h"
#include "../inc/collisionPrevisionAlg.h"
#include "../inc/frozen.h"

// Varible containing the application state
bool app_running = true;

// Global variables containig information about the self and neighboring vehicles
vehicleInformation_t *selfInformation;
vehicleInformation_t *neighborsInformation = NULL;
vehicleInformation_t neighbors[50];

// Parameters to be used on Collision Prevision Algorithm thread
algorithmParams_t params;
                

/**
 * @brief   Function to be used in a thread that repeatedly verifies if the neighbo's last message
 *          was received 10 seconds ago
 * @note   
 * @retval None
 */
void *verifyNeighbors(){
    while(getAppRunning()){
        
        time_t current;
        time_t timePassed;

        for(int i = 0; i < 50; i++){

            if(neighborsInformation[i].lastTimestamp == -1) continue;

            current = time(NULL);
            timePassed = current - neighborsInformation[i].lastTimestamp;

            if(timePassed>10){
                printf("Neighbor %d removed!\n", neighborsInformation[i].stationID);
                removeNeighbor(i);
            }
        }

        sleep(1);
    }
}

/**
 * @brief  Function that removes a specific neighbor from the neighbors list
 * 
 * @param  index: Neighbor's index
 * @retval None
 */
void removeNeighbor(int index){
    neighborsInformation[index].stationID   = 0;
    neighborsInformation[index].lat         = 0.0;
    neighborsInformation[index].lon         = 0.0;
    neighborsInformation[index].speed       = 0.0;
    neighborsInformation[index].heading     = 0.0;
    neighborsInformation[index].x_coord     = 0.0;
    neighborsInformation[index].y_coord     = 0.0;
    neighborsInformation[index].lastTimestamp = -1;
}

/**
 * @brief  Global variables creation and initialization
 *  
 * @retval None
 */
void createStorage(){

    selfInformation         = malloc(sizeof(vehicleInformation_t));

    // Variables initialization

    selfInformation->stationID   = 0;
    selfInformation->lat         = 0.0;
    selfInformation->lon         = 0.0;
    selfInformation->speed       = 0.0;
    selfInformation->heading     = 0.0;
    selfInformation->x_coord     = 0.0;
    selfInformation->y_coord     = 0.0;
    selfInformation->lastTimestamp = -1;

    neighborsInformation = neighbors;

    for(int i=0; i<50; i++){

        neighborsInformation[i].stationID   = 0;
        neighborsInformation[i].lat         = 0.0;
        neighborsInformation[i].lon         = 0.0;
        neighborsInformation[i].speed       = 0.0;
        neighborsInformation[i].heading     = 0.0;
        neighborsInformation[i].x_coord     = 0.0;
        neighborsInformation[i].y_coord     = 0.0;
        neighborsInformation[i].lastTimestamp = -1;

    }

    params.sInformation = selfInformation;
    params.nInformation = neighborsInformation;
    
}


/**
 * @brief  Application's state
 * 
 * @retval Returns the application state
 */
bool getAppRunning(){ return app_running; }


/**
 * @brief  Obtain the pointer to the self vehicle's information
 * 
 * @retval Returns the pointer to the SelfInformation variable
 */
vehicleInformation_t *getSelfInformation(){
    return selfInformation;
}


/**
 * @brief  Obtain the pointer to the neighbors' information
 * 
 * @retval Returns the pointer to the NeighborsInformation variable
 */
vehicleInformation_t *getNeighborsInformation(){
    return neighborsInformation;
}


/**
 * @brief   Updates the self vehicle's information.
 *          Run the Collision Prevision Algorithm
 *    
 * @param  *sInformation: Pointer to the new information's
 * @retval None
 */
void setSelfInformation(vehicleInformation_t *sInformation){

    deepCopy_struct(selfInformation, sInformation);

    free(sInformation);

    // Start collision algorithm
    pthread_t tid_algorithm;
    pthread_create(&tid_algorithm, NULL, collisionPrevisionAlgorithm, &params); 
}


/**
 * @brief  Updates the neighbor vehicle's information. If it is a new neighbor, 
 * add to the neighborsInformation variable.
 *   
 * @param  *nInformation: Vehicle's information
 * @retval None
 */
void setNeighborInformation(vehicleInformation_t *nInformation){

    int stationId = nInformation->stationID;
    
    int firstEmpty = -1;
    for(int i=0; i<50; i++){
        
        if(neighborsInformation[i].stationID == stationId){
            deepCopy_struct(&neighborsInformation[i], nInformation);
            free(nInformation);
            return;
        } else if(neighborsInformation[i].stationID == 0 && firstEmpty == -1){
            firstEmpty = i;
        }
    }

    // If it is a new neighbor
    deepCopy_struct(&neighborsInformation[firstEmpty], nInformation);
    free(nInformation);

    // Run the collision algorithm
    pthread_t tid_algorithm;
    pthread_create(&tid_algorithm, NULL, collisionPrevisionAlgorithm, &params);
}


/**
 * @brief Function to calculate the power of a number (y=x^n)
 * 
 * @param x Base number (x).
 * @param n The number of times to multiply the number (n).
 * @return The operation's result
 * 
 * @example x^n=y -> 3^2 = 9
 */
float powerOf(float x, int n){
    float result = x;
    int limit = n;
    if(n<0){ limit = abs(n); }

    for(int i= 1; i<limit;i++){
        result *= x;
    }

    if(n<0){ result = 1/result; }

    return result;
}


/**
 * @brief  Convert degrees in radians
 *   
 * @param  degrees: Value in degrees
 * @retval Returns the value in radians
 */
float radians(float degrees){
    return degrees * (M_PI/180.0);
}


/**
 * @brief  Convert radians in degrees
 *   
 * @param  radians: Value in radians
 * @retval Returns the value in degrees
 */
float degrees(float radians){
    return radians*(180.0/M_PI);
}

/**
 * @brief  Functions responsible for converting the heading orientation:
 * 
 * @param  value: Initial heading value
 * @retval Returns the new heading value
 */
float convertHeading(float value){

    if(value == 0.0)    { return 90.0;  }
    if(value == 90.0)   { return 0.0;   }
    if(value == 180.0)  { return 270.0; }
    if(value == 270.0)  { return 180.0; }

    if(value > 0.0 && value < 90.0){    return f_mod(-value, 90.0); }
    if(value > 270.0 && value < 360.0){ return f_mod(-value, 90.0) + 90.0; }
    if(value > 180.0 && value < 270.0){ return f_mod(-value, 90.0) + 180.0; }
    if(value > 90.0 && value < 180.0){  return f_mod(-value, 90.0) + 270.0; }

    printf("Something went wrong converting the heading value");
    return 0.0;
}

float f_mod(float x, float y){
    float mod = x;
    if(x>0){
        while(mod>y){mod -= y;}
    } else {
        while(mod<0){mod += y;}
    }
    return mod;
}

/**
 * @brief  Deep copy of the vehicleIformation_t struct
 * 
 * @param  *target: Pointer to the target variable
 * @param  *source: Pointer to the source variable
 * @retval None
 */
void deepCopy_struct(vehicleInformation_t *target, vehicleInformation_t *source){
    
    target->stationID   = source->stationID;
    target->lat         = source->lat;
    target->lon         = source->lon;
    target->speed       = source->speed;
    target->heading     = source->heading;

    target->x_coord     = source->x_coord;
    target->y_coord     = source->y_coord;

    target->lastTimestamp = source->lastTimestamp;
}

/**
 * @brief  Handler to an application signal
 * @note   Developed by Unex
 * @param  sig_num: Signal detected
 * @retval None
 */
void app_signal_handler(int sig_num)
{
    if (sig_num == SIGINT) {
        printf("SIGINT signal!\n");
    }
    if (sig_num == SIGTERM) {
        printf("SIGTERM signal!\n");
    }

    app_running = false;
}


/**
 * @brief  Setup the signal handler. This allows the application to gracefully shutdown
 * @note   Developed by Unex
 * @retval None
 */
char app_sigaltstack[SIGSTKSZ];
int app_setup_signals(void)
{
    stack_t sigstack;
    struct sigaction sa;
    int ret = -1;

    sigstack.ss_sp = app_sigaltstack;
    sigstack.ss_size = SIGSTKSZ;
    sigstack.ss_flags = 0;
    if (sigaltstack(&sigstack, NULL) == -1) {
        perror("signalstack()");
        goto END;
    }

    sa.sa_handler = app_signal_handler;
    sa.sa_flags = SA_ONSTACK;
    if (sigaction(SIGINT, &sa, 0) != 0) {
        perror("sigaction()");
        goto END;
    }
    if (sigaction(SIGTERM, &sa, 0) != 0) {
        perror("sigaction()");
        goto END;
    }

    ret = 0;
END:
    return ret;
}
