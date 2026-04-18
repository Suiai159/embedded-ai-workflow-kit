/**
  * @file    tim_driver.c
  * @brief   TIM Driver Layer Implementation
  ******************************************************************************
  */

#include "tim_driver.h"
#include "stm32f103xb.h"

static TIM_Driver_Callback_t s_tim_callback = 0;
static volatile uint32_t s_tim_tick = 0;

void TIM_Driver_Init(uint32_t frequency_hz, TIM_Driver_Callback_t callback)
{
    s_tim_callback = callback;
    s_tim_tick = 0;

    /* Enable TIM2 clock */
    RCC->APB1ENR |= RCC_APB1ENR_TIM2EN;

    /* Calculate prescaler and auto-reload for desired frequency
     * Timer clock = 72MHz (APB1)
     * frequency = 72MHz / (PSC+1) / (ARR+1)
     * For 20kHz: PSC=35, ARR=99 -> 72M/36/100 = 20kHz
     */
    uint32_t timer_clock = 72000000;
    uint32_t period = timer_clock / frequency_hz;

    /* Use prescaler of 35 (divide by 36) */
    TIM2->PSC = 35;
    TIM2->ARR = (period / 36) - 1;

    /* Enable auto-reload preload */
    TIM2->CR1 = TIM_CR1_ARPE;

    /* Enable update interrupt */
    TIM2->DIER |= TIM_DIER_UIE;

    /* Configure NVIC */
    NVIC_SetPriority(TIM2_IRQn, 2);
    NVIC_EnableIRQ(TIM2_IRQn);
}

void TIM_Driver_Start(void)
{
    TIM2->CR1 |= TIM_CR1_CEN;
}

void TIM_Driver_Stop(void)
{
    TIM2->CR1 &= ~TIM_CR1_CEN;
}

uint32_t TIM_Driver_GetTick(void)
{
    return s_tim_tick;
}

void TIM_Driver_IRQHandler(void)
{
    if (TIM2->SR & TIM_SR_UIF) {
        TIM2->SR &= ~TIM_SR_UIF;  /* Clear interrupt flag */
        s_tim_tick++;

        if (s_tim_callback != 0) {
            s_tim_callback();
        }
    }
}
