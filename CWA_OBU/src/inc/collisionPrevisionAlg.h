#ifndef COLL_AVOID_MNGM_H_
#define COLL_AVOID_MNGM_H_

#include "../inc/auxFunctions.h"

typedef struct safetyZone {
    float A[2];
    float B[2];
    float C[2];
    float D[2];
    float E[2];
} safetyZone_t;

typedef struct vehicle {
    vehicleInformation_t    *information;
    safetyZone_t            *zone;
    float                   distance;
} vehicle_t;

typedef struct algorithmParams {
    vehicleInformation_t *sInformation;
    vehicleInformation_t *nInformation;
} algorithmParams_t;


void* collisionPrevisionAlgorithm(void* params);

#endif