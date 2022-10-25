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
#include "../inc/itsmsg_funcs.h"
#include "../inc/frozen.h"

/**
 * @brief  Unex functions that are used by the applications to auxiliate tasks like CAM encoding 
 * and decoding
 * @note   Mainly developed by Unex
 */

int cam_check_msg_permission(CAM_V2 *p_cam_msg, uint8_t *p_ssp, uint8_t ssp_len)
{
    int rc = 0, fbs;

    if (ssp_len < CAM_SSP_LEN) {
        rc = -1;
        printf("Err: SSP length[%d] is not enough\n", ssp_len);
        goto FAILURE;
    }

    if (p_cam_msg->cam.camParameters.specialVehicleContainer_option) {
        /*
        *   For example, only check emergencyContainer
        *   Please refer to ETSI EN 302 637-2 to check related SSP item
        */
        switch (p_cam_msg->cam.camParameters.specialVehicleContainer.choice) {
            case SpecialVehicleContainer_emergencyContainer:
                if (!IS_CAM_SSP_VALID(EMERGENCY, p_ssp[1])) {
                    printf("Err: certificate not allowed to sign EMERGENCY\n");
                    rc = -1;
                    goto FAILURE;
                }

                if (p_cam_msg->cam.camParameters.specialVehicleContainer.u.emergencyContainer.emergencyPriority_option) {
                    fbs = asn1_bstr_ffs(&(p_cam_msg->cam.camParameters.specialVehicleContainer.u.emergencyContainer.emergencyPriority));
                    switch (fbs) {
                        case EmergencyPriority_requestForRightOfWay:
                            if (!IS_CAM_SSP_VALID(REQUEST_FOR_RIGHT_OF_WAY, p_ssp[2])) {
                                printf("Err: certificate not allowed to sign REQUEST_FOR_RIGHT_OF_WAY\n");
                                rc = -1;
                                goto FAILURE;
                            }
                            break;
                        case EmergencyPriority_requestForFreeCrossingAtATrafficLight:
                            if (!IS_CAM_SSP_VALID(REQUEST_FOR_FREE_CROSSING_AT_A_TRAFFIC_LIGHT, p_ssp[2])) {
                                printf("Err: certificate not allowed to sign REQUEST_FOR_FREE_CROSSING_AT_A_TRAFFIC_LIGHT\n");
                                rc = -1;
                                goto FAILURE;
                            }
                            break;
                    }
                }
                break;
            default:
                // nothing
                break;
        }
    }

FAILURE:
    return rc;
}

void dump_rx_info(itsg5_rx_info_t *rx_info)
{
    struct tm *timeinfo;
    char buffer[80];
    time_t t;

    t = rx_info->timestamp.tv_sec;
    timeinfo = localtime(&t);
    strftime(buffer, 80, "%Y%m%d%H%M%S", timeinfo);
    printf("timestamp:%s\n", buffer);
    printf("rssi:%hd\n", rx_info->rssi);
    printf("data rate:%hu\n", rx_info->data_rate);
    printf("remain hop:%hu\n", rx_info->remain_hop_limit);
    printf("decap status:%d\n", rx_info->security.status);
    switch (rx_info->security.status) {
        case ITSG5_DECAP_VERIFIED_PKT:
            printf("\tSecurity status: this packet is verified\n");
            printf("\tITS-AID: %u\n", rx_info->security.its_aid);
            printf("\tssp_len = %hu\n", rx_info->security.ssp_len);
            for (uint8_t i = 0; i < rx_info->security.ssp_len; i++) {
                printf("\tssp[%hu]=%hu\n", i, rx_info->security.ssp[i]);
            }
            break;
        case ITSG5_DECAP_UNVERIFIABLE_PKT:
            printf("\tSecurity status:  this packet is untrustworthy\n");
            break;
        case ITSG5_DECAP_INVALID_FMT:
            printf("\tSecurity status: decapsulation error (%d), the payload content is invalid\n", rx_info->security.status);
            break;
        default:
            printf("\tSecurity status: other (%d)\n", rx_info->security.status);
            break;
    }
    return;
}


void set_tx_info(itsg5_tx_info_t *tx_info, bool is_secured)
{
    /* set data rate*/
    tx_info->data_rate_is_present = true;
    tx_info->data_rate = 12; /* 12 (500kbps) = 6 (Mbps) */

    if (is_secured) {
        /* set security*/
        tx_info->security_is_present = true;
        /*
        * Assign CAM service specific permissions according to the actual content in payload.
        * Please refer to ETSI TS 103 097, ETSI EN 302 637-2 for more details.
        * Please refer to Unex-APG-ETSI-GN-BTP for more information of build-in certificates
        */
        /* SSP Version control */
        tx_info->security.ssp[0] = 0x0;
        /* Service-specific parameter */
        tx_info->security.ssp[1] = EMERGENCY; /* Emergency container */
        tx_info->security.ssp[2] = REQUEST_FOR_FREE_CROSSING_AT_A_TRAFFIC_LIGHT; /* EmergencyPriority */
        tx_info->security.ssp_len = 3;
    }

    return;
}


int32_t cam_set_semi_axis_length(double meter)
{
    /*
     * According to ETSI TS 102 894-2 V1.2.1 (2014-09)
     * The value shall be set to:
     * 1 if the accuracy is equal to or less than 1 cm,
     * n (n > 1 and n < 4 093) if the accuracy is equal to or less than n cm,
     * 4 093 if the accuracy is equal to or less than 4 093 cm,
     * 4 094 if the accuracy is out of range, i.e. greater than 4 093 cm,
     * 4 095 if the accuracy information is unavailable.
     */
    double centimeter;
    int32_t value;

    centimeter = meter * 100.0;

    if (centimeter < 1.0) {
        value = 1;
    }
    else if (centimeter > 1.0 && centimeter < 4093.0) {
        value = (int32_t)centimeter;
    }
    else {
        value = 4094;
    }

    return value;
}


int32_t cam_set_heading_value(double degree)
{
    int32_t value;

    if (isnan(degree) == 1) {
        value = 3601;
    }
    else {
        value = degree * 10;
    }

    return value;
}

int32_t cam_set_altitude_confidence(double metre)
{
    /*
	 * According to ETSI TS 102 894-2 V1.2.1 (2014-09)
	 * Absolute accuracy of a reported altitude value of a geographical point for a predefined
	 * confidence level (e.g. 95 %). The required confidence level is defined by the
	 * corresponding standards applying the usage of this DE.
	 * The value shall be set to:
	 * 	0 if the altitude accuracy is equal to or less than 0,01 metre
	 * 	1 if the altitude accuracy is equal to or less than 0,02 metre
	 * 	2 if the altitude accuracy is equal to or less than 0,05 metre
	 * 	3 if the altitude accuracy is equal to or less than 0,1 metre
	 * 	4 if the altitude accuracy is equal to or less than 0,2 metre
	 * 	5 if the altitude accuracy is equal to or less than 0,5 metre
	 * 	6 if the altitude accuracy is equal to or less than 1 metre
	 * 	7 if the altitude accuracy is equal to or less than 2 metres
	 * 	8 if the altitude accuracy is equal to or less than 5 metres
	 * 	9 if the altitude accuracy is equal to or less than 10 metres
	 * 	10 if the altitude accuracy is equal to or less than 20 metres
	 * 	11 if the altitude accuracy is equal to or less than 50 metres
	 * 	12 if the altitude accuracy is equal to or less than 100 metres
	 * 	13 if the altitude accuracy is equal to or less than 200 metres
	 * 	14 if the altitude accuracy is out of range, i.e. greater than 200 metres
	 * 	15 if the altitude accuracy information is unavailable
	 */

    int32_t enum_value;

    if (metre <= 0.01) {
        enum_value = AltitudeConfidence_alt_000_01;
    }
    else if (metre <= 0.02) {
        enum_value = AltitudeConfidence_alt_000_02;
    }
    else if (metre <= 0.05) {
        enum_value = AltitudeConfidence_alt_000_05;
    }
    else if (metre <= 0.1) {
        enum_value = AltitudeConfidence_alt_000_10;
    }
    else if (metre <= 0.2) {
        enum_value = AltitudeConfidence_alt_000_20;
    }
    else if (metre <= 0.5) {
        enum_value = AltitudeConfidence_alt_000_50;
    }
    else if (metre <= 1.0) {
        enum_value = AltitudeConfidence_alt_001_00;
    }
    else if (metre <= 2.0) {
        enum_value = AltitudeConfidence_alt_002_00;
    }
    else if (metre <= 5.0) {
        enum_value = AltitudeConfidence_alt_005_00;
    }
    else if (metre <= 10.0) {
        enum_value = AltitudeConfidence_alt_010_00;
    }
    else if (metre <= 20.0) {
        enum_value = AltitudeConfidence_alt_020_00;
    }
    else if (metre <= 50.0) {
        enum_value = AltitudeConfidence_alt_050_00;
    }
    else if (metre <= 100.0) {
        enum_value = AltitudeConfidence_alt_100_00;
    }
    else if (metre <= 200.0) {
        enum_value = AltitudeConfidence_alt_200_00;
    }
    else {
        enum_value = AltitudeConfidence_outOfRange;
    }

    return enum_value;
}


int32_t cam_set_heading_confidence(double degree)
{
    /*
	 * According to ETSI TS 102 894-2 V1.2.1 (2014-09)
	 *
	 * The absolute accuracy of a reported heading value for a predefined confidence level
	 * (e.g. 95 %). The required confidence level is defined by the corresponding standards
	 * applying the DE.
	 * The value shall be set to:
	 * ??1 if the heading accuracy is equal to or less than 0,1 degree,
	 * ??n (n > 1 and n < 125) if the heading accuracy is equal to or less than
	 * n ? 0,1 degree,
	 * 	125 if the heading accuracy is equal to or less than 12,5 degrees,
	 * 	126 if the heading accuracy is out of range, i.e. greater than 12,5 degrees,
	 * 	127 if the heading accuracy information is not available.
	 */

    int32_t value;

    if (degree <= 0.1) {
        value = 1;
    }
    else if (degree > 0.1 && degree <= 12.5) {
        value = (int32_t)(degree * 10);
    }
    else {
        value = 126;
    }

    return value;
}


int32_t cam_set_speed_confidence(double meter_per_sec)
{
    /*
	 * According to ETSI TS 102 894-2 V1.2.1 (2014-09)
	 * The value shall be set to:
	 * 	1 if the speed accuracy is equal to or less than 1 cm/s.
	 * 	n (n > 1 and n < 125) if the speed accuracy is equal to or less than n cm/s.
	 * 	125 if the speed accuracy is equal to or less than 125 cm/s.
	 * 	126 if the speed accuracy is out of range, i.e. greater than 125 cm/s.
	 * 	127 if the speed accuracy information is not available.
	 */

    double cm_per_sec;
    int32_t value;

    cm_per_sec = meter_per_sec * 100.0;

    if (cm_per_sec <= 1.0) {
        value = 1;
    }
    else if (cm_per_sec > 1.0 && cm_per_sec < 125.0) {
        value = (int32_t)(cm_per_sec);
    }
    else if (cm_per_sec >= 125.0 && cm_per_sec < 126.0) {
        value = 125;
    }
    else {
        value = 126;
    }

    return value;
}


int load_station_config(station_config_t *config)
{
    char *content = json_fread(STATION_CONFIG_FILE_NAME);
    if (content == NULL) {
        /* File read failed, create the default config file */
        printf("The station config file not exist, create the default config file!\n");
        json_fprintf(STATION_CONFIG_FILE_NAME,
                     "{ \
                        SendCAM : [   \
                        { \
                            stationID : 168, \
                            exteriorLights : \
                            { \
                                leftTurnSignalOn : 0, \
                                rightTurnSignalOn : 0, \
                            }, \
                            role : emergency, \
                            emergency :  \
                            { \
                                lightBarInUse : 0, \
                                sirenInUse : 1, \
                                causeCode : -1, \
                            } \
                        } \
                        ] \
                    }");
        json_prettify_file(STATION_CONFIG_FILE_NAME);  // Optional
        content = json_fread(STATION_CONFIG_FILE_NAME);
    }

    if (content != NULL) {
        /* Extract setting form JSON format */
        struct json_token t_root;
        int i, len = strlen(content);

        for (i = 0; json_scanf_array_elem(content, len, ".SendCAM", i, &t_root) > 0; i++) {
            char *role = NULL;

            // printf("Index %d, token %.*s\n", i, t_root.len, t_root.ptr);
            json_scanf(t_root.ptr, t_root.len, "{stationID: %d}", &(config->stationID));
            json_scanf(t_root.ptr, t_root.len, "{exteriorLights: {leftTurnSignalOn: %d, rightTurnSignalOn: %d}}", &(config->leftTurnSignalOn), &(config->rightTurnSignalOn));
            json_scanf(t_root.ptr, t_root.len, "{role: %Q}", &role);

            if (0 == strcmp("emergency", role)) {
                config->role = VehicleRole_emergency;
                json_scanf(t_root.ptr, t_root.len, "{emergency: {lightBarInUse: %d, sirenInUse: %d, causeCode: %d}}", &(config->lightBarInUse), &(config->sirenInUse), &(config->causeCode));
            }
            else {
                config->role = VehicleRole_Default;
            }
            if (role != NULL) {
                free(role);
            }
        }
        return 0;
    }
    else {
        printf("Load station config file failed!\n");
        return -1;
    }

    return 0;
}


int32_t app_set_thread_name_and_priority(pthread_t thread, app_thread_type_t type, char *p_name, int32_t priority){
    int32_t result;
    itsg5_app_thread_config_t limited_thread_config;

#ifdef __SET_PRIORITY__
    struct sched_param param;
#endif  // __SET_PRIORITY__
    if (p_name == NULL) {
        return -1;
    }

    /* Check thread priority is in the limited range */
    itsg5_get_app_thread_config(&limited_thread_config);

    if (APP_THREAD_TX == type) {
        /* Check the limited range for tx thread priority */
        if ((priority < limited_thread_config.tx_thread_priority_low) || (priority > limited_thread_config.tx_thread_priority_high)) {
            /* Thread priority is out of range */
            printf("The tx thread priority is out of range (%d-%d): %d \n", limited_thread_config.tx_thread_priority_low, limited_thread_config.tx_thread_priority_high, priority);
            return -1;
        }
    }
    else if (APP_THREAD_RX == type) {
        /* Check the limited range for rx thread priority */
        if ((priority < limited_thread_config.rx_thread_priority_low) || (priority > limited_thread_config.rx_thread_priority_high)) {
            /* Thread priority is out of range */
            printf("The rx thread priority is out of range (%d-%d): %d \n", limited_thread_config.rx_thread_priority_low, limited_thread_config.rx_thread_priority_high, priority);
            return -1;
        }
    }
    else {
        /* Target thread type is unknown */
        printf("The thread type is unknown: %d \n", type);
        return -1;
    }

    result = pthread_setname_np(thread, p_name);
    if (result != 0) {
        printf("Can't set thread name: %d (%s) \n", result, strerror(result));
        return -1;
    }

#ifdef __SET_PRIORITY__
    param.sched_priority = priority;
    result = pthread_setschedparam(thread, SCHED_FIFO, &param);
    if (result != 0) {
        printf("Can't set thread priority: %d (%s) \n", result, strerror(result));
        return -1;
    }
#endif  // __SET_PRIORITY__
    return 0;
}

