/**
  * @file    test_framework.h
  * @brief   Lightweight self-test framework - outputs structured JSON via UART
  *          All code is static inline to avoid adding .c files to Keil project.
  *          Wrapped in #ifdef TEST_MODE - compiles to nothing in normal builds.
  ******************************************************************************
  */

#ifndef TEST_FRAMEWORK_H
#define TEST_FRAMEWORK_H

#ifdef TEST_MODE

#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include "usart.h"

typedef enum {
    TEST_PASS = 0,
    TEST_FAIL = 1,
    TEST_SKIP = 2
} test_result_t;

static uint32_t g_test_passed = 0;
static uint32_t g_test_failed = 0;
static uint32_t g_test_skipped = 0;

static inline void test_print(const char *msg)
{
    HAL_UART_Transmit(&huart1, (uint8_t *)msg, strlen(msg), 1000);
}

static inline void TestSuite_Start(const char *suite_id, uint32_t count)
{
    g_test_passed = 0;
    g_test_failed = 0;
    g_test_skipped = 0;

    test_print("\r\n===TEST_BEGIN===\r\n");

    char buf[128];
    snprintf(buf, sizeof(buf),
             "{\"type\":\"suite\",\"action\":\"start\",\"id\":\"%s\",\"count\":%lu}\r\n",
             suite_id, (unsigned long)count);
    test_print(buf);
}

static inline void TestCase_ReportNum(const char *id, const char *desc,
                                      const char *check,
                                      int32_t expected, int32_t actual,
                                      int32_t tolerance)
{
    int32_t diff = actual - expected;
    if (diff < 0) diff = -diff;

    test_result_t result = (diff <= tolerance) ? TEST_PASS : TEST_FAIL;

    if (result == TEST_PASS) g_test_passed++;
    else g_test_failed++;

    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"type\":\"test\",\"id\":\"%s\",\"desc\":\"%s\",\"check\":\"%s\","
             "\"expected\":%ld,\"actual\":%ld,\"result\":\"%s\"}\r\n",
             id, desc, check,
             (long)expected, (long)actual,
             result == TEST_PASS ? "PASS" : "FAIL");
    test_print(buf);
}

static inline void TestCase_ReportStr(const char *id, const char *desc,
                                      const char *check,
                                      const char *expected, const char *actual,
                                      test_result_t result)
{
    if (result == TEST_PASS) g_test_passed++;
    else if (result == TEST_FAIL) g_test_failed++;
    else g_test_skipped++;

    char buf[256];
    snprintf(buf, sizeof(buf),
             "{\"type\":\"test\",\"id\":\"%s\",\"desc\":\"%s\",\"check\":\"%s\","
             "\"expected\":\"%s\",\"actual\":\"%s\",\"result\":\"%s\"}\r\n",
             id, desc, check, expected, actual,
             result == TEST_PASS ? "PASS" : (result == TEST_FAIL ? "FAIL" : "SKIP"));
    test_print(buf);
}

static inline void TestSuite_End(uint32_t start_tick)
{
    uint32_t duration = HAL_GetTick() - start_tick;

    char buf[128];
    snprintf(buf, sizeof(buf),
             "{\"type\":\"suite\",\"action\":\"end\",\"passed\":%lu,\"failed\":%lu,"
             "\"skipped\":%lu,\"duration_ms\":%lu}\r\n"
             "===TEST_END===\r\n",
             (unsigned long)g_test_passed, (unsigned long)g_test_failed,
             (unsigned long)g_test_skipped, (unsigned long)duration);
    test_print(buf);
}

#endif /* TEST_MODE */
#endif /* TEST_FRAMEWORK_H */
