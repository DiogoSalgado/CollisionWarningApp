#ifndef ITSMSG_FUNCS_H_
#define ITSMSG_FUNCS_H_

#define STATION_CONFIG_FILE_NAME "config_station.json"

#define ERR_MSG_SZ 256
#define MALLOC(sz) malloc(sz)
#define CALLOC(n, sz) calloc((n), (sz))
#define FREE(ptr) free(ptr)

/*
 *******************************************************************************
 * Macros
 *******************************************************************************
 */

/* Predefined CAM information */
#define CAM_PROTOCOL_VERSION (2) /* ETSI EN 302 637-2 V1.4.1 (2019-04) */
#define CAM_STATION_ID_DEF (168U)
#define CAM_STATION_TYPE_DEF ITS_STATION_ROAD_SIDE_UNIT

/** Predefined CAM macro functions
 *  Please correct following macros for getting data from additional INS sensors on host system.
 */
#define CAM_SENSOR_GET_DRIVE_DIRECTION() (0) /* DriveDirection_forward */
#define CAM_SENSOR_GET_VEHICLE_LENGTH_VALUE() (38) /* 0.1 metre. */
#define CAM_SENSOR_GET_VEHICLE_LENGTH_CONF() (0) /* VehicleLengthConfidenceIndication_noTrailerPresent */
#define CAM_SENSOR_GET_VEGICLE_WIDTH_VALUE() (18) /* 0.1 metre. */
#define CAM_SENSOR_GET_LONG_ACCEL_VALUE() (0) /* 0.1 m/s^2. */
#define CAM_SENSOR_GET_LONG_ACCEL_CONF() (102) /* 1 ~ 102 */
#define CAM_SENSOR_GET_CURVATURE_VALUE() (0) /* Curvature, 1 over 30000 meters, (-30000 .. 30001) */
#define CAM_SENSOR_GET_CURVATURE_CONF() (7) /* 0 ~ 7. */
#define CAM_SENSOR_GET_CURVATURE_CONF_CAL_MODE() (2) /* CurvatureCalculationMode_unavailable */
#define CAM_SENSOR_GET_YAW_RATE_VALUE() (0) /* 0,01 degree per second. */
#define CAM_SENSOR_GET_YAW_RATE_CONF() (8) /* YawRateConfidence_unavailable_ITS */

#define IS_CAM_SSP_VALID(x, y) (((x) & (y)) ? true : false)
#define CAM_SSP_LEN (3U)
/* SSP Definitions for Permissions in CAM */
/* Octet Position: 0 , SSP Version control */
/* Octet Position: 1 */
#define CEN_DSRC_TOLLING_ZONE (1 << 7)
#define PUBLIC_TRANSPORT (1 << 6)
#define SPECIAL_TRANSPORT (1 << 5)
#define DANGEROUS_GOODS (1 << 4)
#define ROADWORK (1 << 3)
#define RESCUE (1 << 2)
#define EMERGENCY (1 << 1)
#define SAFETY_CAR (1 << 0)
/* Octet Position: 2 */
#define CLOSED_LANES (1 << 7)
#define REQUEST_FOR_RIGHT_OF_WAY (1 << 6)
#define REQUEST_FOR_FREE_CROSSING_AT_A_TRAFFIC_LIGHT (1 << 5)
#define NO_PASSING (1 << 4)
#define NO_PASSING_FOR_TRUCKS (1 << 3)
#define SPEEED_LIMIT (1 << 2)

/* ITS-S type, defined in ETSI EN 302 636-4-1 V1.2.1 chapter 6.3 Fields of the GeoNetworking address */
typedef enum its_station_type {
    ITS_STATION_UNKNOWN = 0,
    ITS_STATION_PEDESTRAIN = 1,
    ITS_STATION_CYCLIST = 2,
    ITS_STATION_MOPED = 3,
    ITS_STATION_MOTORCYCLE = 4,
    ITS_STATION_PASSENGER_CAR = 5,
    ITS_STATION_BUS = 6,
    ITS_STATION_LIGHT_TRUCK = 7,
    ITS_STATION_HEAVY_TRUCK = 8,
    ITS_STATION_TRAILER = 9,
    ITS_STATION_SPECIAL_VEHICLE = 10,
    ITS_STATION_TRAM = 11,
    ITS_STATION_ROAD_SIDE_UNIT = 15,
} its_station_type_t;

typedef struct station_config {
    uint32_t stationID;
    VehicleRole role;  ///<  Reference to VehicleRole
    bool leftTurnSignalOn;  ///< Left turn signal status, 0 for signal off, 1 for signal on
    bool rightTurnSignalOn;  ///< Right turn signal status, 0 for signal off, 1 for signal on
    bool lightBarInUse;  ///<  Role type: emergency, please refer to LightBarSirenInUse
    bool sirenInUse;  ///<  Role type: emergency, please refer to LightBarSirenInUse
    int32_t causeCode;  ///<  Role type: emergency, please refer to CauseCodeType, -1 for this option not used
} station_config_t;

/* Thread type is using for application send and receive thread, the application thread type is an optional method depend on execute platform */
typedef enum app_thread_type {
    APP_THREAD_TX = 0,
    APP_THREAD_RX = 1
} app_thread_type_t;

// Function Definition
int     cam_check_msg_permission(CAM_V2 *p_cam_msg, uint8_t *p_ssp, uint8_t ssp_len);
void    dump_rx_info(itsg5_rx_info_t *rx_info);
void    set_tx_info(itsg5_tx_info_t *tx_info, bool is_secured);
int32_t cam_set_semi_axis_length(double meter);
int32_t cam_set_heading_value(double degree);
int32_t cam_set_altitude_confidence(double metre);
int32_t cam_set_heading_confidence(double degree);
int32_t cam_set_speed_confidence(double meter_per_sec);
int     load_station_config(station_config_t *config);
int32_t app_set_thread_name_and_priority(pthread_t thread, app_thread_type_t type, char *p_name, int32_t priority);


#endif