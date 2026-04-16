/**
  * @file    log_service.h
  * @brief   Log Service Layer - Application logging interface
  ******************************************************************************
  */

#ifndef LOG_SERVICE_H
#define LOG_SERVICE_H

#include <stdint.h>

/**
  * @brief  Initialize log service
  * @retval None
  */
void LOG_Service_Init(void);

/**
  * @brief  Send log message
  * @param  level: Log level string (e.g., "INFO", "WARN", "ERROR")
  * @param  msg: Log message
  * @retval None
  */
void LOG_Service_Message(const char* level, const char* msg);

/**
  * @brief  Formatted log message
  * @param  level: Log level string
  * @param  fmt: Format string
  * @param  ...: Variable arguments
  * @retval None
  */
void LOG_Service_Printf(const char* level, const char* fmt, ...);

/**
  * @brief  Report system status (periodic report)
  * @param  phase: Current operation phase
  * @param  value: Current value (e.g., duty cycle)
  * @param  tick: Current tick count
  * @retval None
  */
void LOG_Service_ReportStatus(const char* phase, uint8_t value, uint32_t tick);

/* Convenience macros */
#define LOG_INFO(msg)      LOG_Service_Message("INFO", msg)
#define LOG_WARN(msg)      LOG_Service_Message("WARN", msg)
#define LOG_ERROR(msg)     LOG_Service_Message("ERROR", msg)

#define LOG_INFO_FMT(fmt, ...)   LOG_Service_Printf("INFO", fmt, ##__VA_ARGS__)
#define LOG_WARN_FMT(fmt, ...)   LOG_Service_Printf("WARN", fmt, ##__VA_ARGS__)
#define LOG_ERROR_FMT(fmt, ...)  LOG_Service_Printf("ERROR", fmt, ##__VA_ARGS__)

#endif /* LOG_SERVICE_H */
