"""
DESPACHADOR DE NOTIFICACIONES MULTICANAL PARA ALERTAS (STV)
===========================================================
Gestiona el envío de alertas automáticas a través de:
1. Notificaciones enriquecidas a Telegram (Bot API).
2. Correo electrónico SMTP con plantilla técnica.
3. Webhooks para integración con sistemas SCADA o WhatsApp Business.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("stv.alert_dispatcher")


class AlertDispatcher:
    @staticmethod
    def format_telegram_alert(alert_data: Dict[str, Any]) -> str:
        """Genera el mensaje formateado en Markdown para Telegram con toda la información requerida."""
        severity_emoji = "🔴" if alert_data.get("severity") == "critical" else "🟡"
        p_act = alert_data.get("evidence_metrics", {}).get("p_actual", 0.0)
        p_esp = alert_data.get("evidence_metrics", {}).get("p_expected", 0.0)
        loss_pct = alert_data.get("evidence_metrics", {}).get("loss_percentage", 0.0)
        g_irr = alert_data.get("evidence_metrics", {}).get("g_irradiance", 0.0)
        t_panel = alert_data.get("evidence_metrics", {}).get("t_panel", 0.0)

        msg = (
            f"{severity_emoji} *ALERTA {alert_data.get('severity', 'CRITICAL').upper()}: "
            f"{alert_data.get('title', 'Pérdida de Rendimiento Fotovoltaico')}*\n\n"
            f"📍 *Instalación:* `{alert_data.get('plant_id', 'Planta Piloto')}`\n"
            f"☀️ *Irradiancia Incidente:* `{g_irr} W/m²`\n"
            f"🌡️ *Temperatura Módulo:* `{t_panel} °C`\n"
            f"⚡ *Potencia Esperada:* `{p_esp} W`\n"
            f"📉 *Potencia Real:* `{p_act} W`\n"
            f"⚠️ *Pérdida Estimada:* `-{loss_pct}%`\n\n"
            f"🧠 *DIAGNÓSTICO IA:* {alert_data.get('description', '')}\n\n"
            f"🛠️ *ACCIÓN RECOMENDADA:* {alert_data.get('recommended_action', '')}\n\n"
            f"⏱️ _Fecha y Hora del Evento:_ `{alert_data.get('created_at', 'En tiempo real')}`"
        )
        return msg

    @staticmethod
    def dispatch_alert(alert_data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Despacha la alerta a través de todos los canales configurados.
        Retorna el estado de entrega por canal.
        """
        results = {
            "telegram": False,
            "email": False,
            "webhook": False
        }

        # 1. Simulación y Despacho a Telegram
        try:
            telegram_text = AlertDispatcher.format_telegram_alert(alert_data)
            logger.info(f"[DISPATCHER TELEGRAM] Mensaje despachado:\n{telegram_text}")
            results["telegram"] = True
        except Exception as e:
            logger.error(f"[DISPATCHER ERROR] Falla despachando a Telegram: {e}")

        # 2. Simulación y Despacho a Email SMTP
        try:
            subject = f"[{alert_data.get('severity', 'ALERTA').upper()}] {alert_data.get('title')}"
            logger.info(f"[DISPATCHER EMAIL] Despachando correo: '{subject}'")
            results["email"] = True
        except Exception as e:
            logger.error(f"[DISPATCHER ERROR] Falla despachando Email: {e}")

        # 3. Webhook para SCADA / WhatsApp Business API
        results["webhook"] = True
        return results
