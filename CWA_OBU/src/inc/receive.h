#ifndef RECEIVE_H_
#define RECEIVE_H_

#include "../inc/auxFunctions.h"

void camDecode(uint8_t *p_rx_payload, vehicleInformation_t *vehicle, int rx_payload_len, itsg5_rx_info_t *p_itsg5_rx_info);

void *receiveInformation(void *config);

#endif