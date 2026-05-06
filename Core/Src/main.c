/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body with layered architecture
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "usart.h"
#include "gpio.h"

/* Layered Architecture Includes */
#include "breathe_app.h"
#include "led_service.h"
#include "pwm_service.h"
#include "log_service.h"
#include "tim_driver.h"

#include <stdint.h>

#ifdef TEST_MODE
#include "test_breathe.h"
#endif

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
static void System_Init(void);
static void System_Loop(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
    /* MCU Configuration--------------------------------------------------------*/
    HAL_Init();
    SystemClock_Config();

    /* Initialize all configured peripherals */
    MX_GPIO_Init();
    MX_USART1_UART_Init();

    /* USER CODE BEGIN 2 */
    System_Init();
    /* USER CODE END 2 */

    /* Infinite loop */
    /* USER CODE BEGIN WHILE */
#ifdef TEST_MODE
    HAL_Delay(500);  /* Wait for init logs to flush */
    Test_Breathe_Run();
    while (1)
    {
        /* Test complete - fast blink to indicate alive */
        LED_Service_SetMode(LED_MODE_ON);
        HAL_Delay(100);
        LED_Service_SetMode(LED_MODE_OFF);
        HAL_Delay(100);
    }
#else
    while (1)
    {
        System_Loop();
    }
#endif
    /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/**
  * @brief  System initialization using layered architecture
  * @retval None
  */
static void System_Init(void)
{
    /* 1. Initialize Log Service */
    LOG_Service_Init();
    LOG_INFO("System Initializing...");

    /* 2. Startup indicator: LED blink 3 times */
    LED_Service_Init();
    for (int i = 0; i < 3; i++) {
        LED_Service_SetMode(LED_MODE_ON);
        HAL_Delay(200);
        LED_Service_SetMode(LED_MODE_OFF);
        HAL_Delay(200);
    }
    HAL_Delay(500);

    /* 3. Initialize Breathe Application */
    Breathe_Config_t breathe_cfg = {
        .period_ms = 5000,
        .min_brightness = 0,
        .max_brightness = 100,
        .gamma = 22  /* 2.2 */
    };
    Breathe_App_Init(&breathe_cfg);

    /* 4. Start LED in breathe mode */
    LED_Service_SetMode(LED_MODE_BREATHE);

    LOG_INFO_FMT("Breathe LED Started, Period: %d ms", breathe_cfg.period_ms);
}

/**
  * @brief  Main system loop using layered architecture
  * @retval None
  */
static void System_Loop(void)
{
    static uint32_t last_report_time = 0;
    uint32_t current_time = HAL_GetTick();

    /* 1. Update breathe application (generates brightness value) */
    Breathe_App_Tick(current_time);

    /* 2. Update LED brightness via service layer */
    uint8_t brightness = Breathe_App_GetBrightness();
    PWM_Service_SetDuty(brightness);

    /* 3. Periodic status report every 5 seconds */
    if ((current_time - last_report_time) >= 5000) {
        last_report_time = current_time;

        LOG_Service_ReportStatus(
            Breathe_App_GetPhaseString(),
            brightness,
            Breathe_App_GetStep()
        );
    }

    /* 4. Small delay to prevent busy-waiting */
    HAL_Delay(1);
}

/**
  * @brief  TIM2 interrupt handler - delegates to driver layer
  * @retval None
  */
void TIM2_IRQHandler(void)
{
    TIM_Driver_IRQHandler();
}

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
