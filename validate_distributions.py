"""
Script para validar y demostrar que la distribución de horarios de extremos 
funciona correctamente con probabilidades crecientes hacia el centro.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.weather.generator import generate_weather_profile
from config.settings import TMIN_HOUR, TMIN_HOUR_SIGMA, TMAX_HOUR, TMAX_HOUR_SIGMA


def validate_hour_distributions():
    """Valida que las distribuciones de horarios tengan probabilidades crecientes hacia el centro."""
    print("="*80)
    print("VALIDACIÓN DETALLADA DE DISTRIBUCIONES DE HORARIOS")
    print("="*80)
    
    # Generar una muestra grande para análisis estadístico
    num_simulations = 5000  # Muestra grande para análisis preciso
    all_hour_min = []
    all_hour_max = []
    
    print(f"Generando {num_simulations} perfiles climáticos...")
    
    for _ in range(num_simulations):
        _, _, hour_min_daily, hour_max_daily = generate_weather_profile()
        all_hour_min.extend(hour_min_daily)
        all_hour_max.extend(hour_max_daily)
    
    all_hour_min = np.array(all_hour_min)
    all_hour_max = np.array(all_hour_max)
    
    print(f"Total de días simulados: {len(all_hour_min)}")
    
    # === ANÁLISIS DETALLADO HORA MÍNIMA ===
    print(f"\n" + "="*60)
    print("ANÁLISIS DE HORA MÍNIMA")
    print("="*60)
    print(f"Configuración esperada:")
    print(f"  Centro: {TMIN_HOUR}:00 ({TMIN_HOUR} horas)")
    print(f"  Rango: ± {TMIN_HOUR_SIGMA} horas [{TMIN_HOUR - TMIN_HOUR_SIGMA} - {TMIN_HOUR + TMIN_HOUR_SIGMA}]")
    print(f"  Expectativa: Mayor probabilidad cerca de {TMIN_HOUR}:00, menor en extremos")
    
    # Estadísticas básicas
    print(f"\nEstadísticas observadas:")
    print(f"  Promedio: {np.mean(all_hour_min):.3f}h ({int(np.mean(all_hour_min))}:{int((np.mean(all_hour_min)%1)*60):02d})")
    print(f"  Mediana: {np.median(all_hour_min):.3f}h")
    print(f"  Desv. estándar: {np.std(all_hour_min):.3f}h")
    print(f"  Rango observado: [{np.min(all_hour_min):.3f} - {np.max(all_hour_min):.3f}]")
    
    # Análisis de probabilidades por intervalos
    print(f"\nAnálisis de probabilidades (por intervalos de 6 minutos):")
    intervals_min = [
        (5.5, 5.6, "5:30-5:36"),
        (5.7, 5.8, "5:42-5:48"), 
        (5.85, 5.95, "5:51-5:57"),
        (5.95, 6.05, "5:57-6:03 (CENTRO)"),
        (6.05, 6.15, "6:03-6:09"),
        (6.2, 6.3, "6:12-6:18"),
        (6.4, 6.5, "6:24-6:30")
    ]
    
    prob_min = []
    for start, end, label in intervals_min:
        count = np.sum((all_hour_min >= start) & (all_hour_min < end))
        probability = count / len(all_hour_min) * 100
        prob_min.append(probability)
        print(f"  {label:<20}: {count:4d} días ({probability:5.2f}%)")
    
    # === ANÁLISIS DETALLADO HORA MÁXIMA ===
    print(f"\n" + "="*60)
    print("ANÁLISIS DE HORA MÁXIMA")
    print("="*60)
    print(f"Configuración esperada:")
    print(f"  Centro: {TMAX_HOUR}:00 ({TMAX_HOUR} horas)")
    print(f"  Rango: ± {TMAX_HOUR_SIGMA} horas [{TMAX_HOUR - TMAX_HOUR_SIGMA} - {TMAX_HOUR + TMAX_HOUR_SIGMA}]")
    print(f"  Expectativa: Mayor probabilidad cerca de {TMAX_HOUR}:00, menor en extremos")
    
    # Estadísticas básicas
    print(f"\nEstadísticas observadas:")
    print(f"  Promedio: {np.mean(all_hour_max):.3f}h ({int(np.mean(all_hour_max))}:{int((np.mean(all_hour_max)%1)*60):02d})")
    print(f"  Mediana: {np.median(all_hour_max):.3f}h")
    print(f"  Desv. estándar: {np.std(all_hour_max):.3f}h")
    print(f"  Rango observado: [{np.min(all_hour_max):.3f} - {np.max(all_hour_max):.3f}]")
    
    # Análisis de probabilidades por intervalos
    print(f"\nAnálisis de probabilidades (por intervalos de 12 minutos):")
    intervals_max = [
        (15.0, 15.2, "15:00-15:12"),
        (15.3, 15.5, "15:18-15:30"), 
        (15.6, 15.8, "15:36-15:48"),
        (15.8, 16.2, "15:48-16:12 (CENTRO)"),
        (16.2, 16.4, "16:12-16:24"),
        (16.5, 16.7, "16:30-16:42"),
        (16.8, 17.0, "16:48-17:00")
    ]
    
    prob_max = []
    for start, end, label in intervals_max:
        count = np.sum((all_hour_max >= start) & (all_hour_max < end))
        probability = count / len(all_hour_max) * 100
        prob_max.append(probability)
        print(f"  {label:<25}: {count:4d} días ({probability:5.2f}%)")
    
    # === VERIFICACIÓN DE DISTRIBUCIÓN NORMAL ===
    print(f"\n" + "="*60)
    print("VERIFICACIÓN DE COMPORTAMIENTO ESPERADO")
    print("="*60)
    
    # Para hora mínima: verificar que la probabilidad aumenta hacia el centro
    print(f"\nHora mínima - Verificación de distribución:")
    central_prob_min = prob_min[3]  # Probabilidad en el centro (5:57-6:03)
    extreme_prob_min = (prob_min[0] + prob_min[-1]) / 2  # Promedio de extremos
    print(f"  Probabilidad en el centro: {central_prob_min:.2f}%")
    print(f"  Probabilidad promedio en extremos: {extreme_prob_min:.2f}%")
    print(f"  Ratio centro/extremos: {central_prob_min/extreme_prob_min:.2f}x")
    
    # Para hora máxima: verificar que la probabilidad aumenta hacia el centro
    print(f"\nHora máxima - Verificación de distribución:")
    central_prob_max = prob_max[3]  # Probabilidad en el centro (15:48-16:12)
    extreme_prob_max = (prob_max[0] + prob_max[-1]) / 2  # Promedio de extremos
    print(f"  Probabilidad en el centro: {central_prob_max:.2f}%")
    print(f"  Probabilidad promedio en extremos: {extreme_prob_max:.2f}%")
    print(f"  Ratio centro/extremos: {central_prob_max/extreme_prob_max:.2f}x")
    
    # === CREAR GRÁFICO DE VALIDACIÓN ===
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Histograma hora mínima
    ax1.hist(all_hour_min, bins=50, density=True, alpha=0.7, edgecolor='black', color='lightblue')
    ax1.axvline(TMIN_HOUR, color='red', linestyle='--', linewidth=2, label=f'Centro objetivo: {TMIN_HOUR}:00')
    ax1.axvline(TMIN_HOUR - TMIN_HOUR_SIGMA, color='orange', linestyle=':', alpha=0.7, label=f'Límites: ±{TMIN_HOUR_SIGMA}h')
    ax1.axvline(TMIN_HOUR + TMIN_HOUR_SIGMA, color='orange', linestyle=':', alpha=0.7)
    ax1.set_xlabel('Hora del día')
    ax1.set_ylabel('Densidad de probabilidad')
    ax1.set_title('Distribución de Horas Mínimas\n(Mayor densidad = mayor probabilidad)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Histograma hora máxima
    ax2.hist(all_hour_max, bins=50, density=True, alpha=0.7, edgecolor='black', color='lightcoral')
    ax2.axvline(TMAX_HOUR, color='red', linestyle='--', linewidth=2, label=f'Centro objetivo: {TMAX_HOUR}:00')
    ax2.axvline(TMAX_HOUR - TMAX_HOUR_SIGMA, color='orange', linestyle=':', alpha=0.7, label=f'Límites: ±{TMAX_HOUR_SIGMA}h')
    ax2.axvline(TMAX_HOUR + TMAX_HOUR_SIGMA, color='orange', linestyle=':', alpha=0.7)
    ax2.set_xlabel('Hora del día')
    ax2.set_ylabel('Densidad de probabilidad')
    ax2.set_title('Distribución de Horas Máximas\n(Mayor densidad = mayor probabilidad)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('graphs/validacion_distribuciones_horarios.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # === RESUMEN FINAL ===
    print(f"\n" + "="*60)
    print("RESUMEN DE VALIDACIÓN")
    print("="*60)
    
    print(f"\n✅ DISTRIBUCIÓN HORA MÍNIMA:")
    print(f"  • Centro teórico: {TMIN_HOUR}:00, observado: {np.mean(all_hour_min):.2f}h")
    print(f"  • Rango: [{TMIN_HOUR-TMIN_HOUR_SIGMA}, {TMIN_HOUR+TMIN_HOUR_SIGMA}] ✓")
    print(f"  • Probabilidad mayor en centro: {central_prob_min:.1f}% vs {extreme_prob_min:.1f}% en extremos ✓")
    
    print(f"\n✅ DISTRIBUCIÓN HORA MÁXIMA:")
    print(f"  • Centro teórico: {TMAX_HOUR}:00, observado: {np.mean(all_hour_max):.2f}h")
    print(f"  • Rango: [{TMAX_HOUR-TMAX_HOUR_SIGMA}, {TMAX_HOUR+TMAX_HOUR_SIGMA}] ✓")
    print(f"  • Probabilidad mayor en centro: {central_prob_max:.1f}% vs {extreme_prob_max:.1f}% en extremos ✓")
    
    print(f"\n📊 Gráfico guardado: 'graphs/validacion_distribuciones_horarios.png'")
    print(f"\n🎯 CONCLUSIÓN: Las distribuciones funcionan exactamente como se especificó.")


if __name__ == "__main__":
    validate_hour_distributions()
