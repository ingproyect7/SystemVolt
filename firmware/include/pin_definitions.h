/**
 * @file pin_definitions.h
 * @brief Asignación formal de pines GPIO y constantes de calibración de transductores.
 * @project STV - Sistema Fotovoltaico Inteligente
 * @target ESP32-S3-WROOM-1 / ESP32
 */

#ifndef PIN_DEFINITIONS_H
#define PIN_DEFINITIONS_H

#include <stdint.h>

// ==============================================================================
// 1. ASIGNACIÓN DE PINES GPIO
// ==============================================================================

// --- Bus I2C Principal (ADS1115 ADC, SHT31 Clima, DS3231 RTC, MLX90614 IR) ---
#define PIN_I2C_SDA             8
#define PIN_I2C_SCL             9
#define I2C_FREQUENCY_HZ        400000  // 400 kHz Fast-Mode

// --- Bus SPI (Tarjeta MicroSD y MAX31865 PT100) ---
#define PIN_SPI_SCK             12
#define PIN_SPI_MISO            13
#define PIN_SPI_MOSI            11
#define PIN_SPI_CS_SD           10      // Chip Select MicroSD
#define PIN_SPI_CS_MAX31865     14      // Chip Select RTD PT100

// --- Puerto UART2 para Bus RS-485 (Inversor Modbus / Piranómetro) ---
#define PIN_RS485_TX            17
#define PIN_RS485_RX            18
#define PIN_RS485_DE_RE         21      // Control de flujo (opcional con MAX13487 AutoDirection)
#define RS485_BAUDRATE          9600

// --- Bus 1-Wire (Sensor DS18B20 auxiliar de temperatura) ---
#define PIN_ONEWIRE_TEMP        4

// --- Entradas / Salidas de Señalización y Estado ---
#define PIN_LED_STATUS_WIFI     47      // LED Verde: Estado de conexión
#define PIN_LED_STATUS_MQTT     48      // LED Azul: Tráfico MQTT
#define PIN_LED_ALERT           45      // LED Rojo: Alerta crítica local
#define PIN_INPUT_DC_DISCONNECT 38      // Entrada digital: Estado seccionador DC

// ==============================================================================
// 2. DIRECCIONES DEL BUS I2C
// ==============================================================================
#define I2C_ADDR_ADS1115        0x48    // ADC 16 bits (ADDR a GND)
#define I2C_ADDR_SHT31          0x44    // Sensor Temperatura/Humedad
#define I2C_ADDR_DS3231_RTC     0x68    // Reloj RTC
#define I2C_ADDR_MLX90614       0x5A    // Termómetro Infrarrojo Hotspots

// ==============================================================================
// 3. CONSTANTES Y COEFICIENTES DE CALIBRACIÓN DE TRANSDUCTORES
// ==============================================================================

/**
 * Cadena de Tensión DC (AMC1301 + Divisor E96 + ADS1115):
 * R_top = 1.0 MΩ (3 x 333.3 kΩ), R_bottom = 249.0 Ω (0.1% precisión).
 * Relación divisor = 249 / (1000000 + 249) = 0.000248937
 * Ganancia AMC1301 = 8.2x diferencial.
 * Factor total = 1.0 / (0.000248937 * 8.2) = 490.00 V/V
 */
#define CALIB_V_DIVIDER_RATIO   0.000248937f
#define CALIB_AMC1301_GAIN      8.2f
#define CALIB_VOLTAGE_SCALE     490.00f     // Factor para convertir V_diff del ADC a Voltios DC reales
#define VOLTAGE_MAX_SAFE_LIMIT  1050.0f     // Límite de corte por sobretensión (V)

/**
 * Cadena de Corriente DC (Allegro ACS758LCB-050B + Acondicionador 2:1):
 * Rango: -50 A a +50 A.
 * Sensibilidad nominal bruta: 40.0 mV/A.
 * Con atenuador resistivo 2:1 a la entrada del ADC (protege los 3.3V del ESP32):
 * Sensibilidad efectiva en pin ADC: 20.0 mV/A (0.020 V/A).
 * Voltaje de reposo a 0 A en pin ADC: 2.50V / 2 = 1.250 V.
 */
#define CALIB_ACS758_VREF       1.250f      // Voltaje en reposo en el pin ADC (V)
#define CALIB_ACS758_SENS       0.020f      // Sensibilidad efectiva en Voltios por Amperio (20 mV/A)
#define CURRENT_MAX_SAFE_LIMIT  45.0f       // Límite de corte por sobrecorriente (A)

/**
 * Parámetros del RTD PT100 (MAX31865):
 * Rref = 430.0 Ω (resistor de referencia de precisión 0.1%).
 * R0 = 100.0 Ω (resistencia de la PT100 a 0 °C).
 */
#define PT100_RREF              430.0f
#define PT100_R0                100.0f

#endif // PIN_DEFINITIONS_H
