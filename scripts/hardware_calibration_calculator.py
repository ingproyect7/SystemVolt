"""
CALCULADORA DE INGENIERÍA ELECTRÓNICA Y CALIBRACIÓN DE HARDWARE (FASE 2)
=======================================================================
Verifica el dimensionamiento térmico, disipación de potencia, rangos dinámicos
y límites de saturación para los circuitos de acondicionamiento y aislamiento
galvánico de la plataforma STV.
"""
from typing import Dict


def calculate_voltage_sensing_stage(v_string_max: float = 1000.0) -> Dict[str, float]:
    """
    Calcula los parámetros eléctricos del divisor de tensión de precisión y
    la entrada del amplificador de aislamiento galvánico Texas Instruments AMC1301.
    """
    # Resistencia superior: 3 resistores de 333.3 kΩ en serie = 1 MΩ (1W metal film 0.1%, resisten 500V c/u)
    r_top = 1_000_000.0
    # Resistencia inferior estándar E96 0.1%: 249 Ω
    r_bottom = 249.0
    r_total = r_top + r_bottom

    # Corriente que drena el divisor a tensión máxima (1000V)
    i_divider = v_string_max / r_total
    # Disipación total de potencia en el divisor: P = V^2 / R
    p_total = (v_string_max ** 2) / r_total
    # Disipación por resistor superior (tres secciones de 333.3 kΩ)
    p_per_top_resistor = ((v_string_max * (333_333.3 / r_total)) ** 2) / 333_333.3

    # Voltaje diferencial aplicado a las entradas VINP - VINN del AMC1301
    v_in_amc1301 = v_string_max * (r_bottom / r_total)
    
    # Ganancia lineal fija del AMC1301 = 8.2x
    gain_amc1301 = 8.2
    v_out_diff_amc1301 = v_in_amc1301 * gain_amc1301

    # Resolución en el ADC ADS1115 (16 bits, PGA ±2.048V, rango diferencial = 15 bits efectivos + signo)
    # LSB = 2.048V / 32768 = 62.5 µV por cuenta
    adc_lsb_volts = 2.048 / 32768.0
    volts_per_lsb_real = (adc_lsb_volts / gain_amc1301) * (r_total / r_bottom)

    return {
        "v_string_max": v_string_max,
        "r_total_ohms": r_total,
        "current_drained_ma": round(i_divider * 1000.0, 3),
        "total_power_dissipation_watts": round(p_total, 3),
        "power_per_top_resistor_watts": round(p_per_top_resistor, 3),
        "v_in_amc1301_diff_volts": round(v_in_amc1301, 4),
        "v_out_diff_amc1301_volts": round(v_out_diff_amc1301, 4),
        "amc1301_linear_limit_ok": v_in_amc1301 <= 0.250,  # Límite lineal del AMC1301 es ±250 mV
        "adc_lsb_resolution_volts": round(volts_per_lsb_real, 4)
    }


def calculate_current_sensing_stage(i_max_amps: float = 40.0) -> Dict[str, float]:
    """
    Calcula los parámetros del sensor de corriente de efecto Hall Allegro ACS758LCB-050B.
    Incluye divisor de acondicionamiento 2:1 para acoplar la salida de 5V al ADC ADS1115 (3.3V).
    """
    vcc = 5.0
    v_zero_current = vcc / 2.0  # 2.500 V
    sensitivity_raw = 0.040     # 40 mV/A (0.040 V/A)
    resistance_conductor_mohm = 0.1  # Resistencia interna del lazo de corriente primario: 100 µΩ

    # Voltaje en bornes del sensor a corriente máxima
    v_sensor_at_imax = v_zero_current + (i_max_amps * sensitivity_raw)
    
    # Divisor resistivo de precisión 2:1 (10 kΩ / 10 kΩ 0.1%) para adaptar rango 0-5V a 0-2.5V
    attenuation_factor = 0.5
    v_adc_at_imax = v_sensor_at_imax * attenuation_factor
    effective_sensitivity = sensitivity_raw * attenuation_factor  # 20 mV/A en el pin del ADC

    # Pérdida por calentamiento Joule en el sensor: P = I^2 * R
    p_joule = (i_max_amps ** 2) * (resistance_conductor_mohm / 1000.0)

    # Resolución del ADC ADS1115 con PGA ±2.048V o ±4.096V
    # Con PGA ±4.096V: LSB = 4.096V / 32768 = 125 µV
    adc_lsb_volts = 4.096 / 32768.0
    amps_per_lsb = adc_lsb_volts / effective_sensitivity

    return {
        "i_max_amps": i_max_amps,
        "v_sensor_zero_current": v_zero_current,
        "v_sensor_at_imax": round(v_sensor_at_imax, 3),
        "v_adc_at_imax": round(v_adc_at_imax, 3),
        "power_dissipation_joule_watts": round(p_joule, 4),
        "current_resolution_ma": round(amps_per_lsb * 1000.0, 3),
        "adc_within_safe_range": v_adc_at_imax <= 3.30  # Seguro para ADC alimentado a 3.3V
    }


if __name__ == "__main__":
    print("=" * 75)
    print("VERIFICACIÓN DE INGENIERÍA ELECTRÓNICA - FASE 2 (STV)")
    print("=" * 75)
    
    v_results = calculate_voltage_sensing_stage(1000.0)
    print("\n1. ETAPA DE MEDICIÓN DE TENSIÓN DC AISLADA (AMC1301 + ADS1115):")
    print(f"• Tensión máxima de entrada: {v_results['v_string_max']} V DC")
    print(f"• Corriente consumida por el divisor: {v_results['current_drained_ma']} mA")
    print(f"• Disipación total de potencia: {v_results['total_power_dissipation_watts']} W")
    print(f"• Disipación por resistor superior (1W nominal): {v_results['power_per_top_resistor_watts']} W")
    print(f"• Tensión de entrada diferencial en AMC1301: {v_results['v_in_amc1301_diff_volts'] * 1000:.2f} mV")
    print(f"• ¿Entrada dentro de rango lineal (<= 250 mV)?: {v_results['amc1301_linear_limit_ok']}")
    print(f"• Salida diferencial hacia ADC: {v_results['v_out_diff_amc1301_volts']:.3f} V")
    print(f"• Resolución mínima medible en el panel: {v_results['adc_lsb_resolution_volts']:.4f} V / cuenta LSB")

    i_results = calculate_current_sensing_stage(40.0)
    print("\n2. ETAPA DE MEDICIÓN DE CORRIENTE DC AISLADA (ACS758 + Divisor 2:1 + ADS1115):")
    print(f"• Corriente máxima de trabajo: {i_results['i_max_amps']} A")
    print(f"• Voltaje del sensor a 40 A: {i_results['v_sensor_at_imax']} V")
    print(f"• Voltaje condicionado en pin ADC: {i_results['v_adc_at_imax']} V")
    print(f"• Disipación térmica Joule en el sensor: {i_results['power_dissipation_joule_watts']} W")
    print(f"• Resolución del sensor: {i_results['current_resolution_ma']} mA / cuenta LSB")
    print(f"• ¿Voltaje dentro de límites seguros del ADC (<= 3.3V)?: {i_results['adc_within_safe_range']}")
    print("=" * 75)
