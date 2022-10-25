#ifndef SEND_H_
#define SEND_H_

#include "../inc/auxFunctions.h"

void camEncode(uint8_t **tx_buf, vehicleInformation_t *vInformation, int *tx_buf_len, poti_fix_data_t *p_fix_data);
void sendInformation(itsg5_caster_comm_config_t *config);

#endif