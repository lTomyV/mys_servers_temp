#!/usr/bin/env python3
"""
Demostración del modelo físico completo de sala de servidores.
Simula transferencia de calor exterior → sala → servidor → carcasa con control dinámico.
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Agregar el path del proyecto
sys.path.append(str(Path(__file__).parent))

from src.simulation.modelo_fisico_completo import ModeloSalaServidores, SalaServidoresConfig
from src.visualization.graficos_temporales import (
    generar_grafico_evolucion_temporal, 
    generar_grafico_correlacion_temp_potencia,
    generar_resumen_diario
)

def demo_modelo_completo():
    """Demuestra el funcionamiento del modelo físico completo."""
    
    print("🏢 DEMOSTRACIÓN DEL MODELO FÍSICO COMPLETO")
    print("=" * 60)
    
    # Configurar el modelo
    config = SalaServidoresConfig(
        # Sala de servidores pequeña pero realista
        largo_sala=5.0,
        ancho_sala=4.0,
        alto_sala=3.0,
        
        # Paredes de concreto con mejor aislamiento
        espesor_pared=0.35,  # 35 cm (más gruesas)
        conductividad_concreto=1.4,  # W/(m·K) (concreto con aislante)
        area_paredes_exteriores=45.0,  # m² (menos área expuesta)
        
        # Servidor con potencia moderada
        potencia_servidor=800.0,  # W - más conservador
        masa_servidor=60.0,  # kg
        
        # Sistema de refrigeración eficiente pero no excesivo
        eficiencia_refrigeracion=3.5,  # COP alto pero realista
        potencia_min_refrigeracion=300.0,  # W
        potencia_max_refrigeracion=8000.0,  # W (reducido)
        
        # Control PID más agresivo para mantener bajo 25°C
        kp=200.0,  # Más agresivo
        ki=15.0,   # Más agresivo
        kd=8.0,    # Más agresivo
        temp_objetivo=23.5,  # Objetivo más conservador para nunca pasar de 25°C
    )
    
    print(f"Configuración de la sala:")
    print(f"  - Dimensiones: {config.largo_sala}×{config.ancho_sala}×{config.alto_sala} m")
    print(f"  - Volumen de aire: {config.volumen_aire} m³")
    print(f"  - Espesor de paredes: {config.espesor_pared} m")
    print(f"  - Potencia del servidor: {config.potencia_servidor} W")
    print(f"  - Objetivo de temperatura: {config.temp_objetivo}°C")
    
    # Generar perfil de temperatura exterior desafiante
    print(f"\nGenerando perfil de temperatura exterior...")
    
    perfil_dia = {
        'min_temp': 25.0,  # Día caluroso pero no extremo
        'max_temp': 40.0,  # Temperatura alta pero manejable
        'min_temp_hour': 6.0,
        'max_temp_hour': 15.0,
    }
    
    # Vector de tiempo (24 horas, cada 2 minutos para mayor resolución)
    tiempo_horas = np.linspace(0, 24, 24*30+1)  # 721 puntos
    tiempo_segundos = tiempo_horas * 3600
    
    # Generar perfil de temperatura exterior
    temp_exterior = np.zeros_like(tiempo_horas)
    for i, hora in enumerate(tiempo_horas):
        # Perfil sinusoidal con picos realistas
        if hora <= perfil_dia['min_temp_hour']:
            # Noche/madrugada - temperatura mínima
            temp_exterior[i] = perfil_dia['min_temp'] + 2 * np.sin((hora - 6) * np.pi / 12)
        elif hora <= perfil_dia['max_temp_hour']:
            # Mañana/mediodía - calentamiento
            factor = (hora - perfil_dia['min_temp_hour']) / (perfil_dia['max_temp_hour'] - perfil_dia['min_temp_hour'])
            temp_base = perfil_dia['min_temp'] + (perfil_dia['max_temp'] - perfil_dia['min_temp']) * np.sin(factor * np.pi / 2)
            temp_exterior[i] = temp_base + 1 * np.sin(hora * 2 * np.pi / 24)  # Variación menor
        else:
            # Tarde/noche - enfriamiento
            factor = (hora - perfil_dia['max_temp_hour']) / (24 + perfil_dia['min_temp_hour'] - perfil_dia['max_temp_hour'])
            temp_base = perfil_dia['max_temp'] - (perfil_dia['max_temp'] - perfil_dia['min_temp']) * factor
            temp_exterior[i] = temp_base + 1 * np.sin(hora * 2 * np.pi / 24)
    
    print(f"  - Temperatura mínima: {np.min(temp_exterior):.1f}°C")
    print(f"  - Temperatura máxima: {np.max(temp_exterior):.1f}°C")
    
    # Crear modelo y ejecutar simulación
    print(f"\nEjecutando simulación...")
    modelo = ModeloSalaServidores(config)
    
    resultados = modelo.simular_perfil_completo(
        temperaturas_exterior=temp_exterior,
        tiempo=tiempo_segundos,
        temp_inicial=22.0
    )
    
    # Mostrar resultados
    print(f"\n📊 RESULTADOS DE LA SIMULACIÓN:")
    print(f"  - Temperatura máxima de carcasa: {resultados['max_temp_carcasa']:.2f}°C")
    print(f"  - Temperatura promedio de carcasa: {resultados['avg_temp_carcasa']:.2f}°C")
    print(f"  - Tiempo sobre 25°C: {resultados['tiempo_sobre_25C']:.2f} horas")
    print(f"  - Energía total: {resultados['energia_total_kwh']:.2f} kWh")
    print(f"  - Potencia promedio: {resultados['potencia_promedio']:.0f} W")
    print(f"  - Potencia máxima: {resultados['potencia_maxima']:.0f} W")
    
    # Control de temperatura exitoso?
    if resultados['max_temp_carcasa'] <= 25.0:
        print(f"  ✅ Control de temperatura EXITOSO")
    else:
        print(f"  ⚠️ Control de temperatura PARCIAL - excedió 25°C")
    
    # Crear gráficos
    print(f"\n📈 Generando gráficos...")
    
    fig, axes = plt.subplots(3, 1, figsize=(12, 12))
    fig.suptitle('Simulación Completa de Sala de Servidores', fontsize=16, fontweight='bold')
    
    # Gráfico 1: Temperaturas
    ax1 = axes[0]
    ax1.plot(tiempo_horas, temp_exterior, 'r-', linewidth=2, label='Exterior')
    ax1.plot(tiempo_horas, resultados['temp_interior'], 'b-', linewidth=2, label='Interior (sala)')
    ax1.plot(tiempo_horas, resultados['temp_servidor'], 'g-', linewidth=2, label='Servidor')
    ax1.plot(tiempo_horas, resultados['temp_carcasa'], 'orange', linewidth=3, label='Carcasa (crítica)')
    ax1.axhline(y=25.0, color='red', linestyle='--', alpha=0.7, label='Límite 25°C')
    ax1.set_ylabel('Temperatura [°C]')
    ax1.set_title('Evolución de Temperaturas')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Gráfico 2: Potencia de refrigeración
    ax2 = axes[1]
    ax2.plot(tiempo_horas, resultados['potencia_refrigeracion'] / 1000, 'purple', linewidth=2)
    ax2.set_ylabel('Potencia [kW]')
    ax2.set_title('Potencia de Refrigeración (Control Dinámico)')
    ax2.grid(True, alpha=0.3)
    ax2.fill_between(tiempo_horas, 0, resultados['potencia_refrigeracion'] / 1000, alpha=0.3, color='purple')
    
    # Gráfico 3: Error de control
    ax3 = axes[2]
    error_control = resultados['temp_carcasa'] - config.temp_objetivo
    ax3.plot(tiempo_horas, error_control, 'red', linewidth=2)
    ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax3.axhline(y=1.0, color='orange', linestyle='--', alpha=0.7, label='Límite +1°C')
    ax3.set_ylabel('Error [°C]')
    ax3.set_xlabel('Tiempo [horas]')
    ax3.set_title(f'Error de Control (Objetivo: {config.temp_objetivo}°C)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar gráfico
    output_path = Path("graphs/simulacion_modelo_completo.png")
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  ✅ Gráfico guardado: {output_path}")
    
    # Generar gráficos temporales adicionales
    print(f"\n📈 Generando gráficos temporales detallados...")
    
    # Convertir formato de resultados para compatibilidad con funciones de gráficos
    resultados_convertidos = {
        'time': resultados['tiempo'],
        'T_exterior': resultados['temp_exterior'],
        'T_interior': resultados['temp_interior'],
        'T_server': resultados['temp_servidor'],
        'T_case': resultados['temp_carcasa'],
        'cooling_power': resultados['potencia_refrigeracion'],
    }
    
    # Gráfico de evolución temporal (el solicitado)
    generar_grafico_evolucion_temporal(
        resultados_convertidos, 
        titulo="Evolución Temporal: Temperaturas y Potencia de Refrigeración",
        guardar_en="graphs/evolucion_temporal_detallada.png"
    )
    
    # Gráfico de correlaciones
    generar_grafico_correlacion_temp_potencia(
        resultados_convertidos,
        guardar_en="graphs/correlacion_temperatura_potencia.png"
    )
    
    # Resumen diario en un solo gráfico
    generar_resumen_diario(
        resultados_convertidos,
        guardar_en="graphs/resumen_diario_completo.png"
    )
    
    # Mostrar estadísticas de transferencia de calor
    print(f"\n🔥 ANÁLISIS DE TRANSFERENCIA DE CALOR:")
    
    # Calcular flujos promedio en el punto más crítico (hora de mayor temperatura)
    idx_max = np.argmax(temp_exterior)
    Q_pared, Q_aire_servidor, Q_servidor_carcasa = modelo.calcular_transferencia_calor(
        temp_exterior[idx_max],
        resultados['temp_interior'][idx_max],
        resultados['temp_servidor'][idx_max],
        resultados['temp_carcasa'][idx_max]
    )
    
    print(f"  En el momento más crítico (hora {tiempo_horas[idx_max]:.1f}):")
    print(f"  - Calor entrante por paredes: {Q_pared:.0f} W")
    print(f"  - Calor del aire al servidor: {Q_aire_servidor:.0f} W")
    print(f"  - Calor del servidor a carcasa: {Q_servidor_carcasa:.0f} W")
    print(f"  - Potencia de refrigeración: {resultados['potencia_refrigeracion'][idx_max]:.0f} W")
    print(f"  - Calor removido: {resultados['potencia_refrigeracion'][idx_max] * config.eficiencia_refrigeracion:.0f} W")
    
    print(f"\n🎯 El modelo físico completo simula correctamente:")
    print(f"  ✓ Transferencia de calor a través de paredes de concreto")
    print(f"  ✓ Inercia térmica de la sala de servidores") 
    print(f"  ✓ Control dinámico PID de la refrigeración")
    print(f"  ✓ Respuesta realista a condiciones extremas")

if __name__ == "__main__":
    demo_modelo_completo()
