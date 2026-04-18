/**
  * @file    pwm_service.c
  * @brief   PWM Service Layer Implementation - Software PWM
  ******************************************************************************
  */

#include "pwm_service.h"
#include "gpio_driver.h"
#include "tim_driver.h"

/* LED connected to PC13 */
#define PWM_LED_PORT    GPIO_PORT_C
#define PWM_LED_PIN     DRV_GPIO_PIN_13

static volatile uint8_t s_pwm_duty = 0;
static volatile uint8_t s_pwm_counter = 0;
static volatile uint8_t s_resolution = 100;
static volatile uint8_t s_running = 0;

void PWM_Service_Init(uint32_t frequency_hz, uint8_t resolution)
{
    s_resolution = resolution;
    s_pwm_duty = 0;
    s_pwm_counter = 0;
    s_running = 0;

    /* Initialize GPIO driver */
    GPIO_Driver_Init();

    /* Initialize timer with specified frequency */
    TIM_Driver_Init(frequency_hz, PWM_Service_Tick);
}

void PWM_Service_SetDuty(uint8_t duty)
{
    if (duty > s_resolution) {
        duty = s_resolution;
    }
    s_pwm_duty = duty;
}

uint8_t PWM_Service_GetDuty(void)
{
    return s_pwm_duty;
}

void PWM_Service_Tick(void)
{
    if (!s_running) {
        return;
    }

    /* Increment PWM counter */
    s_pwm_counter++;
    if (s_pwm_counter >= s_resolution) {
        s_pwm_counter = 0;
    }

    /* Update LED based on duty cycle (active low) */
    if (s_pwm_counter < s_pwm_duty) {
        GPIO_Driver_WritePin(PWM_LED_PORT, PWM_LED_PIN, GPIO_STATE_RESET);  /* LED ON (low) */
    } else {
        GPIO_Driver_WritePin(PWM_LED_PORT, PWM_LED_PIN, GPIO_STATE_SET);    /* LED OFF (high) */
    }
}

void PWM_Service_Start(void)
{
    s_running = 1;
    TIM_Driver_Start();
}

void PWM_Service_Stop(void)
{
    s_running = 0;
    TIM_Driver_Stop();
    GPIO_Driver_WritePin(PWM_LED_PORT, PWM_LED_PIN, GPIO_STATE_SET);  /* LED OFF */
}
