/**
 * @file telemetry_types.h
 * @brief Estructuras de datos para la adquisición, buffer local y telemetría MQTT.
 * @project STV - Sistema Fotovoltaico Inteligente
 */

#ifndef TELEMETRY_TYPES_H
#define TELEMETRY_TYPES_H

#include <stdint.h>
#include <stdbool.h>

#pragma pack(push, 1)

/**
 * Estructura binaria compacta para almacenamiento en buffer MicroSD o envío MQTT.
 * Tamaño optimizado a 48 bytes por registro para minimizar ancho de banda y uso de flash.
 */
typedef struct {
    uint32_t timestamp_unix;    // Segundos UNIX desde 1970 (obtenido del RTC DS3231)
    
    // Variables Eléctricas DC
    float v_dc;                 // Voltios DC del arreglo fotovoltaico
    float i_dc;                 // Amperios DC del arreglo
    float p_dc;                 // Vatios DC calculados
    
    // Variables Ambientales
    float g_irradiance;         // Irradiancia solar (W/m²)
    float t_panel;              // Temperatura del panel fotovoltaico (°C)
    float t_ambient;            // Temperatura ambiente (°C)
    float rh_ambient;           // Humedad relativa ambiente (%)
    
    // Variables Inversor (Opcional, si se lee por Modbus)
    float p_ac;                 // Potencia activa AC (W)
    float frequency;            // Frecuencia de red (Hz)
    
    // Diagnóstico de Hardware Edge
    int8_t wifi_rssi;           // Potencia de señal Wi-Fi (dBm)
    uint8_t flags;              // Bit 0: Offline buffered, Bit 1: Overvoltage, Bit 2: Inverter error
} TelemetrySample;

#pragma pack(pop)

typedef struct {
    char device_uid[32];
    char plant_id[40];
    char wifi_ssid[32];
    char wifi_password[64];
    char mqtt_broker[64];
    uint16_t mqtt_port;
    char mqtt_user[32];
    char mqtt_password[64];
    uint16_t publish_interval_sec;
} GatewayConfig;

#endif // TELEMETRY_TYPES_H
