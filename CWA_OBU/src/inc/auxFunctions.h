#ifndef AUXFUNCTIONS_H_
#define AUXFUNCTIONS_H_

#define EARTH_RADIUS 6371.0     

typedef struct vehicleInformation {
    int stationID;
    double lat;
    double lon;
    float speed;
    float heading;
    float x_coord;
    float y_coord;
    time_t lastTimestamp;
} vehicleInformation_t;

bool    getAppRunning(void);
void    createStorage(void);

vehicleInformation_t *getNeighborsInformation(void);
vehicleInformation_t *getSelfInformation(void);
void    setSelfInformation(vehicleInformation_t *sInformation);
void    setNeighborInformation(vehicleInformation_t *nInformation);

void *verifyNeighbors();
void removeNeighbor(int index);

void    deepCopy_struct(vehicleInformation_t *target, vehicleInformation_t *source);

float powerOf(float x, int n);
float radians(float degrees);
float degrees(float radians);
float convertHeading(float value);
float f_mod(float x, float y);

void app_signal_handler(int sig_num);
int  app_setup_signals(void);

void freeMemory();

#endif