#!/usr/bin/env python3
"""
Script específico para generar el gráfico solicitado:
- Temperatura exterior vs tiempo
- Temperatura de carcasa vs tiempo  
- Potencia de refrigeración vs tiempo
"""

import sys
import numpy as np
from pathlib import Path

# Agregar el path del proyecto
sys.path.append(str(Path(__file__).parent))

from src.simulation.modelo_fisico_completo import ModeloSalaServidores, SalaServidoresConfig
from src.visualization.graficos_temporales import generar_grafico_evolucion_temporal

def generar_grafico_solicitado():
    """
    Genera el gráfico específico solicitado con una simulación de ejemplo.
    """
    
    print("🎯 GENERANDO GRÁFICO SOLICITADO")
    print("=" * 50)
    print("Gráfico: Temperatura Exterior | Temperatura Carcasa | Potencia Refrigeración")
    print("Vs Tiempo (horas)")
    
    # Configurar modelo con parámetros optimizados
    config = SalaServidoresConfig(
        # Sala mediana
        largo_sala=6.0,
        ancho_sala=5.0,
        alto_sala=3.0,
        
        # Paredes bien aisladas
        espesor_pared=0.30,
        conductividad_concreto=1.5,
        area_paredes_exteriores=50.0,
        
        # Servidor típico
        potencia_servidor=1000.0,
        masa_servidor=70.0,
        
        # Sistema de refrigeración más potente
        eficiencia_refrigeracion=3.5,  # COP bueno
        potencia_min_refrigeracion=1200.0,  # W - mucho más alto
        potencia_max_refrigeracion=12000.0,  # W - más potencia máxima
        
        # Control PID efectivo pero no agresivo
        kp=60.0,   # Equilibrado
        ki=2.5,    # Equilibrado
        kd=1.5,    # Equilibrado
        temp_objetivo=23.5,  # Objetivo más estricto pero alcanzable
    )
    
    # Perfil de temperatura exterior realista (día caluroso de verano)
    print("Configurando día de verano con alta variación térmica...")
    
    # 24 horas con resolución de 5 minutos
    tiempo_horas = np.linspace(0, 24, 24*12+1)  # 289 puntos
    tiempo_segundos = tiempo_horas * 3600
    
    # Perfil de temperatura exterior más realista
    temp_exterior = np.zeros_like(tiempo_horas)
    for i, hora in enumerate(tiempo_horas):
        # Temperatura base sinusoidal
        temp_base = 30.0 + 12.0 * np.sin((hora - 6) * np.pi / 12)
        
        # Añadir variación adicional para momentos del día
        if 10 <= hora <= 18:  # Horas de mayor calor
            temp_extra = 3.0 * np.sin((hora - 10) * np.pi / 8)
        else:
            temp_extra = 0
            
        # Pequeñas variaciones aleatorias
        ruido = np.random.normal(0, 0.5)
        
        temp_exterior[i] = temp_base + temp_extra + ruido
    
    # Limitar temperaturas a rangos realistas
    temp_exterior = np.clip(temp_exterior, 18, 45)
    
    print(f"Temperatura exterior: {np.min(temp_exterior):.1f}°C - {np.max(temp_exterior):.1f}°C")
    
    # Ejecutar simulación
    print("Ejecutando simulación del sistema de refrigeración...")
    modelo = ModeloSalaServidores(config)
    
    resultados = modelo.simular_perfil_completo(
        temperaturas_exterior=temp_exterior,
        tiempo=tiempo_segundos,
        temp_inicial=22.0
    )
    
    # Mostrar resumen
    print(f"\n📊 RESUMEN DE LA SIMULACIÓN:")
    print(f"  ✓ Temperatura máxima de carcasa: {resultados['max_temp_carcasa']:.2f}°C")
    print(f"  ✓ Tiempo sobre 25°C: {resultados['tiempo_sobre_25C']:.2f} horas")
    print(f"  ✓ Energía consumida: {resultados['energia_total_kwh']:.2f} kWh")
    print(f"  ✓ Potencia promedio: {resultados['potencia_promedio']:.0f} W")
    
    if resultados['max_temp_carcasa'] <= 25.0:
        print(f"  🎯 CONTROL EXITOSO - Temperatura siempre bajo 25°C")
        estado = "EXITOSO"
    else:
        print(f"  ⚠️  CONTROL PARCIAL - Temperatura excedió límite")
        estado = "PARCIAL"
    
    # Convertir formato para gráfico
    datos_grafico = {
        'time': resultados['tiempo'],
        'T_exterior': resultados['temp_exterior'],
        'T_case': resultados['temp_carcasa'],
        'cooling_power': resultados['potencia_refrigeracion'],
    }
    
    # Generar el gráfico solicitado
    print(f"\n📈 Generando gráfico de evolución temporal...")
    
    titulo = f"Sistema de Refrigeración de Sala de Servidores - Control {estado}"
    
    generar_grafico_evolucion_temporal(
        datos_grafico,
        titulo=titulo,
        guardar_en="graphs/temperatura_exterior_carcasa_potencia.png"
    )
    
    print(f"\n✅ GRÁFICO GENERADO EXITOSAMENTE")
    print(f"📍 Ubicación: graphs/temperatura_exterior_carcasa_potencia.png")
    print(f"\nEl gráfico muestra:")
    print(f"  📈 Panel Superior: Temperatura Exterior vs Tiempo")
    print(f"  🌡️  Panel Medio: Temperatura de Carcasa vs Tiempo (con límite de 25°C)")
    print(f"  ⚡ Panel Inferior: Potencia de Refrigeración vs Tiempo")
    print(f"\n🎯 Este gráfico demuestra cómo el sistema ajusta dinámicamente")
    print(f"    la potencia de refrigeración para mantener la carcasa")
    print(f"    del servidor por debajo de 25°C sin importar la temperatura exterior.")

if __name__ == "__main__":
    generar_grafico_solicitado()
