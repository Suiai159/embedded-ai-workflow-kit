/**
  * @file    breathe_app.h
  * @brief   Breathe LED Application Layer - Business logic
  ******************************************************************************
  */

#ifndef BREATHE_APP_H
#define BREATHE_APP_H

#include <stdint.h>

/* Configuration structure */
typedef struct {
    uint32_t period_ms;         /* Breathe period in milliseconds (e.g., 5000 for 5s) */
    uint8_t  min_brightness;    /* Minimum brightness 0-100 */
    uint8_t  max_brightness;    /* Maximum brightness 0-100 */
    uint8_t  gamma;             /* Gamma correction factor (e.g., 22 for 2.2) */
} Breathe_Config_t;

/**
  * @brief  Initialize breathe application with configuration
  * @param  config: Pointer to configuration structure
  * @retval None
  */
void Breathe_App_Init(const Breathe_Config_t* config);

/**
  * @brief  Process breathe tick - call periodically
  * @param  timestamp_ms: Current timestamp in milliseconds
  * @retval None
  */
void Breathe_App_Tick(uint32_t timestamp_ms);

/**
  * @brief  Get current brightness value
  * @retval uint8_t: Current brightness 0-100
  */
uint8_t Breathe_App_GetBrightness(void);

/**
  * @brief  Get current phase as string ("UP" or "DOWN")
  * @retval const char*: Phase string
  */
const char* Breathe_App_GetPhaseString(void);

/**
  * @brief  Check if breathe is in UP phase (brightening)
  * @retval uint8_t: 1 if UP phase, 0 if DOWN phase
  */
uint8_t Breathe_App_IsUpPhase(void);

/**
  * @brief  Get current step in the breathe cycle
  * @retval uint32_t: Current step number
  */
uint32_t Breathe_App_GetStep(void);

#endif /* BREATHE_APP_H */
