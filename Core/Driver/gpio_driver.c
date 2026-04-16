/**
  * @file    gpio_driver.c
  * @brief   GPIO Driver Layer Implementation
  ******************************************************************************
  */

#include "gpio_driver.h"
#include "stm32f1xx_hal.h"
#include "stm32f103xb.h"

/* Map port enum to actual GPIO registers */
static GPIO_TypeDef* const GPIO_PORT_MAP[] = {
    GPIOA,
    GPIOB,
    GPIOC,
    GPIOD,
    GPIOE
};

void GPIO_Driver_Init(void)
{
    /* GPIO clocks are enabled in HAL_MspInit */
    /* Pin configuration is done by CubeMX generated code (MX_GPIO_Init) */
}

void GPIO_Driver_WritePin(GPIO_Port_t port, uint8_t pin, GPIO_State_t state)
{
    if (port > GPIO_PORT_E || pin > 15) {
        return;
    }

    GPIO_TypeDef* gpio_port = GPIO_PORT_MAP[port];

    if (state == GPIO_STATE_SET) {
        gpio_port->BSRR = (1U << pin);  /* Set pin high */
    } else {
        gpio_port->BRR = (1U << pin);   /* Set pin low */
    }
}

void GPIO_Driver_TogglePin(GPIO_Port_t port, uint8_t pin)
{
    if (port > GPIO_PORT_E || pin > 15) {
        return;
    }

    GPIO_TypeDef* gpio_port = GPIO_PORT_MAP[port];
    uint32_t odr = gpio_port->ODR;

    if (odr & (1U << pin)) {
        gpio_port->BRR = (1U << pin);   /* Currently high, set low */
    } else {
        gpio_port->BSRR = (1U << pin);  /* Currently low, set high */
    }
}

GPIO_State_t GPIO_Driver_ReadPin(GPIO_Port_t port, uint8_t pin)
{
    if (port > GPIO_PORT_E || pin > 15) {
        return GPIO_STATE_RESET;
    }

    GPIO_TypeDef* gpio_port = GPIO_PORT_MAP[port];

    if (gpio_port->IDR & (1U << pin)) {
        return GPIO_STATE_SET;
    }
    return GPIO_STATE_RESET;
}
