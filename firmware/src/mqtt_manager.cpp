/**
 * @file mqtt_manager.cpp
 * @brief Cliente MQTT 5.0 sobre TLS con serialización JSON y gestión de reconexión.
 * @project STV - Sistema Fotovoltaico Inteligente
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "telemetry_types.h"

// Declaraciones de funciones del buffer
extern uint8_t drainBufferedRecords(TelemetrySample* output_array, uint8_t max_records);
extern void commitDrainedRecords(uint8_t records_committed);
extern uint32_t getPendingRecordsCount();

static WiFiClientSecure espClient;
static PubSubClient mqttClient(espClient);

static GatewayConfig gwConfig;
static char topicTelemetry[128];
static char topicStatus[128];
static char topicBatch[128];

void initMQTT(const GatewayConfig* config) {
    gwConfig = *config;

    // Configurar tópicos MQTT
    snprintf(topicTelemetry, sizeof(topicTelemetry), "stv/v1/%s/%s/telemetry", 
             gwConfig.plant_id, gwConfig.device_uid);
    snprintf(topicStatus, sizeof(topicStatus), "stv/v1/%s/%s/status", 
             gwConfig.plant_id, gwConfig.device_uid);
    snprintf(topicBatch, sizeof(topicBatch), "stv/v1/%s/%s/batch", 
             gwConfig.plant_id, gwConfig.device_uid);

    // En producción se cargan los certificados raíz X.509 de la CA con espClient.setCACert(...)
    // Para entornos de desarrollo permitimos TLS sin validación estricta de certificado local:
    espClient.setInsecure();

    mqttClient.setServer(gwConfig.mqtt_broker, gwConfig.mqtt_port);
    mqttClient.setBufferSize(2048); // Búfer para paquetes JSON
}

bool connectWiFi() {
    if (WiFi.status() == WL_CONNECTED) return true;

    Serial.printf("[WIFI] Conectando a %s...\n", gwConfig.wifi_ssid);
    WiFi.mode(WIFI_STA);
    WiFi.begin(gwConfig.wifi_ssid, gwConfig.wifi_password);

    uint8_t attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 15) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("\n[WIFI] Conectado exitosamente. IP: %s | RSSI: %d dBm\n", 
                      WiFi.localIP().toString().c_str(), WiFi.RSSI());
        return true;
    }

    Serial.println("\n[ERROR] No se pudo conectar a la red Wi-Fi.");
    return false;
}

bool connectMQTT() {
    if (mqttClient.connected()) return true;
    if (WiFi.status() != WL_CONNECTED) return false;

    Serial.print("[MQTT] Conectando al broker seguro...");

    // Payload de Last Will and Testament (LWT) para avisar si el dispositivo se apaga bruscamente
    const char* willTopic = topicStatus;
    const char* willMessage = "{\"status\": \"offline\", \"reason\": \"connection_lost\"}";
    uint8_t willQos = 1;
    bool willRetain = true;

    if (mqttClient.connect(gwConfig.device_uid, gwConfig.mqtt_user, gwConfig.mqtt_password,
                           willTopic, willQos, willRetain, willMessage)) {
        Serial.println(" ¡Conectado!");
        
        // Publicar estado ONLINE retenido
        char onlinePayload[128];
        snprintf(onlinePayload, sizeof(onlinePayload), 
                 "{\"status\": \"online\", \"ip\": \"%s\", \"rssi\": %d}", 
                 WiFi.localIP().toString().c_str(), WiFi.RSSI());
        mqttClient.publish(topicStatus, onlinePayload, true);
        return true;
    }

    Serial.printf(" Falló (rc=%d). Reintentando en el siguiente ciclo.\n", mqttClient.state());
    return false;
}

bool publishTelemetrySample(const TelemetrySample* sample) {
    if (!mqttClient.connected()) return false;

    // Serializar a formato JSON idéntico al contrato Pydantic TelemetryIngestPayload de la Fase 1
    JsonDocument doc;
    doc["device_uid"] = gwConfig.device_uid;
    doc["plant_id"] = gwConfig.plant_id;
    doc["timestamp"] = sample->timestamp_unix;

    JsonObject dc = doc["dc"].to<JsonObject>();
    dc["v_dc"] = serialized(String(sample->v_dc, 2));
    dc["i_dc"] = serialized(String(sample->i_dc, 2));
    dc["p_dc"] = serialized(String(sample->p_dc, 2));

    JsonObject env = doc["env"].to<JsonObject>();
    env["g_irradiance"] = serialized(String(sample->g_irradiance, 1));
    env["t_panel"] = serialized(String(sample->t_panel, 1));
    env["t_ambient"] = serialized(String(sample->t_ambient, 1));
    env["rh_ambient"] = serialized(String(sample->rh_ambient, 1));

    JsonObject status = doc["status"].to<JsonObject>();
    status["wifi_rssi"] = WiFi.RSSI();
    status["buffer_pending_records"] = getPendingRecordsCount();
    status["uptime_seconds"] = esp_timer_get_time() / 1000000;

    char jsonBuffer[512];
    serializeJson(doc, jsonBuffer, sizeof(jsonBuffer));

    return mqttClient.publish(topicTelemetry, jsonBuffer, false);
}

void processOfflineDraining() {
    uint32_t pending = getPendingRecordsCount();
    if (pending == 0 || !mqttClient.connected()) return;

    Serial.printf("[DRAIN] Vaciando buffer offline. Registros pendientes: %u\n", pending);

    const uint8_t BATCH_SIZE = 10;
    TelemetrySample batch[BATCH_SIZE];

    uint8_t readCount = drainBufferedRecords(batch, BATCH_SIZE);
    if (readCount == 0) return;

    uint8_t publishedCount = 0;
    for (uint8_t i = 0; i < readCount; i++) {
        if (publishTelemetrySample(&batch[i])) {
            publishedCount++;
            delay(20); // Pequeña pausa para no saturar el canal
        } else {
            break;
        }
    }

    if (publishedCount > 0) {
        commitDrainedRecords(publishedCount);
    }
}

void mqttLoop() {
    if (WiFi.status() == WL_CONNECTED) {
        if (!mqttClient.connected()) {
            connectMQTT();
        } else {
            mqttClient.loop();
            // Si el broker está conectado y hay datos en el buffer de la SD, drenar en segundo plano
            processOfflineDraining();
        }
    }
}
