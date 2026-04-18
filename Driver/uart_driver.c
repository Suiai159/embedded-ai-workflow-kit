/**
  * @file    uart_driver.c
  * @brief   UART Driver Layer Implementation
  ******************************************************************************
  */

#include "uart_driver.h"
#include "stm32f1xx_hal.h"
#include "stm32f103xb.h"
#include "usart.h"
#include <string.h>
#include <stdio.h>

/* External handle from HAL */
extern UART_HandleTypeDef huart1;

void UART_Driver_Init(void)
{
    /* UART is initialized by MX_USART1_UART_Init() */
    HAL_Delay(100);  /* Wait for stability */
}

void UART_Driver_SendByte(uint8_t byte)
{
    HAL_UART_Transmit(&huart1, &byte, 1, 100);
}

void UART_Driver_SendData(const uint8_t* data, uint16_t len)
{
    if (data == 0 || len == 0) {
        return;
    }
    HAL_UART_Transmit(&huart1, (uint8_t*)data, len, 100);
}

void UART_Driver_SendString(const char* str)
{
    if (str == 0) {
        return;
    }
    HAL_UART_Transmit(&huart1, (uint8_t*)str, strlen(str), 100);
}

void UART_Driver_Printf(const char* fmt, ...)
{
    char buffer[128];
    va_list args;

    va_start(args, fmt);
    vsnprintf(buffer, sizeof(buffer), fmt, args);
    va_end(args);

    HAL_UART_Transmit(&huart1, (uint8_t*)buffer, strlen(buffer), 100);
}

uint8_t UART_Driver_IsTxReady(void)
{
    return (USART1->SR & USART_SR_TXE) ? 1 : 0;
}

/* Redirect printf to UART */
int fputc(int ch, FILE* f)
{
    HAL_UART_Transmit(&huart1, (uint8_t*)&ch, 1, 100);
    return ch;
}
