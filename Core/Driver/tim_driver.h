/**
  * @file    tim_driver.h
  * @brief   TIM Driver Layer - Hardware abstraction for Timer operations
  ******************************************************************************
  */

#ifndef TIM_DRIVER_H
#define TIM_DRIVER_H

#include <stdint.h>

/* Timer callback function type */
typedef void (*TIM_Driver_Callback_t)(void);

/**
  * @brief  Initialize TIM driver with specified frequency
  * @param  frequency_hz: Timer interrupt frequency in Hz
  * @param  callback: Callback function to call on timer interrupt
  * @retval None
  */
void TIM_Driver_Init(uint32_t frequency_hz, TIM_Driver_Callback_t callback);

/**
  * @brief  Start the timer
  * @retval None
  */
void TIM_Driver_Start(void);

/**
  * @brief  Stop the timer
  * @retval None
  */
void TIM_Driver_Stop(void);

/**
  * @brief  Get current tick count (incremented each interrupt)
  * @retval uint32_t: tick count
  */
uint32_t TIM_Driver_GetTick(void);

/**
  * @brief  Timer interrupt handler (call this in TIM2_IRQHandler)
  * @retval None
  */
void TIM_Driver_IRQHandler(void);

#endif /* TIM_DRIVER_H */
