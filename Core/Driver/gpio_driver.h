/**
  * @file    gpio_driver.h
  * @brief   GPIO Driver Layer - Hardware abstraction for GPIO operations
  ******************************************************************************
  */

#ifndef GPIO_DRIVER_H
#define GPIO_DRIVER_H

#include <stdint.h>

/* GPIO Pin definitions */
#define DRV_GPIO_PIN_0    0
#define DRV_GPIO_PIN_1    1
#define DRV_GPIO_PIN_2    2
#define DRV_GPIO_PIN_3    3
#define DRV_GPIO_PIN_4    4
#define DRV_GPIO_PIN_5    5
#define DRV_GPIO_PIN_6    6
#define DRV_GPIO_PIN_7    7
#define DRV_GPIO_PIN_8    8
#define DRV_GPIO_PIN_9    9
#define DRV_GPIO_PIN_10   10
#define DRV_GPIO_PIN_11   11
#define DRV_GPIO_PIN_12   12
#define DRV_GPIO_PIN_13   13
#define DRV_GPIO_PIN_14   14
#define DRV_GPIO_PIN_15   15

/* GPIO Port definitions */
typedef enum {
    GPIO_PORT_A = 0,
    GPIO_PORT_B,
    GPIO_PORT_C,
    GPIO_PORT_D,
    GPIO_PORT_E
} GPIO_Port_t;

/* GPIO Pin state */
typedef enum {
    GPIO_STATE_RESET = 0,  /* Low */
    GPIO_STATE_SET         /* High */
} GPIO_State_t;

/**
  * @brief  Initialize GPIO driver
  * @retval None
  */
void GPIO_Driver_Init(void);

/**
  * @brief  Write pin state
  * @param  port: GPIO port
  * @param  pin: Pin number (0-15)
  * @param  state: GPIO_STATE_RESET or GPIO_STATE_SET
  * @retval None
  */
void GPIO_Driver_WritePin(GPIO_Port_t port, uint8_t pin, GPIO_State_t state);

/**
  * @brief  Toggle pin state
  * @param  port: GPIO port
  * @param  pin: Pin number (0-15)
  * @retval None
  */
void GPIO_Driver_TogglePin(GPIO_Port_t port, uint8_t pin);

/**
  * @brief  Read pin state
  * @param  port: GPIO port
  * @param  pin: Pin number (0-15)
  * @retval GPIO_State_t
  */
GPIO_State_t GPIO_Driver_ReadPin(GPIO_Port_t port, uint8_t pin);

#endif /* GPIO_DRIVER_H */
