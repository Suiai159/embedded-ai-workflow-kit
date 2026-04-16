/**
  * @file    led_service.c
  * @brief   LED Service Layer Implementation
  ******************************************************************************
  */

#include "led_service.h"
#include "pwm_service.h"
#include "gpio_driver.h"

#define LED_PORT    GPIO_PORT_C
#define LED_PIN     DRV_GPIO_PIN_13

static LED_Mode_t s_led_mode = LED_MODE_OFF;
static uint8_t s_led_brightness = 0;

void LED_Service_Init(void)
{
    s_led_mode = LED_MODE_OFF;
    s_led_brightness = 0;

    /* Initialize GPIO and PWM */
    GPIO_Driver_Init();
    PWM_Service_Init(20000, 100);  /* 20kHz, 100 steps */

    /* LED off by default (active low) */
    GPIO_Driver_WritePin(LED_PORT, LED_PIN, GPIO_STATE_SET);
}

void LED_Service_SetMode(LED_Mode_t mode)
{
    s_led_mode = mode;

    switch (mode) {
        case LED_MODE_OFF:
            PWM_Service_Stop();
            GPIO_Driver_WritePin(LED_PORT, LED_PIN, GPIO_STATE_SET);  /* LED OFF */
            break;

        case LED_MODE_ON:
            PWM_Service_Stop();
            GPIO_Driver_WritePin(LED_PORT, LED_PIN, GPIO_STATE_RESET);  /* LED ON */
            break;

        case LED_MODE_BREATHE:
            PWM_Service_Start();
            break;

        case LED_MODE_BLINK:
            PWM_Service_Stop();
            break;
    }
}

void LED_Service_SetBrightness(uint8_t brightness)
{
    if (brightness > 100) {
        brightness = 100;
    }
    s_led_brightness = brightness;

    if (s_led_mode == LED_MODE_BREATHE) {
        PWM_Service_SetDuty(brightness);
    }
}

LED_Mode_t LED_Service_GetMode(void)
{
    return s_led_mode;
}

void LED_Service_Tick(uint32_t timestamp_ms)
{
    (void)s_led_brightness;  /* Currently unused, reserved for future modes */

    if (s_led_mode == LED_MODE_BLINK) {
        /* Simple blink: toggle every call (call rate controls blink speed) */
        GPIO_Driver_TogglePin(LED_PORT, LED_PIN);
    }
}
