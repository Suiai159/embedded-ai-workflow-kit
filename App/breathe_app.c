/**
  * @file    breathe_app.c
  * @brief   Breathe LED Application Layer Implementation
  *          Pure business logic - no hardware dependencies
  ******************************************************************************
  */

#include "breathe_app.h"
#include <math.h>

/* Default sine table size */
#define SINE_TABLE_SIZE     256
#define PI                  3.14159265f

/* Static configuration */
static Breathe_Config_t s_config = {
    .period_ms = 5000,
    .min_brightness = 0,
    .max_brightness = 100,
    .gamma = 22  /* 2.2 * 10 for integer math */
};

/* Sine lookup table (256 bytes in RAM) */
static uint8_t s_sine_table[SINE_TABLE_SIZE];

/* Runtime state */
static volatile uint32_t s_step = 0;
static volatile uint32_t s_last_update_ms = 0;
static volatile uint32_t s_step_interval_ms = 0;
static volatile uint8_t s_current_brightness = 0;

/**
  * @brief  Generate sine lookup table with gamma correction
  * @retval None
  */
static void Breathe_GenerateSineTable(void)
{
    float gamma = s_config.gamma / 10.0f;

    for (int i = 0; i < SINE_TABLE_SIZE; i++) {
        /* Generate full sine wave cycle (0 to 2*PI) */
        float angle = (float)i / SINE_TABLE_SIZE * 2.0f * PI;
        float sine_val = (sinf(angle) + 1.0f) / 2.0f;  /* Map to 0.0 ~ 1.0 */

        /* Gamma correction */
        float gamma_val = powf(sine_val, gamma);

        /* Map to brightness range */
        uint8_t brightness_range = s_config.max_brightness - s_config.min_brightness;
        uint8_t duty = (uint8_t)(gamma_val * brightness_range) + s_config.min_brightness;

        if (duty > s_config.max_brightness) {
            duty = s_config.max_brightness;
        }

        s_sine_table[i] = duty;
    }
}

void Breathe_App_Init(const Breathe_Config_t* config)
{
    /* Apply configuration or use defaults */
    if (config != 0) {
        s_config.period_ms = config->period_ms;
        s_config.min_brightness = config->min_brightness;
        s_config.max_brightness = config->max_brightness;
        s_config.gamma = config->gamma;
    }

    /* Calculate step interval */
    s_step_interval_ms = s_config.period_ms / SINE_TABLE_SIZE;
    if (s_step_interval_ms == 0) {
        s_step_interval_ms = 1;
    }

    /* Reset state */
    s_step = 0;
    s_last_update_ms = 0;
    s_current_brightness = s_config.min_brightness;

    /* Generate lookup table */
    Breathe_GenerateSineTable();
}

void Breathe_App_Tick(uint32_t timestamp_ms)
{
    /* Check if it's time to update */
    if ((timestamp_ms - s_last_update_ms) < s_step_interval_ms) {
        return;
    }
    s_last_update_ms = timestamp_ms;

    /* Update step */
    s_step++;
    if (s_step >= SINE_TABLE_SIZE) {
        s_step = 0;
    }

    /* Get brightness from sine table */
    s_current_brightness = s_sine_table[s_step];
}

uint8_t Breathe_App_GetBrightness(void)
{
    return s_current_brightness;
}

const char* Breathe_App_GetPhaseString(void)
{
    /* First half of sine wave is UP (brightening), second half is DOWN */
    if (s_step < (SINE_TABLE_SIZE / 2)) {
        return "UP";
    }
    return "DOWN";
}

uint8_t Breathe_App_IsUpPhase(void)
{
    return (s_step < (SINE_TABLE_SIZE / 2)) ? 1 : 0;
}

uint32_t Breathe_App_GetStep(void)
{
    return s_step;
}
