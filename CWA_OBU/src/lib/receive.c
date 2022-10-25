#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
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

// Header Files

#include "../inc/receive.h"
#include "../inc/auxFunctions.h"
#include "../inc/itsmsg_funcs.h"
#include "../inc/frozen.h"

// Pointer to the global variable that stores information about this device
vehicleInformation_t *selfInformation_p;

static bool convertCoordinates(vehicleInformation_t *vehicle);

/**
 * @brief  Function responsible for running the ReceiveInformation part, which is responsible for
 * receiving ITS-G5 CAM messages
 * 
 * @param  *config: Caster configuration used by the device to receive ITS messages
 * @retval None
 */
void *receiveInformation(void *config)
{
    
    uint8_t rx_buf[ITSG5_CASTER_PKT_SIZE_MAX];
    size_t len;
    int ret;
    itsg5_rx_info_t rx_info = {0};
    itsg5_caster_handler_t handler = ITSG5_INVALID_CASTER_HANDLER;

    // Caster creation to message receiving
    ret = itsg5_caster_create(&handler, config);
    if (!IS_SUCCESS(ret)) {
        printf("Cannot link to V2Xcast Service, V2Xcast Service create ret: [%d] %s!\n", ret, ERROR_MSG(ret));
        printf("Please confirm network connection by ping the Unex device then upload a V2Xcast config to create a V2Xcast Service.\n");
        return 0;
    }

    // Obtaining the memory address of the global variable containing self information
    selfInformation_p = getSelfInformation();

    while(getAppRunning()) {

        // Waiting a CAM message
        ret = itsg5_caster_rx(handler, &rx_info, rx_buf, sizeof(rx_buf), &len);
        
        if (IS_SUCCESS(ret)) {
            
            /* Display ITS-G5 RX information */
            // dump_rx_info(&rx_info);

            // Auxiliary variable that stores information about this received message
            vehicleInformation_t *vehicle = malloc(sizeof(vehicleInformation_t));

            // Message decoding
            camDecode(rx_buf, vehicle, (int)len, &rx_info);

            if(vehicle != NULL){

                // Convert geographical coordinates in cartesian system coordinates
                if(convertCoordinates(vehicle)){

                    vehicle->heading = convertHeading(vehicle->heading);

                    printf( "-------------------------------\n"
                            "Message Received from %d!\n"
                            "Lat: %.7f, Lon: %.7f, Speed: %.2f, Heading: %.2f\n"
                            "-------------------------------\n",
                            vehicle->stationID,
                            vehicle->lat,
                            vehicle->lon,
                            vehicle->speed,
                            vehicle->heading);

                    // Update global neighbors' information
                    // Run the algorithm on a different thread
                    setNeighborInformation(vehicle);
                }
            } 

        }
        else {
            printf("Failed to receive data, err code is: [%d] %s\n", ret, ERROR_MSG(ret));
        }
        fflush(stdout); 
    }

    // Caster release
    itsg5_caster_release(handler);
}



/**
 * @brief  Convert geograhical coordinates in a cartesian system coordinates
 *  
 * @param  *vehicle: Vehicle's information to be converted
 * @retval true: in case the convertion were successful; false: if an error occured
 */
static bool convertCoordinates(vehicleInformation_t *vehicle){

    // In case the self vehicle hasn't available information
    if(selfInformation_p->lat == 0.0){ 
        vehicle->x_coord = 0.0;
        vehicle->y_coord = 0.0;
        return false; 
    }

    float lat_e = 0.0;
    float lon_e = 0.0;

    float lat_r = 0.0;
    float lon_r = 0.0;

    lat_e = radians(vehicle->lat);
    lon_e = radians(vehicle->lon);

    lat_r = radians(selfInformation_p->lat); 
    lon_r = radians(selfInformation_p->lon);

    float delta = acos(sin(lat_e)*sin(lat_r) + cos(lat_e)*cos(lat_r)*cos(lon_e-lon_r));

    if(delta==0.0){
        vehicle->x_coord = 0.0;
        vehicle->y_coord = 0.0;
        return false;
    }

    float alpha = acos((sin(lat_e)-sin(lat_r)*cos(delta))/(sin(delta)*cos(lat_r)));
    float alpha_re = 0.0;

    if(lon_r >= lon_e){
        alpha_re = 2 * M_PI - alpha;
    } else {
        alpha_re = alpha;
    }

    float distance = EARTH_RADIUS * delta;
    distance *= 1000;

    alpha_re =  fmod((360.0 - degrees(alpha_re)) + 90.0, 360.0);

    vehicle->x_coord = cos(radians(alpha_re))*distance;
    vehicle->y_coord = sin(radians(alpha_re))*distance;

    return true;
}

/**
 * @brief Decode a CAM message
 * @note  Mainly developed by Unex
 * 
 * @param p_rx_payload      message payload 
 * @param vehicle           variable to be filled with the vehicle's information
 * @param rx_payload_len    message payload's lenght
 * @param p_itsg5_rx_info   message receiving extra information (RSSI)
 */
void camDecode(uint8_t *p_rx_payload, vehicleInformation_t *vehicle, int rx_payload_len, itsg5_rx_info_t *p_itsg5_rx_info)
{
    ITSMsgCodecErr err;
    ItsPduHeader *p_rx_decode_hdr = NULL;
    CAM *p_rx_decode_cam = NULL;
    CAM_V2 *p_rx_decode_cam_v2 = NULL;
    int result;

    /* Allocate a buffer for restoring the decode error information if needed. */
    err.msg_size = 256;
    err.msg = calloc(1, err.msg_size);

    if (err.msg == NULL) {
        printf("Cannot allocate memory for error message buffer.\n");
        return;
    }

    /* Determine and decode the content in RX payload. */
    result = itsmsg_decode(&p_rx_decode_hdr, p_rx_payload, rx_payload_len, &err);

    /* Check whether this is a ITS message. */
    if (result > 0 && p_rx_decode_hdr != NULL) {
        /* Check whether this is a ITS CAM message. */
        if (p_rx_decode_hdr->messageID == CAM_Id) {
            /* Display ITS message version. */
            //printf("ITS msg protocol version: v%d\n", p_rx_decode_hdr->protocolVersion);

            /* Mapping data format base on protocol version. */
            switch (p_rx_decode_hdr->protocolVersion) {
                case 1:
                    /* Convert to version 1 CAM data format. */
                    p_rx_decode_cam = (CAM *)p_rx_decode_hdr;

                    /* Extract other message element, the example only extract contents of newest version Unex supported */
                    printf("[ Received CAM from station %u ]\n", p_rx_decode_cam->header.stationID);
                    break;
                case 2:
                    /* Convert to version 2 CAM data format. */
                    p_rx_decode_cam_v2 = (CAM_V2 *)p_rx_decode_hdr;

                    /* Check CAM msg permission */
                    if (p_itsg5_rx_info->security.status == ITSG5_DECAP_VERIFIED_PKT) {
                        result = cam_check_msg_permission(p_rx_decode_cam_v2, p_itsg5_rx_info->security.ssp, p_itsg5_rx_info->security.ssp_len);
                        printf("Check msg permissions: ");
                        if (IS_SUCCESS(result)) {
                            printf("trustworthy\n");
                        }
                        else {
                            printf("untrustworthy\n");
                        }
                    }

                    vehicle->stationID  = p_rx_decode_cam_v2->header.stationID;
                    vehicle->lat        = p_rx_decode_cam_v2->cam.camParameters.basicContainer.referencePosition.latitude*powerOf(10,-7);
                    vehicle->lon        = p_rx_decode_cam_v2->cam.camParameters.basicContainer.referencePosition.longitude*powerOf(10,-7);

                    vehicle->heading    = p_rx_decode_cam_v2->cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.heading.headingValue/10.0;
                    vehicle->speed      = p_rx_decode_cam_v2->cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.speed.speedValue/100.0;

                    vehicle->lastTimestamp = time(NULL);

                    break;
                default:
                    printf("Received unsupported CAM protocol version: %d\n", p_rx_decode_hdr->protocolVersion);
                    break;
            }
        }
        else {
            printf("Received unrecognized ITS message type: %d\n", p_rx_decode_hdr->messageID);
        }

        /* Release the decode message buffer. */
        itsmsg_free(p_rx_decode_hdr);
    }
    else {
        printf("Unable to decode RX packet: %s\n", err.msg);
    }

    /* Release the allocated error message buffer. */
    free(err.msg);
}
