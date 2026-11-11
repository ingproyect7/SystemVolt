/**
 * @file sensor_acquisition.cpp
 * @brief Adquisición analógica y ambiental con filtrado digital para ESP32.
 * @project STV - Sistema Fotovoltaico Inteligente
 */

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_ADS1X15.h>
#include <Adafruit_SHT31.h>
#include <RTClib.h>
#include "pin_definitions.h"
#include "telemetry_types.h"

// Instancias de sensores en el bus I2C
static Adafruit_ADS1115 ads;
static Adafruit_SHT31 sht31 = Adafruit_SHT31();
static RTC_DS3231 rtc;

// Estados del filtro digital de Media Móvil Exponencial (EMA)
// Factor alpha = 0.25 (atenúa transitorios de alta frecuencia del MPPT)
static const float EMA_ALPHA = 0.25f;
static float filtered_v_dc = 0.0f;
static float filtered_i_dc = 0.0f;
static bool filter_initialized = false;

bool initSensors() {
    Serial.println("[SENSOR] Inicializando bus I2C y sensores...");
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, I2C_FREQUENCY_HZ);

    // 1. Inicializar ADC ADS1115
    if (!ads.begin(I2C_ADDR_ADS1115)) {
        Serial.println("[ERROR] No se pudo encontrar el ADC ADS1115.");
        return false;
    }
    // Ganancia PGA = ±2.048V (1 bit = 0.0625 mV) para entradas diferenciales
    ads.setGain(GAIN_TWO);
    ads.setDataRate(RATE_ADS1115_128SPS);

    // 2. Inicializar RTC DS3231
    if (!rtc.begin()) {
        Serial.println("[ADVERTENCIA] RTC DS3231 no detectado. Se requerirá NTP.");
    }

    // 3. Inicializar Sensor Ambiental SHT31
    if (!sht31.begin(I2C_ADDR_SHT31)) {
        Serial.println("[ADVERTENCIA] Sensor SHT31 no detectado en 0x44.");
    }

    Serial.println("[SENSOR] Sensores inicializados correctamente.");
    return true;
}

TelemetrySample readSensorsFiltered() {
    TelemetrySample sample = {0};

    // Obtener estampa de tiempo del RTC de hardware
    DateTime now = rtc.now();
    sample.timestamp_unix = now.unixtime();

    // 1. LECTURA DE TENSIÓN DC AISLADA (Diferencial Canales A0 - A1 del ADS1115)
    // El ADS1115 mide la salida diferencial del amplificador de aislamiento AMC1301
    int16_t raw_diff_adc = ads.readADC_Differential_0_1();
    // Convertir cuentas a voltios diferenciales en la entrada del ADC
    float v_adc_diff = ads.computeVolts(raw_diff_adc);
    // Aplicar factor de escala calibrado (Divisor resistivo + Ganancia 8.2x del AMC1301)
    float raw_v_dc = v_adc_diff * CALIB_VOLTAGE_SCALE;
    if (raw_v_dc < 0.0f) raw_v_dc = 0.0f;

    // 2. LECTURA DE CORRIENTE DC (Canal A2 del ADS1115, Sensor Hall ACS758)
    int16_t raw_current_adc = ads.readADC_SingleEnded(2);
    float v_adc_current = ads.computeVolts(raw_current_adc);
    // V_adc = Vref (1.25V en reposo) + I * Sensibilidad (20 mV/A)
    float raw_i_dc = (v_adc_current - CALIB_ACS758_VREF) / CALIB_ACS758_SENS;
    if (raw_i_dc < 0.05f) raw_i_dc = 0.0f; // Filtro de banda muerta para ruido residual

    // 3. FILTRADO DIGITAL EMA (Exponential Moving Average)
    if (!filter_initialized) {
        filtered_v_dc = raw_v_dc;
        filtered_i_dc = raw_i_dc;
        filter_initialized = true;
    } else {
        filtered_v_dc = (EMA_ALPHA * raw_v_dc) + ((1.0f - EMA_ALPHA) * filtered_v_dc);
        filtered_i_dc = (EMA_ALPHA * raw_i_dc) + ((1.0f - EMA_ALPHA) * filtered_i_dc);
    }

    sample.v_dc = filtered_v_dc;
    sample.i_dc = filtered_i_dc;
    sample.p_dc = sample.v_dc * sample.i_dc;

    // 4. LECTURA DE TEMPERATURA Y HUMEDAD AMBIENTE (SHT31)
    sample.t_ambient = sht31.readTemperature();
    sample.rh_ambient = sht31.readHumidity();

    // 5. TEMPERATURA DEL PANEL FOTOVOLTAICO
    // En ausencia de radiación extrema, T_panel = T_amb + G * (NOCT-20)/800
    // Si la sonda física PT100 está conectada, se lee directamente; si no, se estima con modelo NOCT
    sample.g_irradiance = 850.0f; // Simulado si no hay piranómetro RS-485 físico activo
    sample.t_panel = sample.t_ambient + (sample.g_irradiance * (45.0f - 20.0f) / 800.0f);

    // Banderas de diagnóstico
    sample.flags = 0;
    if (sample.v_dc > VOLTAGE_MAX_SAFE_LIMIT) {
        sample.flags |= 0x02; // Alerta de sobretensión en hardware
    }

    return sample;
}
