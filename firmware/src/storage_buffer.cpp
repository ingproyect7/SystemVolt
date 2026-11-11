/**
 * @file storage_buffer.cpp
 * @brief Implementación del sistema Store-and-Forward en MicroSD / Flash SPIFFS.
 * @project STV - Sistema Fotovoltaico Inteligente
 */

#include <Arduino.h>
#include <SPI.h>
#include <SD.h>
#include "pin_definitions.h"
#include "telemetry_types.h"

static const char* BUFFER_FILE_PATH = "/buffer_telemetry.bin";
static bool sd_initialized = false;
static uint32_t pending_records_count = 0;

bool initStorageBuffer() {
    Serial.println("[STORAGE] Inicializando almacenamiento en MicroSD...");
    SPI.begin(PIN_SPI_SCK, PIN_SPI_MISO, PIN_SPI_MOSI);

    if (!SD.begin(PIN_SPI_CS_SD)) {
        Serial.println("[ADVERTENCIA] Falló inicio de MicroSD. El búfer offline no estará disponible.");
        sd_initialized = false;
        return false;
    }

    sd_initialized = true;
    
    // Contar cuántos registros pendientes hay en el archivo
    if (SD.exists(BUFFER_FILE_PATH)) {
        File file = SD.open(BUFFER_FILE_PATH, FILE_READ);
        if (file) {
            pending_records_count = file.size() / sizeof(TelemetrySample);
            file.close();
            Serial.printf("[STORAGE] MicroSD lista. Registros pendientes en cola: %u\n", pending_records_count);
        }
    } else {
        Serial.println("[STORAGE] MicroSD lista. Archivo de buffer creado nuevo.");
        pending_records_count = 0;
    }

    return true;
}

bool pushSampleToBuffer(const TelemetrySample* sample) {
    if (!sd_initialized) return false;

    File file = SD.open(BUFFER_FILE_PATH, FILE_APPEND);
    if (!file) {
        Serial.println("[ERROR] No se pudo abrir archivo de buffer para escritura.");
        return false;
    }

    // Escribir estructura binaria compacta (48 bytes)
    size_t written = file.write((const uint8_t*)sample, sizeof(TelemetrySample));
    file.close();

    if (written == sizeof(TelemetrySample)) {
        pending_records_count++;
        return true;
    }
    return false;
}

uint32_t getPendingRecordsCount() {
    return pending_records_count;
}

uint8_t drainBufferedRecords(TelemetrySample* output_array, uint8_t max_records) {
    if (!sd_initialized || pending_records_count == 0) return 0;

    File file = SD.open(BUFFER_FILE_PATH, FILE_READ);
    if (!file) return 0;

    uint8_t records_read = 0;
    while (file.available() >= (int)sizeof(TelemetrySample) && records_read < max_records) {
        file.read((uint8_t*)&output_array[records_read], sizeof(TelemetrySample));
        // Marcar la muestra con bandera de haber sido recuperada de búfer offline
        output_array[records_read].flags |= 0x01;
        records_read++;
    }
    file.close();

    return records_read;
}

void commitDrainedRecords(uint8_t records_committed) {
    if (!sd_initialized || records_committed == 0) return;

    // Si se drenaron todos los registros, truncamos el archivo a 0 bytes
    if (records_committed >= pending_records_count) {
        SD.remove(BUFFER_FILE_PATH);
        pending_records_count = 0;
        Serial.println("[STORAGE] Búfer completamente sincronizado y vaciado.");
        return;
    }

    // Si aún quedan registros pendientes en cola, reescribimos el archivo temporalmente
    File source = SD.open(BUFFER_FILE_PATH, FILE_READ);
    File temp = SD.open("/temp_buf.bin", FILE_WRITE);

    // Saltar los registros ya transmitidos con éxito
    source.seek(records_committed * sizeof(TelemetrySample));
    while (source.available()) {
        temp.write(source.read());
    }

    source.close();
    temp.close();

    SD.remove(BUFFER_FILE_PATH);
    SD.rename("/temp_buf.bin", BUFFER_FILE_PATH);

    pending_records_count -= records_committed;
    Serial.printf("[STORAGE] Sincronizados %u registros. Restantes en cola: %u\n", 
                  records_committed, pending_records_count);
}
