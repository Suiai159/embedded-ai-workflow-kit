/**
  * @file    pwm_service.h
  * @brief   PWM Service Layer - Software PWM generation
  ******************************************************************************
  */

#ifndef PWM_SERVICE_H
#define PWM_SERVICE_H

#include <stdint.h>

/* PWM Configuration */
#define PWM_RESOLUTION      100     /* PWM resolution 0-100 */
#define PWM_FREQUENCY_HZ    20000   /* 20kHz for no visible flicker */

/**
  * @brief  Initialize PWM service
  * @param  frequency_hz: PWM frequency in Hz
  * @param  resolution: PWM resolution (duty cycle range)
  * @retval None
  */
void PWM_Service_Init(uint32_t frequency_hz, uint8_t resolution);

/**
  * @brief  Set PWM duty cycle
  * @param  duty: Duty cycle value (0 to resolution)
  * @retval None
  */
void PWM_Service_SetDuty(uint8_t duty);

/**
  * @brief  Get current PWM duty cycle
  * @retval uint8_t: Current duty cycle
  */
uint8_t PWM_Service_GetDuty(void);

/**
  * @brief  PWM tick handler (called by timer interrupt)
  * @retval None
  */
void PWM_Service_Tick(void);

/**
  * @brief  Start PWM output
  * @retval None
  */
void PWM_Service_Start(void);

/**
  * @brief  Stop PWM output
  * @retval None
  */
void PWM_Service_Stop(void);

#endif /* PWM_SERVICE_H */
