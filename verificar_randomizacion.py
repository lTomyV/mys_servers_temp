"""
Script para verificar que la randomización de temperaturas y horarios funciona correctamente.
Genera múltiples perfiles climáticos y muestra estadísticas de variación.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.weather.generator import generate_weather_profile, generate_hourly_temperature_profile


def verificar_randomizacion(num_pruebas=20):
    """Verifica que las temperaturas y horarios se generen de manera aleatoria."""
    
    print("="*70)
    print("VERIFICACIÓN DE RANDOMIZACIÓN EN GENERACIÓN CLIMÁTICA")
    print("="*70)
    print(f"Generando {num_pruebas} perfiles climáticos independientes...\n")
    
    # Arrays para almacenar todas las generaciones
    all_t_min = []
    all_t_max = []
    all_hour_min = []
    all_hour_max = []
    
    # Generar múltiples perfiles y mostrar los primeros días
    for i in range(num_pruebas):
        t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_weather_profile()
        
        all_t_min.append(t_min_daily)
        all_t_max.append(t_max_daily)
        all_hour_min.append(hour_min_daily)
        all_hour_max.append(hour_max_daily)
        
        # Mostrar los primeros 3 días de las primeras 10 ejecuciones
        if i < 10:
            print(f"--- Ejecución {i+1} (primeros 3 días) ---")
            for day in range(3):
                hour_min_str = f"{int(hour_min_daily[day])}:{int((hour_min_daily[day] % 1) * 60):02d}"
                hour_max_str = f"{int(hour_max_daily[day])}:{int((hour_max_daily[day] % 1) * 60):02d}"
                print(f"  Día {day+1}: T_min={t_min_daily[day]:.1f}°C a las {hour_min_str}, "
                      f"T_max={t_max_daily[day]:.1f}°C a las {hour_max_str}")
            print()
    
    # Convertir a arrays de numpy para análisis
    all_t_min = np.array(all_t_min)
    all_t_max = np.array(all_t_max)
    all_hour_min = np.array(all_hour_min)
    all_hour_max = np.array(all_hour_max)
    
    # Análisis estadístico
    print("="*70)
    print("ANÁLISIS ESTADÍSTICO DE LA RANDOMIZACIÓN")
    print("="*70)
    
    # Estadísticas de temperaturas mínimas
    t_min_flat = all_t_min.flatten()
    print(f"TEMPERATURAS MÍNIMAS ({len(t_min_flat)} valores):")
    print(f"  Media: {np.mean(t_min_flat):.2f}°C")
    print(f"  Desv. Estándar: {np.std(t_min_flat):.2f}°C")
    print(f"  Rango: [{np.min(t_min_flat):.1f}, {np.max(t_min_flat):.1f}]°C")
    print(f"  Variación entre ejecuciones: {np.std([np.mean(profile) for profile in all_t_min]):.2f}°C")
    
    # Estadísticas de temperaturas máximas
    t_max_flat = all_t_max.flatten()
    print(f"\nTEMPERATURAS MÁXIMAS ({len(t_max_flat)} valores):")
    print(f"  Media: {np.mean(t_max_flat):.2f}°C")
    print(f"  Desv. Estándar: {np.std(t_max_flat):.2f}°C")
    print(f"  Rango: [{np.min(t_max_flat):.1f}, {np.max(t_max_flat):.1f}]°C")
    print(f"  Variación entre ejecuciones: {np.std([np.mean(profile) for profile in all_t_max]):.2f}°C")
    
    # Estadísticas de horarios mínimos
    hour_min_flat = all_hour_min.flatten()
    print(f"\nHORARIOS DE TEMPERATURA MÍNIMA ({len(hour_min_flat)} valores):")
    print(f"  Media: {np.mean(hour_min_flat):.2f} horas")
    print(f"  Desv. Estándar: {np.std(hour_min_flat):.2f} horas")
    print(f"  Rango: [{np.min(hour_min_flat):.2f}, {np.max(hour_min_flat):.2f}] horas")
    print(f"  Variación entre ejecuciones: {np.std([np.mean(profile) for profile in all_hour_min]):.2f} horas")
    
    # Estadísticas de horarios máximos
    hour_max_flat = all_hour_max.flatten()
    print(f"\nHORARIOS DE TEMPERATURA MÁXIMA ({len(hour_max_flat)} valores):")
    print(f"  Media: {np.mean(hour_max_flat):.2f} horas")
    print(f"  Desv. Estándar: {np.std(hour_max_flat):.2f} horas")
    print(f"  Rango: [{np.min(hour_max_flat):.2f}, {np.max(hour_max_flat):.2f}] horas")
    print(f"  Variación entre ejecuciones: {np.std([np.mean(profile) for profile in all_hour_max]):.2f} horas")
    
    # Verificación de diferencias entre ejecuciones
    print("\n" + "="*70)
    print("VERIFICACIÓN DE DIFERENCIAS ENTRE EJECUCIONES")
    print("="*70)
    
    # Comparar las primeras dos ejecuciones día por día
    print("Comparación detallada entre Ejecución 1 y Ejecución 2 (primeros 5 días):")
    print("-" * 70)
    
    for day in range(5):
        diff_t_min = abs(all_t_min[0][day] - all_t_min[1][day])
        diff_t_max = abs(all_t_max[0][day] - all_t_max[1][day])
        diff_hour_min = abs(all_hour_min[0][day] - all_hour_min[1][day])
        diff_hour_max = abs(all_hour_max[0][day] - all_hour_max[1][day])
        
        print(f"Día {day+1}:")
        print(f"  ΔT_min: {diff_t_min:.2f}°C, ΔT_max: {diff_t_max:.2f}°C")
        print(f"  ΔHora_min: {diff_hour_min:.2f}h, ΔHora_max: {diff_hour_max:.2f}h")
    
    # Crear gráficos de verificación
    crear_graficos_verificacion(all_t_min, all_t_max, all_hour_min, all_hour_max, num_pruebas)
    
    return all_t_min, all_t_max, all_hour_min, all_hour_max


def crear_graficos_verificacion(all_t_min, all_t_max, all_hour_min, all_hour_max, num_pruebas):
    """Crea gráficos para visualizar la variabilidad."""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle(f'Verificación de Randomización - {num_pruebas} Ejecuciones', fontsize=16)
    
    # Temperaturas mínimas por ejecución (promedios diarios)
    ax = axes[0, 0]
    means_t_min = [np.mean(profile) for profile in all_t_min]
    ax.plot(range(1, num_pruebas+1), means_t_min, 'bo-', alpha=0.7)
    ax.set_title('Temperatura Mínima Promedio por Ejecución')
    ax.set_xlabel('Número de Ejecución')
    ax.set_ylabel('Temperatura (°C)')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=np.mean(means_t_min), color='r', linestyle='--', alpha=0.7, label=f'Media: {np.mean(means_t_min):.1f}°C')
    ax.legend()
    
    # Temperaturas máximas por ejecución (promedios diarios)
    ax = axes[0, 1]
    means_t_max = [np.mean(profile) for profile in all_t_max]
    ax.plot(range(1, num_pruebas+1), means_t_max, 'ro-', alpha=0.7)
    ax.set_title('Temperatura Máxima Promedio por Ejecución')
    ax.set_xlabel('Número de Ejecución')
    ax.set_ylabel('Temperatura (°C)')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=np.mean(means_t_max), color='b', linestyle='--', alpha=0.7, label=f'Media: {np.mean(means_t_max):.1f}°C')
    ax.legend()
    
    # Horarios mínimos por ejecución (promedios diarios)
    ax = axes[1, 0]
    means_hour_min = [np.mean(profile) for profile in all_hour_min]
    ax.plot(range(1, num_pruebas+1), means_hour_min, 'go-', alpha=0.7)
    ax.set_title('Hora de T_min Promedio por Ejecución')
    ax.set_xlabel('Número de Ejecución')
    ax.set_ylabel('Hora del día')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=np.mean(means_hour_min), color='purple', linestyle='--', alpha=0.7, 
               label=f'Media: {np.mean(means_hour_min):.1f}h')
    ax.legend()
    
    # Horarios máximos por ejecución (promedios diarios)
    ax = axes[1, 1]
    means_hour_max = [np.mean(profile) for profile in all_hour_max]
    ax.plot(range(1, num_pruebas+1), means_hour_max, 'mo-', alpha=0.7)
    ax.set_title('Hora de T_max Promedio por Ejecución')
    ax.set_xlabel('Número de Ejecución')
    ax.set_ylabel('Hora del día')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=np.mean(means_hour_max), color='orange', linestyle='--', alpha=0.7, 
               label=f'Media: {np.mean(means_hour_max):.1f}h')
    ax.legend()
    
    plt.tight_layout()
    
    # Crear directorio graphs si no existe
    os.makedirs('graphs', exist_ok=True)
    plt.savefig('graphs/verificacion_randomizacion.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n📊 Gráfico de verificación guardado en: graphs/verificacion_randomizacion.png")


def verificar_perfiles_horarios(num_pruebas=5):
    """Verifica que los perfiles horarios también varíen."""
    print("\n" + "="*70)
    print("VERIFICACIÓN DE PERFILES HORARIOS")
    print("="*70)
    
    # Generar algunos perfiles horarios y mostrar variabilidad
    for i in range(num_pruebas):
        t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_weather_profile()
        hourly_temps = generate_hourly_temperature_profile(t_min_daily, t_max_daily, hour_min_daily, hour_max_daily)
        
        # Mostrar estadísticas del primer día
        day_1_temps = hourly_temps[:24]
        print(f"Ejecución {i+1} - Día 1:")
        print(f"  Temp. mínima del día: {np.min(day_1_temps):.1f}°C a las {np.argmin(day_1_temps):02d}:00")
        print(f"  Temp. máxima del día: {np.max(day_1_temps):.1f}°C a las {np.argmax(day_1_temps):02d}:00")
        print(f"  Rango diario: {np.max(day_1_temps) - np.min(day_1_temps):.1f}°C")
        print(f"  Temperatura a las 12:00: {day_1_temps[12]:.1f}°C")


if __name__ == "__main__":
    # Ejecutar verificaciones
    all_t_min, all_t_max, all_hour_min, all_hour_max = verificar_randomizacion(20)
    verificar_perfiles_horarios(5)
    
    print("\n" + "="*70)
    print("CONCLUSIÓN")
    print("="*70)
    print("Si ves variación en los valores anteriores, la randomización funciona correctamente.")
    print("Si todos los valores son idénticos, hay un problema con la generación aleatoria.")
    print("="*70)
