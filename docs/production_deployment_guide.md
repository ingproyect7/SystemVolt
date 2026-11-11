# GUÍA DE DESPLIEGUE EN PRODUCCIÓN, ESCALABILIDAD Y CIBERSEGURIDAD (FASE 10)

---

## 1. ARQUITECTURA DE DESPLIEGUE EN PRODUCCIÓN

```
                        [ INTERNET / RED DE CAMPO ]
                                     │
                        [ REVERSE PROXY NGINX / TLS 1.3 ]
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
   [ PUERTO 443 HTTPS ]      [ PUERTO 8883 MQTTS ]     [ PUERTO 3000 HTTP ]
           │                         │                         │
     [ FASTAPI CORE ]         [ BROKER EMQX TLS ]       [ FRONTEND REACT ]
     (3 Réplicas Uvicorn)     (Clúster de Ingestión)    (Nginx Static CDN)
           │                         │
           ├─────────────────────────┤
           ▼                         ▼
   [ REDIS 7 CLUSTER ] ──► [ TIMESCALEDB PG16 ]
   (Colas y Sesiones)       (Hipertablas Particionadas + Compresión)
```

---

## 2. PROCEDIMIENTO DE COMISIONAMIENTO Y EMPAREJAMIENTO DE GATEWAYS

Para dar de alta un nuevo dispositivo de campo de forma segura:

1. **Aprovisionamiento Criptográfico:**  
   Cada Gateway `ESP32-S3` se graba de fábrica con un par de claves públicas/privadas y un `device_uid` único basado en la dirección MAC del chip.
2. **Registro en Plataforma Web:**  
   El instalador accede al módulo de administración y registra el identificador de hardware del dispositivo asociándolo a una planta solar específica. La plataforma genera un token HMAC de aprovisionamiento de un solo uso.
3. **Puesta en Marcha en Terreno:**  
   El técnico alimenta el gateway con $12\text{--}24\,\text{V DC}$. El dispositivo se conecta a la red Wi-Fi o 4G local, realiza un handshake mTLS hacia el broker en el puerto 8883 y emite su primer paquete de telemetría de prueba.
4. **Verificación de Línea:**  
   El técnico observa el LED verde de estado en la caja estanca IP65 y valida en su teléfono móvil que el dashboard STV muestre la planta en estado `ONLINE`.

---

## 3. CIBERSEGURIDAD INDUSTRIAL (ESTÁNDAR IEC 62443)

- **Cifrado en Tránsito:** Ningún dato viaja en texto plano. Se exige TLS 1.3 con suite de cifrado `ECDHE-ECDSA-AES128-GCM-SHA256` para MQTT y HTTPS.
- **Autenticación Fuerte de Dispositivos:** Cada gateway se autentica mediante credenciales independientes con permisos de publicación restringidos únicamente a su propio tópico: `stv/v1/{empresa_id}/{planta_id}/{device_uid}/#`.
- **Aislamiento Multi-tenant:** El backend aplica filtros automáticos por `company_id` en todas las consultas de base de datos para impedir fugas de información entre empresas rivales.
- **Protección contra Inyección y Denegación de Servicio (DoS):**
  - Limitador de tasa (*Rate Limiting*) en el API Gateway mediante Redis (máximo 60 peticiones/minuto por IP).
  - Validación física de parámetros en Pydantic antes de tocar la base de datos.

---

## 4. POLÍTICAS DE COPIA DE SEGURIDAD Y RECUPERACIÓN ANTE DESASTRES

1. **Respaldos Automatizados (pg_dump):**  
   Ejecución diaria a las 02:00 AM UTC de un volcado comprimido de la base de datos relacional y catálogo de usuarios, transferido a un bucket de almacenamiento seguro (AWS S3 / Cloudflare R2) con retención de 30 días.
2. **Retención Histórica de Series Temporales (TimescaleDB):**
   - **Datos brutos (muestras cada 10 segundos):** Se almacenan comprimidos durante 14 días.
   - **Datos agregados (promedios de 5 minutos y 1 hora):** Se generan mediante *Continuous Aggregates* y se conservan de forma permanente para análisis de degradación a lo largo de los 25 años de vida útil de la planta.
3. **Recuperación ante Desastres (RTO / RPO):**
   - **RPO (Pérdida máxima de datos admisible):** $< 15\,\text{minutos}$ (gracias a los buffers locales Store-and-Forward de los gateways).
   - **RTO (Tiempo de recuperación del servicio):** $< 30\,\text{minutos}$ mediante despliegue orquestado con Docker Compose.
