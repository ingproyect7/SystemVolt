/**
 * @file main.cpp
 * @brief Orquestador multihilo FreeRTOS para adquisición y comunicación IoT.
 * @project STV - Sistema Fotovoltaico Inteligente
 * @target ESP32-S3
 */

#include <Arduino.h>
#include "pin_definitions.h"
#include "telemetry_types.h"

// Prototipos de módulos
extern bool initSensors();
extern TelemetrySample readSensorsFiltered();
extern bool initStorageBuffer();
extern bool pushSampleToBuffer(const TelemetrySample* sample);
extern void initMQTT(const GatewayConfig* config);
extern bool connectWiFi();
extern bool connectMQTT();
extern bool publishTelemetrySample(const TelemetrySample* sample);
extern void mqttLoop();

// Cola FreeRTOS para pasar muestras del hilo de adquisición al de comunicación
static QueueHandle_t telemetryQueue;

// Configuración predeterminada del Gateway STV
static GatewayConfig config = {
    .device_uid = "STV-ESP32-S3-001",
    .plant_id = "PLANT-PILOTO-MEDELLIN",
    .wifi_ssid = "STV_LAB_WIFI",
    .wifi_password = "SolarPassword2026",
    .mqtt_broker = "192.168.1.100", // O IP del broker EMQX
    .mqtt_port = 8883,
    .mqtt_user = "stv_gateway",
    .mqtt_password = "stv_mqtt_secret_2026",
    .publish_interval_sec = 10
};

// ==============================================================================
// TAREA 1: ADQUISICIÓN DE ALTA PRIORIDAD (NÚCLEO 0 - TIEMPO REAL ESTRICTO)
// ==============================================================================
void TaskSensorAcquisition(void* pvParameters) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    const TickType_t xFrequency = pdMS_TO_TICKS(1000); // Muestreo estricto a 1 Hz (1 segundo)

    Serial.println("[TASK] Tarea de adquisición iniciada en Núcleo 0.");

    while (1) {
        // 1. Leer sensores físicos con filtrado digital pasa-bajos
        TelemetrySample sample = readSensorsFiltered();

        // 2. Enviar a la cola de comunicación (espera máxima de 50 ms si está llena)
        if (xQueueSend(telemetryQueue, &sample, pdMS_TO_TICKS(50)) != pdPASS) {
            Serial.println("[ADVERTENCIA] Cola de telemetría llena. Descartando muestra más antigua.");
        }

        // 3. Mantener frecuencia periódica estricta de 1 Hz
        vTaskDelayUntil(&xLastWakeTime, xFrequency);
    }
}

// ==============================================================================
// TAREA 2: COMUNICACIÓN, MQTT Y RESILIENCIA (NÚCLEO 1 - RED Y BUFFER)
// ==============================================================================
void TaskCommunication(void* pvParameters) {
    Serial.println("[TASK] Tarea de comunicación iniciada en Núcleo 1.");

    TelemetrySample incomingSample;
    uint32_t lastPublishTime = 0;

    while (1) {
        // Mantener conexión Wi-Fi y procesar loop de MQTT
        connectWiFi();
        mqttLoop();

        // Verificar si hay nuevas muestras en la cola generadas por el Núcleo 0
        if (xQueueReceive(telemetryQueue, &incomingSample, pdMS_TO_TICKS(100)) == pdPASS) {
            uint32_t nowSeconds = millis() / 1000;

            // Transmitir cada `publish_interval_sec` (ej. cada 10 segundos)
            if (nowSeconds - lastPublishTime >= config.publish_interval_sec) {
                lastPublishTime = nowSeconds;

                // Intentar publicar vía MQTT en tiempo real
                bool published = publishTelemetrySample(&incomingSample);

                if (published) {
                    digitalWrite(PIN_LED_STATUS_MQTT, HIGH);
                    vTaskDelay(pdMS_TO_TICKS(20));
                    digitalWrite(PIN_LED_STATUS_MQTT, LOW);
                } else {
                    // SI NO HAY CONEXIÓN A INTERNET / BROKER:
                    // Guardar automáticamente en el buffer local de la MicroSD (Store & Forward)
                    Serial.println("[OFFLINE] Sin conexión MQTT. Guardando muestra en buffer MicroSD...");
                    pushSampleToBuffer(&incomingSample);
                }
            }
        }

        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

// ==============================================================================
// SETUP Y LANZAMIENTO MULTIHILO
// ==============================================================================
void setup() {
    Serial.begin(115200);
    delay(1000);
    Serial.println("\n========================================================");
    Serial.println("   STV - SISTEMA FOTOVOLTAICO INTELIGENTE (ESP32-S3)    ");
    Serial.println("========================================================");

    // Configurar pines de LEDs indicadores
    pinMode(PIN_LED_STATUS_WIFI, OUTPUT);
    pinMode(PIN_LED_STATUS_MQTT, OUTPUT);
    pinMode(PIN_LED_ALERT, OUTPUT);

    // Inicializar hardware
    initSensors();
    initStorageBuffer();
    initMQTT(&config);

    // Crear cola FreeRTOS para 30 muestras
    telemetryQueue = xQueueCreate(30, sizeof(TelemetrySample));
    if (telemetryQueue == NULL) {
        Serial.println("[FATAL] Error al crear la cola de telemetría.");
        while (1);
    }

    // Crear Tarea de Adquisición en Núcleo 0 (Prioridad 2)
    xTaskCreatePinnedToCore(
        TaskSensorAcquisition,
        "TaskSensors",
        4096,
        NULL,
        2,
        NULL,
        0
    );

    // Crear Tarea de Comunicación en Núcleo 1 (Prioridad 1)
    xTaskCreatePinnedToCore(
        TaskCommunication,
        "TaskComms",
        8192,
        NULL,
        1,
        NULL,
        1
    );

    Serial.println("[SISTEMA] Sistema operativo FreeRTOS en ejecución.");
}

void loop() {
    // El hilo loop() queda libre; todo el trabajo lo gestionan las tareas FreeRTOS
    vTaskDelay(pdMS_TO_TICKS(1000));
}
