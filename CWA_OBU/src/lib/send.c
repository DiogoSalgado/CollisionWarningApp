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

// Header files

#include "../inc/send.h"
#include "../inc/auxFunctions.h"
#include "../inc/itsmsg_funcs.h"
#include "../inc/frozen.h"

// File containing the hardcoded information, in case it is necessary
station_config_t station_config;

/**
 * @brief  Function responsible for running the sendInformation part, which is 
 * responsible for sending CAM messages
 *   
 * @param  *config: Caster configuration used by the device to send ITS messages
 * @retval None
 */
void sendInformation(itsg5_caster_comm_config_t *config)
{
    uint8_t *tx_buf = NULL;
    int tx_buf_len = 0;
    int ret;
    poti_fix_data_t         fix_data        = {0};
    poti_gnss_info_t        gnss_info       = {0};
    itsg5_tx_info_t         tx_info         = {0}; 
    itsg5_caster_handler_t  handler         = ITSG5_INVALID_CASTER_HANDLER;
    poti_handler_t          poti_handler    = POTI_INVALID_CASTER_HANDLER;

    // Caster creation to message sending
    ret = itsg5_caster_create(&handler, config);
    if (!IS_SUCCESS(ret)) {
        printf("Cannot link to V2Xcast Service, V2Xcast Service create ret: [%d] %s!\n", ret, ERROR_MSG(ret));
        printf("Please confirm network connection by ping the Unex device then upload a V2Xcast config to create a V2Xcast Service.\n");
        return;
    }

    // Create an instance of a POTI caster 
    poti_comm_config_t poti_config = {.ip = config->ip};
    ret = poti_caster_create(&poti_handler, &poti_config);
    if (!IS_SUCCESS(ret)) {
        printf("Fail to create POTI caster, ret:%d!\n", ret);
        return;
    }

    /* Load station setting from configuration file */
    ret = load_station_config(&station_config);
    if (-1 == ret) {
        printf("Using fixed CAM data.\n");
    }

    while (getAppRunning()) {

        // Obtaining the GPS information
        ret = poti_caster_fix_data_rx(poti_handler, &fix_data);

        if (ret != 0) {
            printf( "-------------------------------\n"
                    "Fail to receive GNSS fix data from POTI caster service, %d\n"
                    "-------------------------------\n", ret);

            /* Waiting for POTI caster service startup */
            usleep(1000000);
            continue;
        }

        ret = poti_caster_gnss_info_get(poti_handler, &gnss_info);
        if (!IS_SUCCESS(ret)) {
            printf("Something went wrong while obtaining GNSS information\n");
        }

        // Auxiliary variable that contains the information used by this loop iteration
        vehicleInformation_t *vInformation = malloc(sizeof(vehicleInformation_t));

        // Message encoding. vInformation variable is updated inside this function
        camEncode(&tx_buf, vInformation, &tx_buf_len, &fix_data);

        if (tx_buf != NULL) {
            
            // Set the transmission information
            set_tx_info(&tx_info, 0);

            // CAM sending using ITS-G5
            ret = itsg5_caster_tx(handler, &tx_info, tx_buf, (size_t)tx_buf_len);
            if (!IS_SUCCESS(ret)) {
                printf("Failed to transmit data, err code is: [%d] %s\n", ret, ERROR_MSG(ret));
            } else{

                vInformation->heading = convertHeading(vInformation->heading);

                printf( "-------------------------------\n"
                        "Message Transmitted, StationID: %d!\n"
                        "Lat: %.7f, Lon: %.7f, Speed: %.2f, Heading: %.2f\n"
                        "-------------------------------\n",
                        vInformation->stationID,
                        vInformation->lat,
                        vInformation->lon,
                        vInformation->speed,
                        vInformation->heading);

            }

            itsmsg_buf_free(tx_buf);
            
            // Update the global variable's value, to be used by the algorithm
            // Runs the algorithm on a different thread
            setSelfInformation(vInformation);
        }

        // flush the standard output
        fflush(stdout);

        // Varies according to the CAM generation frequency
        sleep(1);
    }

    // Casters release
    itsg5_caster_release(handler);
    poti_caster_release(poti_handler);
}

/**
 * @brief   Encode the CAM message
 * @note    Mainly developed by Unex
 * 
 * @param tx_buf        Output of encoded message
 * @param vInformation  Variable to be filled with GNSS information
 * @param tx_buf_len    Output lenght
 * @param p_fix_data    GNSS information
 */
void camEncode(uint8_t **tx_buf, vehicleInformation_t *vInformation, int *tx_buf_len, poti_fix_data_t *p_fix_data)
{
    ITSMsgCodecErr err;
    CAM_V2 cam_tx_encode_fmt;
    int ret = 0;

    /* Make sure we reset the data structure at least once. */
    memset((void *)&cam_tx_encode_fmt, 0, sizeof(cam_tx_encode_fmt));

    /* For the present document, the value of the DE protocolVersion shall be set to 1.  */
    cam_tx_encode_fmt.header.protocolVersion = CAM_PROTOCOL_VERSION;
    cam_tx_encode_fmt.header.messageID = CAM_Id;
    if (0 == ret) {
        /* Set stationID form station config file */
        cam_tx_encode_fmt.header.stationID = station_config.stationID;
    }
    else {
        /* Set fixed stationID*/
        cam_tx_encode_fmt.header.stationID = CAM_STATION_ID_DEF;
    }

    /*
     * Time corresponding to the time of the reference position in the CAM, considered
     * as time of the CAM generation.
     * The value of the DE shall be wrapped to 65 536. This value shall be set as the
     * remainder of the corresponding value of TimestampIts divided by 65 536 as below:
     *      generationDeltaTime = TimestampIts mod 65 536
     * TimestampIts represents an integer value in milliseconds since 2004-01-01T00:00:00:000Z
     * as defined in ETSI TS 102 894-2 [2].
     */
    //cam_tx_encode_fmt.cam.generationDeltaTime = (int32_t) tx_counter % 1000;
    cam_tx_encode_fmt.cam.generationDeltaTime = (int32_t)fmod(p_fix_data->time.tai_since_2004 * 1000.0, 65536); /* TAI milliseconds since 2004-01-01 00:00:00.000 UTC. */

    /*
	 * Position and position accuracy measured at the reference point of the originating
	 * ITS-S. The measurement time shall correspond to generationDeltaTime.
	 * If the station type of the originating ITS-S is set to one out of the values 3 to 11
	 * the reference point shall be the ground position of the centre of the front side of
	 * the bounding box of the vehicle.
	 * The positionConfidenceEllipse provides the accuracy of the measured position
	 * with the 95 % confidence level. Otherwise, the positionConfidenceEllipse shall be
	 * set to unavailable.
	 * If semiMajorOrientation is set to 0 degree North, then the semiMajorConfidence
	 * corresponds to the position accuracy in the North/South direction, while the
	 * semiMinorConfidence corresponds to the position accuracy in the East/West
	 * direction. This definition implies that the semiMajorConfidence might be smaller
	 * than the semiMinorConfidence.
	 */
    cam_tx_encode_fmt.cam.camParameters.basicContainer.stationType = CAM_STATION_TYPE_DEF;
    cam_tx_encode_fmt.cam.camParameters.basicContainer.referencePosition.latitude = (int32_t)(p_fix_data->latitude * 10000000.0); /* Convert to 1/10 micro degree. */
    cam_tx_encode_fmt.cam.camParameters.basicContainer.referencePosition.longitude = (int32_t)(p_fix_data->longitude * 10000000.0); /* Convert to 1/10 micro degree. */
    cam_tx_encode_fmt.cam.camParameters.basicContainer.referencePosition.altitude.altitudeValue = (int32_t)(p_fix_data->altitude * 100.0);
    cam_tx_encode_fmt.cam.camParameters.basicContainer.referencePosition.positionConfidenceEllipse.semiMajorConfidence = cam_set_semi_axis_length(p_fix_data->err_smajor_axis); /* Convert to centimetre. */
    cam_tx_encode_fmt.cam.camParameters.basicContainer.referencePosition.positionConfidenceEllipse.semiMinorConfidence = cam_set_semi_axis_length(p_fix_data->err_sminor_axis); /* Convert to centimetre. */
    cam_tx_encode_fmt.cam.camParameters.basicContainer.referencePosition.positionConfidenceEllipse.semiMajorOrientation = cam_set_heading_value(p_fix_data->err_smajor_orientation);
    cam_tx_encode_fmt.cam.camParameters.basicContainer.referencePosition.altitude.altitudeConfidence = cam_set_altitude_confidence(p_fix_data->err_altitude);
    cam_tx_encode_fmt.cam.camParameters.basicContainer.referencePosition.altitude.altitudeValue = (int32_t)(p_fix_data->altitude * 100.0);
    /*
     * The mandatory high frequency container of CAM.
     */

    /* Heading. */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.heading.headingValue = (int32_t)(p_fix_data->course_over_ground * 10.0); /* Convert to 0.1 degree from North. */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.heading.headingConfidence = cam_set_heading_confidence(p_fix_data->err_course_over_ground); /* Convert to 1 ~ 127 enumeration. */

    /* Speed, 0.01 m/s */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.speed.speedValue = (int16_t)(p_fix_data->horizontal_speed * 100.0); /* Convert to 0.01 metre per second. */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.speed.speedConfidence = cam_set_speed_confidence(p_fix_data->err_horizontal_speed);

    /* Direction. */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.driveDirection = CAM_SENSOR_GET_DRIVE_DIRECTION();

    /* Vehicle length, 0.1 metre  */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.vehicleLength.vehicleLengthValue = CAM_SENSOR_GET_VEHICLE_LENGTH_VALUE();
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.vehicleLength.vehicleLengthConfidenceIndication = CAM_SENSOR_GET_VEHICLE_LENGTH_CONF();

    /* Vehicle width, 0.1 metre */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.vehicleWidth = CAM_SENSOR_GET_VEGICLE_WIDTH_VALUE();

    /* Longitudinal acceleration, 0.1 m/s^2 */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.longitudinalAcceleration.longitudinalAccelerationValue = CAM_SENSOR_GET_LONG_ACCEL_VALUE();
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.longitudinalAcceleration.longitudinalAccelerationConfidence = CAM_SENSOR_GET_LONG_ACCEL_CONF();

    /*
     * Curvature value, 1 over 30000 meters, (-30000 .. 30001)
     * The confidence value shall be set to:
     *      0 if the accuracy is less than or equal to 0,00002 m-1
     *      1 if the accuracy is less than or equal to 0,0001 m-1
     *      2 if the accuracy is less than or equal to 0,0005 m-1
     *      3 if the accuracy is less than or equal to 0,002 m-1
     *      4 if the accuracy is less than or equal to 0,01 m-1
     *      5 if the accuracy is less than or equal to 0,1 m-1
     *      6 if the accuracy is out of range, i.e. greater than 0,1 m-1
     *      7 if the information is not available
     */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.curvature.curvatureValue = CAM_SENSOR_GET_CURVATURE_VALUE();
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.curvature.curvatureConfidence = CAM_SENSOR_GET_CURVATURE_CONF();
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.curvatureCalculationMode = CAM_SENSOR_GET_CURVATURE_CONF_CAL_MODE();

    /* YAW rate, 0,01 degree per second. */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.yawRate.yawRateValue = CAM_SENSOR_GET_YAW_RATE_VALUE();
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.yawRate.yawRateConfidence = CAM_SENSOR_GET_YAW_RATE_CONF();

    /* Optional fields, disable all by default. */
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.accelerationControl_option = FALSE;
    //cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.accelerationControl =
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.lanePosition_option = FALSE;
    //cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.lanePosition =
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.steeringWheelAngle_option = FALSE;
    //cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.steeringWheelAngle =
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.lateralAcceleration_option = FALSE;
    //cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.lateralAcceleration =
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.verticalAcceleration_option = FALSE;
    //cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.verticalAcceleration =
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.performanceClass_option = FALSE;
    //cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.performanceClass =
    cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.cenDsrcTollingZone_option = FALSE;
    //cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.cenDsrcTollingZone =


    /*
    *   If stationType is set to specialVehicles(10)
    *       LowFrequencyContainer shall be set to BasicVehicleContainerLowFrequency
    *       SpecialVehicleContainer shall be set to EmergencyContainer
    */
    if (cam_tx_encode_fmt.cam.camParameters.basicContainer.stationType == ITS_STATION_SPECIAL_VEHICLE) {
        /*
        * The optional low frequency container of CAM.
        *      vehicleRole: emergency(6)
        *      exteriorLights: select highBeamHeadlightsOn (1)
        *           lowBeamHeadlightsOn (0),
        *           highBeamHeadlightsOn (1),
        *           leftTurnSignalOn (2),
        *           rightTurnSignalOn (3),
        *           daytimeRunningLightsOn (4),
        *           reverseLightOn (5),
        *           fogLightOn (6),
        *           parkingLightsOn (7)
        *      pathHistory: set zero historical path points
        */
        cam_tx_encode_fmt.cam.camParameters.lowFrequencyContainer_option = true;
        if (0 == ret) {
            /* Set vehicleRole form station config file */
            cam_tx_encode_fmt.cam.camParameters.lowFrequencyContainer.u.basicVehicleContainerLowFrequency.vehicleRole = station_config.role;
        }
        else {
            /* Set fixed vehicleRole*/
            cam_tx_encode_fmt.cam.camParameters.lowFrequencyContainer.u.basicVehicleContainerLowFrequency.vehicleRole = VehicleRole_emergency;
        }

        /* alloc and set the bit of bitstring */
        asn1_bstr_alloc_set_bit(&(cam_tx_encode_fmt.cam.camParameters.lowFrequencyContainer.u.basicVehicleContainerLowFrequency.exteriorLights), ExteriorLights_MAX_BITS_ITS, ExteriorLights_highBeamHeadlightsOn_ITS);

        /* Set exteriorLights form station config file */
        if (station_config.leftTurnSignalOn) {
            asn1_bstr_set_bit(&(cam_tx_encode_fmt.cam.camParameters.lowFrequencyContainer.u.basicVehicleContainerLowFrequency.exteriorLights), ExteriorLights_leftTurnSignalOn_ITS);
        }
        if (station_config.rightTurnSignalOn) {
            asn1_bstr_set_bit(&(cam_tx_encode_fmt.cam.camParameters.lowFrequencyContainer.u.basicVehicleContainerLowFrequency.exteriorLights), ExteriorLights_rightTurnSignalOn_ITS);
        }

        cam_tx_encode_fmt.cam.camParameters.lowFrequencyContainer.u.basicVehicleContainerLowFrequency.pathHistory.count = 0;

        /*
        * The optional special vehicle container of CAM.
        *       lightBarSirenInUse: select sirenActivated (1)
        *           lightBarActivated (0)
        *           sirenActivated (1)
        *       emergencyPriority: enable , select requestForFreeCrossingAtATrafficLight (1)
        *           requestForRightOfWay (0)
        *           requestForFreeCrossingAtATrafficLight (1)
        *       causeCode/subCauseCode: disable
        */
        cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer_option = true;

        switch (cam_tx_encode_fmt.cam.camParameters.lowFrequencyContainer.u.basicVehicleContainerLowFrequency.vehicleRole) {
            case VehicleRole_emergency:
                cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.choice = SpecialVehicleContainer_emergencyContainer;
                /* Set lightBarSirenInUse from station config file */
                asn1_bstr_alloc(&(cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.lightBarSirenInUse), LightBarSirenInUse_MAX_BITS);
                if (station_config.lightBarInUse) {
                    asn1_bstr_set_bit(&(cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.lightBarSirenInUse), LightBarSirenInUse_lightBarActivated);
                }

                if (station_config.sirenInUse) {
                    asn1_bstr_set_bit(&(cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.lightBarSirenInUse), LightBarSirenInUse_sirenActivated);
                }

                cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.emergencyPriority_option = true;
                asn1_bstr_alloc_set_bit(&(cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.emergencyPriority), EmergencyPriority_MAX_BITS, EmergencyPriority_requestForFreeCrossingAtATrafficLight);

                /* Set incidentIndication from station config file */
                if (-1 == station_config.causeCode) {
                    cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.incidentIndication_option = false;
                }
                else {
                    cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.incidentIndication_option = true;
                    cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.incidentIndication.causeCode = station_config.causeCode;
                    cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.incidentIndication.subCauseCode = 0;
                }
                break;
            default:
                /* Please follow the ETSI EN 302 637-2 mapping special vehicle container according to the vehicle role */
                break;
        }
    }


    /* Allocate a buffer for restoring the decode error information if needed. */
    err.msg_size = 512;
    err.msg = calloc(1, err.msg_size);

    

    if (err.msg == NULL) {
        printf("Cannot allocate memory for error message buffer.\n");
    } else {

        /* Encode the CAM message. */
        *tx_buf_len = itsmsg_encode(tx_buf, (ItsPduHeader *)&cam_tx_encode_fmt, &err);

        if (*tx_buf_len <= 0) {
            printf("itsmsg_encode error: %s\n", err.msg);
        }

        // Vehicle information update
        
        vInformation->stationID = cam_tx_encode_fmt.header.stationID;
        
        vInformation->lat   = cam_tx_encode_fmt.cam.camParameters.basicContainer.referencePosition.latitude*powerOf(10,-7);
        vInformation->lon   = cam_tx_encode_fmt.cam.camParameters.basicContainer.referencePosition.longitude*powerOf(10,-7);

        vInformation->heading   = cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.heading.headingValue/10.0;
        vInformation->speed     = cam_tx_encode_fmt.cam.camParameters.highFrequencyContainer.u.basicVehicleContainerHighFrequency.speed.speedValue/100.0;

        vInformation->x_coord   = 0.0;
        vInformation->y_coord   = 0.0;

        vInformation->lastTimestamp = time(NULL);

        /* Release the allocated error message buffer. */
        free(err.msg);
    }

    // Change self information
    // setSelfInformation(latitude, longitude, speed, direction);

    if (cam_tx_encode_fmt.cam.camParameters.basicContainer.stationType == ITS_STATION_SPECIAL_VEHICLE) {
        /* free the memory for encoding */
        asn1_bstr_free(&(cam_tx_encode_fmt.cam.camParameters.lowFrequencyContainer.u.basicVehicleContainerLowFrequency.exteriorLights));
        asn1_bstr_free(&(cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.lightBarSirenInUse));
        asn1_bstr_free(&(cam_tx_encode_fmt.cam.camParameters.specialVehicleContainer.u.emergencyContainer.emergencyPriority));
    }

    return;
}
