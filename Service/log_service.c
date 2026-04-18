/**
  * @file    log_service.c
  * @brief   Log Service Layer Implementation
  ******************************************************************************
  */

#include "log_service.h"
#include "uart_driver.h"
#include <stdarg.h>
#include <stdio.h>

void LOG_Service_Init(void)
{
    UART_Driver_Init();
}

void LOG_Service_Message(const char* level, const char* msg)
{
    UART_Driver_SendString("[");
    UART_Driver_SendString(level);
    UART_Driver_SendString("] ");
    UART_Driver_SendString(msg);
    UART_Driver_SendString("\r\n");
}

void LOG_Service_Printf(const char* level, const char* fmt, ...)
{
    char buffer[128];
    va_list args;

    UART_Driver_SendString("[");
    UART_Driver_SendString(level);
    UART_Driver_SendString("] ");

    va_start(args, fmt);
    vsnprintf(buffer, sizeof(buffer), fmt, args);
    va_end(args);

    UART_Driver_SendString(buffer);
    UART_Driver_SendString("\r\n");
}

void LOG_Service_ReportStatus(const char* phase, uint8_t value, uint32_t tick)
{
    UART_Driver_Printf("[STATUS] phase=%s, value=%d, tick=%lu\r\n",
                       phase, value, tick);
}
