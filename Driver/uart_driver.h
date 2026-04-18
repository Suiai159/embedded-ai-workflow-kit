/**
  * @file    uart_driver.h
  * @brief   UART Driver Layer - Hardware abstraction for UART operations
  ******************************************************************************
  */

#ifndef UART_DRIVER_H
#define UART_DRIVER_H

#include <stdint.h>
#include <stdarg.h>

/**
  * @brief  Initialize UART driver
  * @retval None
  */
void UART_Driver_Init(void);

/**
  * @brief  Send a single byte
  * @param  byte: Byte to send
  * @retval None
  */
void UART_Driver_SendByte(uint8_t byte);

/**
  * @brief  Send multiple bytes
  * @param  data: Pointer to data buffer
  * @param  len: Number of bytes to send
  * @retval None
  */
void UART_Driver_SendData(const uint8_t* data, uint16_t len);

/**
  * @brief  Send a null-terminated string
  * @param  str: String to send
  * @retval None
  */
void UART_Driver_SendString(const char* str);

/**
  * @brief  Formatted print (printf-like)
  * @param  fmt: Format string
  * @param  ...: Variable arguments
  * @retval None
  */
void UART_Driver_Printf(const char* fmt, ...);

/**
  * @brief  Check if UART is ready to transmit
  * @retval uint8_t: 1 if ready, 0 if busy
  */
uint8_t UART_Driver_IsTxReady(void);

#endif /* UART_DRIVER_H */
