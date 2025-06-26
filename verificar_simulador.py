"""
Script para mostrar la variabilidad en el simulador principal.
Ejecuta algunas simulaciones y muestra cómo varían día a día.
"""

import sys
import os
import numpy as np

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.simulation.runner import run_monte_carlo_simulation


def mostrar_variabilidad_simulador(num_sims=5):
    """Muestra la variabilidad en el simulador principal."""
    
    print("="*70)
    print("VERIFICACIÓN DE VARIABILIDAD EN EL SIMULADOR PRINCIPAL")
    print("="*70)
    print(f"Ejecutando {num_sims} simulaciones de la estrategia 'LineaBase'...\n")
    
    # Ejecutar algunas simulaciones y mostrar los primeros días de temperatura
    costs, temp_profiles = run_monte_carlo_simulation("LineaBase", num_sims)
    
    print(f"Costos generados: {costs}")
    print(f"Variación en costos: σ = {np.std(costs):.2f}")
    print()
    
    # Mostrar variabilidad en los perfiles de temperatura (primeros 3 días de cada simulación)
    for sim in range(min(num_sims, 5)):
        profile = temp_profiles[sim]
        
        print(f"--- Simulación {sim+1} ---")
        for day in range(3):
            day_start = day * 24
            day_end = day_start + 24
            day_temps = profile[day_start:day_end]
            
            min_temp = np.min(day_temps)
            max_temp = np.max(day_temps)
            min_hour = np.argmin(day_temps)
            max_hour = np.argmax(day_temps)
            
            print(f"  Día {day+1}: T_min={min_temp:.1f}°C ({min_hour:02d}:00), "
                  f"T_max={max_temp:.1f}°C ({max_hour:02d}:00)")
        print()
    
    # Comparar estadísticas entre simulaciones
    print("--- Estadísticas por Simulación ---")
    for sim in range(num_sims):
        profile = temp_profiles[sim]
        print(f"Simulación {sim+1}:")
        print(f"  Temp. promedio del mes: {np.mean(profile):.2f}°C")
        print(f"  Temp. mínima del mes: {np.min(profile):.2f}°C") 
        print(f"  Temp. máxima del mes: {np.max(profile):.2f}°C")
        print(f"  Desviación estándar: {np.std(profile):.2f}°C")
    
    print("\n" + "="*70)
    print("CONCLUSIÓN:")
    print("- Si ves diferentes temperaturas día a día → Randomización OK ✅")
    print("- Si ves promedios mensuales similares → Normal y esperado ✅")
    print("- La variabilidad está en los días individuales, no en los promedios")
    print("="*70)


if __name__ == "__main__":
    mostrar_variabilidad_simulador(5)
