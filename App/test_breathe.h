/**
  * @file    test_breathe.h
  * @brief   Breathe app self-test cases - outputs JSON via test_framework
  *          Wrapped in #ifdef TEST_MODE.
  ******************************************************************************
  */

#ifndef TEST_BREATHE_H
#define TEST_BREATHE_H

#ifdef TEST_MODE

#include "test_framework.h"
#include "breathe_app.h"
#include "led_service.h"
#include "pwm_service.h"

static inline const char *LED_ModeToStr(LED_Mode_t mode)
{
    switch (mode) {
        case LED_MODE_OFF:     return "OFF";
        case LED_MODE_ON:      return "ON";
        case LED_MODE_BREATHE: return "BREATHE";
        case LED_MODE_BLINK:   return "BLINK";
        default:               return "UNKNOWN";
    }
}

static inline void Test_Breathe_Run(void)
{
    uint32_t start = HAL_GetTick();
    TestSuite_Start("breathe_test", 5);

    /* TC001: LED initial mode after System_Init */
    LED_Mode_t mode = LED_Service_GetMode();
    TestCase_ReportStr("TC001", "LED初始模式", "LED_MODE",
                       "BREATHE", LED_ModeToStr(mode),
                       (mode == LED_MODE_BREATHE) ? TEST_PASS : TEST_FAIL);

    /* TC002: PWM initial duty cycle */
    uint8_t duty = PWM_Service_GetDuty();
    TestCase_ReportNum("TC002", "PWM初始占空比", "PWM_DUTY",
                       0, (int32_t)duty, 0);

    /* TC003: Breathe initial brightness */
    uint8_t brightness = Breathe_App_GetBrightness();
    TestCase_ReportNum("TC003", "呼吸初始亮度", "brightness",
                       0, (int32_t)brightness, 5);

    /* TC004: Breathe initial phase */
    uint8_t is_up = Breathe_App_IsUpPhase();
    TestCase_ReportStr("TC004", "呼吸初始相位", "phase",
                       "UP", is_up ? "UP" : "DOWN",
                       is_up ? TEST_PASS : TEST_FAIL);

    /* TC005: LED mode switch ON */
    LED_Service_SetMode(LED_MODE_ON);
    LED_Mode_t new_mode = LED_Service_GetMode();
    TestCase_ReportStr("TC005", "LED模式切换ON", "LED_MODE",
                       "ON", LED_ModeToStr(new_mode),
                       (new_mode == LED_MODE_ON) ? TEST_PASS : TEST_FAIL);

    /* Restore breathe mode */
    LED_Service_SetMode(LED_MODE_BREATHE);

    TestSuite_End(start);
}

#endif /* TEST_MODE */
#endif /* TEST_BREATHE_H */
