/**
  * @file    led_service.h
  * @brief   LED Service Layer - LED control abstraction
  ******************************************************************************
  */

#ifndef LED_SERVICE_H
#define LED_SERVICE_H

#include <stdint.h>

/* LED Operation modes */
typedef enum {
    LED_MODE_OFF = 0,       /* LED always off */
    LED_MODE_ON,            /* LED always on */
    LED_MODE_BREATHE,       /* Breathing effect */
    LED_MODE_BLINK          /* Blinking effect */
} LED_Mode_t;

/**
  * @brief  Initialize LED service
  * @retval None
  */
void LED_Service_Init(void);

/**
  * @brief  Set LED operation mode
  * @param  mode: LED mode (OFF, ON, BREATHE, BLINK)
  * @retval None
  */
void LED_Service_SetMode(LED_Mode_t mode);

/**
  * @brief  Set LED brightness (for breathe mode)
  * @param  brightness: Brightness value 0-100
  * @retval None
  */
void LED_Service_SetBrightness(uint8_t brightness);

/**
  * @brief  Get current LED mode
  * @retval LED_Mode_t: Current mode
  */
LED_Mode_t LED_Service_GetMode(void);

/**
  * @brief  LED service tick handler (called periodically)
  * @param  timestamp_ms: Current timestamp in milliseconds
  * @retval None
  */
void LED_Service_Tick(uint32_t timestamp_ms);

#endif /* LED_SERVICE_H */
