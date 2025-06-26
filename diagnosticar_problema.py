"""
Diagnóstico específico para encontrar por qué los promedios horarios están fijos.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.weather.generator import generate_weather_profile, generate_hourly_temperature_profile
from src.analysis.statistics import calculate_temperature_statistics


def diagnosticar_promedios_horarios():
    """Diagnostica por qué los promedios horarios salen siempre iguales."""
    
    print("="*80)
    print("DIAGNÓSTICO DE PROMEDIOS HORARIOS FIJOS")
    print("="*80)
    
    # Generar 5 simulaciones y analizar perfiles horarios
    num_sims = 5
    temperature_profiles = []
    
    print("Generando perfiles de temperatura...\n")
    
    for sim in range(num_sims):
        t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_weather_profile()
        hourly_temps = generate_hourly_temperature_profile(t_min_daily, t_max_daily, hour_min_daily, hour_max_daily)
        temperature_profiles.append(hourly_temps)
        
        # Mostrar detalles del primer día
        day_1_temps = hourly_temps[:24]
        print(f"--- Simulación {sim+1}, Día 1 ---")
        print(f"T_min generada: {t_min_daily[0]:.2f}°C a las {hour_min_daily[0]:.2f}h")
        print(f"T_max generada: {t_max_daily[0]:.2f}°C a las {hour_max_daily[0]:.2f}h")
        print(f"Perfil horario - Min: {np.min(day_1_temps):.2f}°C en hora {np.argmin(day_1_temps)}")
        print(f"Perfil horario - Max: {np.max(day_1_temps):.2f}°C en hora {np.argmax(day_1_temps)}")
        print(f"Temperaturas horarias: {[f'{temp:.1f}' for temp in day_1_temps[:12]]}...")
        print()
    
    # Calcular estadísticas usando la función original
    print("="*80)
    print("ANÁLISIS DE ESTADÍSTICAS HORARIAS")
    print("="*80)
    
    temp_stats = calculate_temperature_statistics(temperature_profiles)
    
    print("Promedios por hora del día:")
    for hour in range(24):
        print(f"Hora {hour:02d}:00 - Promedio: {temp_stats['hourly_means'][hour]:.2f}°C")
    
    print(f"\nHora con menor promedio: {temp_stats['min_hour']:02d}:00 ({temp_stats['hourly_means'][temp_stats['min_hour']]:.2f}°C)")
    print(f"Hora con mayor promedio: {temp_stats['max_hour']:02d}:00 ({temp_stats['hourly_means'][temp_stats['max_hour']]:.2f}°C)")
    
    # Análisis detallado de la distribución horaria
    print("\n" + "="*80)
    print("ANÁLISIS DETALLADO DE DISTRIBUCIÓN HORARIA")
    print("="*80)
    
    # Ver la estructura de temp_data
    temp_data = np.array(temperature_profiles)
    print(f"Forma de temp_data: {temp_data.shape}")
    print(f"Total de horas por simulación: {temp_data.shape[1]}")
    print(f"Días esperados: {temp_data.shape[1] // 24}")
    
    # Analizar variabilidad por hora específica
    test_hours = [6, 12, 16, 18]  # Horas típicas de interés
    
    for test_hour in test_hours:
        hour_values = []
        for sim in range(num_sims):
            for day in range(31):  # 31 días
                hour_idx = day * 24 + test_hour
                if hour_idx < temp_data.shape[1]:
                    hour_values.append(temp_data[sim, hour_idx])
        
        if hour_values:
            print(f"\nHora {test_hour:02d}:00 - {len(hour_values)} valores:")
            print(f"  Media: {np.mean(hour_values):.2f}°C")
            print(f"  Desv. Std: {np.std(hour_values):.2f}°C")
            print(f"  Rango: [{np.min(hour_values):.1f}, {np.max(hour_values):.1f}]°C")
            print(f"  Primeros 10 valores: {[f'{v:.1f}' for v in hour_values[:10]]}")
    
    # Crear gráfico de diagnóstico
    crear_grafico_diagnostico(temperature_profiles, temp_stats)
    
    return temperature_profiles, temp_stats


def crear_grafico_diagnostico(temperature_profiles, temp_stats):
    """Crea gráficos de diagnóstico para visualizar el problema."""
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Diagnóstico de Promedios Horarios', fontsize=16)
    
    # Gráfico 1: Perfiles de temperatura de las primeras 3 simulaciones (primeros 3 días)
    ax = axes[0, 0]
    colors = ['blue', 'red', 'green']
    for sim in range(min(3, len(temperature_profiles))):
        day_hours = np.arange(0, 72)  # 3 días = 72 horas
        temps = temperature_profiles[sim][:72]
        ax.plot(day_hours, temps, color=colors[sim], alpha=0.7, label=f'Simulación {sim+1}')
    
    ax.set_title('Perfiles de Temperatura (Primeros 3 Días)')
    ax.set_xlabel('Hora (desde inicio)')
    ax.set_ylabel('Temperatura (°C)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Gráfico 2: Promedios horarios a lo largo del día
    ax = axes[0, 1]
    hours = np.arange(24)
    ax.plot(hours, temp_stats['hourly_means'], 'bo-', linewidth=2, markersize=6)
    ax.set_title('Promedios por Hora del Día')
    ax.set_xlabel('Hora del Día')
    ax.set_ylabel('Temperatura Promedio (°C)')
    ax.set_xticks(range(0, 24, 2))
    ax.grid(True, alpha=0.3)
    
    # Marcar las horas extremas
    min_hour = temp_stats['min_hour']
    max_hour = temp_stats['max_hour']
    ax.plot(min_hour, temp_stats['hourly_means'][min_hour], 'ro', markersize=10, label='Mínimo')
    ax.plot(max_hour, temp_stats['hourly_means'][max_hour], 'go', markersize=10, label='Máximo')
    ax.legend()
    
    # Gráfico 3: Distribución de temperaturas por hora clave
    ax = axes[1, 0]
    test_hours = [6, 12, 16, 18]
    temp_data = np.array(temperature_profiles)
    
    box_data = []
    labels = []
    for hour in test_hours:
        hour_values = []
        for sim in range(temp_data.shape[0]):
            for day in range(31):
                hour_idx = day * 24 + hour
                if hour_idx < temp_data.shape[1]:
                    hour_values.append(temp_data[sim, hour_idx])
        box_data.append(hour_values)
        labels.append(f'{hour:02d}:00')
    
    ax.boxplot(box_data, labels=labels)
    ax.set_title('Distribución de Temperaturas por Hora')
    ax.set_ylabel('Temperatura (°C)')
    ax.grid(True, alpha=0.3)
    
    # Gráfico 4: Mapa de calor simplificado
    ax = axes[1, 1]
    
    # Crear matriz de temperaturas por hora y día (promedio de todas las simulaciones)
    heat_data = np.zeros((24, 31))  # 24 horas x 31 días
    
    for hour in range(24):
        for day in range(31):
            day_temps = []
            for sim in range(len(temperature_profiles)):
                hour_idx = day * 24 + hour
                if hour_idx < len(temperature_profiles[sim]):
                    day_temps.append(temperature_profiles[sim][hour_idx])
            if day_temps:
                heat_data[hour, day] = np.mean(day_temps)
    
    im = ax.imshow(heat_data, cmap='RdYlBu_r', aspect='auto')
    ax.set_title('Mapa de Calor: Temperatura por Hora y Día')
    ax.set_xlabel('Día del Mes')
    ax.set_ylabel('Hora del Día')
    ax.set_yticks(range(0, 24, 2))
    ax.set_yticklabels([f'{h:02d}:00' for h in range(0, 24, 2)])
    plt.colorbar(im, ax=ax, label='Temperatura (°C)')
    
    plt.tight_layout()
    
    # Crear directorio graphs si no existe
    os.makedirs('graphs', exist_ok=True)
    plt.savefig('graphs/diagnostico_promedios_horarios.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n📊 Gráfico de diagnóstico guardado en: graphs/diagnostico_promedios_horarios.png")


if __name__ == "__main__":
    profiles, stats = diagnosticar_promedios_horarios()
    
    print("\n" + "="*80)
    print("POSIBLES CAUSAS DEL PROBLEMA:")
    print("="*80)
    print("1. Los horarios aleatorios se redondean a enteros -> pérdida de variabilidad")
    print("2. El suavizado puede estar homogeneizando demasiado los perfiles")
    print("3. El número de simulaciones puede ser insuficiente para mostrar variabilidad")
    print("4. La función sinusoidal base puede dominar sobre los valores aleatorios")
    print("="*80)
