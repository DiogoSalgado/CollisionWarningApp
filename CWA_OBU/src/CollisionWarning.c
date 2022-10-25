/**
 ********************************************************************************
 * @file    CollisionWarning.c
 * @brief   CWA - Collision Warning Application
 * @author  Diogo Salgado
 *******************************************************************************
 */
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#include <pthread.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>

#include "error_code_user.h"
#include "poti_caster_service.h"
#include "itsg5_caster_service.h"
#include "itsmsg.h"
#include "itsmsg_codec.h"

#include "inc/frozen.h"
#include "inc/send.h"
#include "inc/receive.h"
#include "inc/auxFunctions.h"
#include "inc/itsmsg_funcs.h"

/**
 * @brief   Application's main function
 * @note    Based on Unex example applications
 */
int main(int argc, char *argv[])
{
    // Variables initialization

    (void)argc;
    (void)argv;

    int ret;
    ITSMsgConfig cfg;

    // Application receives no parameters
    if (argc != 1) {
        printf("./CollisionAvoidance \n");
        return -1;
    }

    // Function that allows the signals setup
    // This allows the application to correctly shutdown
    ret = app_setup_signals();
    if (!IS_SUCCESS(ret)) {
        printf("Fail to app_setup_signals\n");
        return -1;
    }

    ret = itsmsg_init(&cfg);
    if (!IS_SUCCESS(ret)) {
        printf("Fail to init ITS message\n");
        return -1;
    }

    // Init context of the caster
    ret = itsg5_caster_init();
    if (!IS_SUCCESS(ret)) {
        printf("Fail to init ITS the caster\n");
        return -1;
    }

    // Casters configuration

    itsg5_caster_comm_config_t config_tx;
    itsg5_caster_comm_config_t config_rx;

    itsg5_app_thread_config_t app_thread_config_tx;
    itsg5_app_thread_config_t app_thread_config_rx;

    config_tx.ip = "127.0.0.1";
    config_tx.caster_id = 0;
    config_tx.caster_comm_mode = ITSG5_CASTER_MODE_TX;

    config_rx.ip = "127.0.0.1";
    config_rx.caster_id = 0;
    config_rx.caster_comm_mode = ITSG5_CASTER_MODE_RX;

    /* If the example is run in Unex device, please using the below functions to set tx and rx message threads name and priority */
    /* If the example is run on other platforms, it is optional to set tx and rx message threads name and priority */
    itsg5_get_app_thread_config(&app_thread_config_tx);
    app_set_thread_name_and_priority(pthread_self(), APP_THREAD_TX, app_thread_config_tx.tx_thread_name, app_thread_config_tx.tx_thread_priority_high);

    itsg5_get_app_thread_config(&app_thread_config_rx);
    app_set_thread_name_and_priority(pthread_self(), APP_THREAD_RX, app_thread_config_rx.rx_thread_name, app_thread_config_rx.rx_thread_priority_high);

    // Create the global variables
    createStorage();

    pthread_t tid_verifyNeighbors;
    pthread_create(&tid_verifyNeighbors, NULL, verifyNeighbors, NULL);

    // Create threads: Receive Information and Send Information

    pthread_t tid_send;
    pthread_create(&tid_send, NULL, sendInformation, &config_tx);

    receiveInformation(&config_rx);

    printf("Application terminated\n");
   
    // Deinit the ITS-G5 Caster
    itsg5_caster_deinit();

    return 0;
}
