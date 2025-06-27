"""
Script de prueba para verificar que las distribuciones gaussianas 
estén funcionando correctamente según los parámetros especificados.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.weather.generator import generate_weather_profile
from config.settings import (
    TMIN_MEDIAN, TMAX_MEDIAN, TMIN_SIGMA, TMAX_SIGMA,
    TMIN_HOUR, TMIN_HOUR_SIGMA, TMAX_HOUR, TMAX_HOUR_SIGMA
)

def test_temperature_distributions(n_samples=1000):
    """Prueba las distribuciones de temperaturas para múltiples muestras."""
    print("🔬 Probando distribuciones de temperaturas...")
    
    all_t_min = []
    all_t_max = []
    all_hour_min = []
    all_hour_max = []
    
    # Generar múltiples perfiles para obtener estadísticas robustas
    for _ in range(n_samples):
        t_min, t_max, hour_min, hour_max = generate_weather_profile()
        all_t_min.extend(t_min)
        all_t_max.extend(t_max)
        all_hour_min.extend(hour_min)
        all_hour_max.extend(hour_max)
    
    all_t_min = np.array(all_t_min)
    all_t_max = np.array(all_t_max)
    all_hour_min = np.array(all_hour_min)
    all_hour_max = np.array(all_hour_max)
    
    print(f"\n📊 Estadísticas de {len(all_t_min)} valores:")
    
    # Temperaturas mínimas
    print(f"\n🌡️  TEMPERATURAS MÍNIMAS:")
    print(f"  • Objetivo: μ={TMIN_MEDIAN}°C, σ={TMIN_SIGMA}, rango=[16°C, 25°C]")
    print(f"  • Obtenido: μ={np.mean(all_t_min):.3f}°C, σ={np.std(all_t_min):.3f}")
    print(f"  • Rango: {np.min(all_t_min):.1f}°C - {np.max(all_t_min):.1f}°C")
    print(f"  • En rango: {np.sum((all_t_min >= 16) & (all_t_min <= 25))} de {len(all_t_min)} ({100*np.sum((all_t_min >= 16) & (all_t_min <= 25))/len(all_t_min):.1f}%)")
    
    # Temperaturas máximas
    print(f"\n🌡️  TEMPERATURAS MÁXIMAS:")
    print(f"  • Objetivo: μ={TMAX_MEDIAN}°C, σ={TMAX_SIGMA}, rango=[30°C, 42°C]")
    print(f"  • Obtenido: μ={np.mean(all_t_max):.3f}°C, σ={np.std(all_t_max):.3f}")
    print(f"  • Rango: {np.min(all_t_max):.1f}°C - {np.max(all_t_max):.1f}°C")
    print(f"  • En rango: {np.sum((all_t_max >= 30) & (all_t_max <= 42))} de {len(all_t_max)} ({100*np.sum((all_t_max >= 30) & (all_t_max <= 42))/len(all_t_max):.1f}%)")
    
    # Horarios mínimos
    print(f"\n⏰ HORARIOS DE TEMPERATURAS MÍNIMAS:")
    print(f"  • Objetivo: μ={TMIN_HOUR}:00, σ={TMIN_HOUR_SIGMA*60:.0f} min, rango=[5.5, 6.5]")
    mean_hour_min = np.mean(all_hour_min)
    std_hour_min = np.std(all_hour_min)
    print(f"  • Obtenido: μ={mean_hour_min:.3f} ({int(mean_hour_min)}:{int((mean_hour_min % 1)*60):02d}), σ={std_hour_min*60:.1f} min")
    print(f"  • Rango: {np.min(all_hour_min):.2f} - {np.max(all_hour_min):.2f}")
    print(f"  • En rango: {np.sum((all_hour_min >= 5.5) & (all_hour_min <= 6.5))} de {len(all_hour_min)} ({100*np.sum((all_hour_min >= 5.5) & (all_hour_min <= 6.5))/len(all_hour_min):.1f}%)")
    
    # Horarios máximos
    print(f"\n⏰ HORARIOS DE TEMPERATURAS MÁXIMAS:")
    print(f"  • Objetivo: μ={TMAX_HOUR}:00, σ={TMAX_HOUR_SIGMA*60:.0f} min, rango=[15, 17]")
    mean_hour_max = np.mean(all_hour_max)
    std_hour_max = np.std(all_hour_max)
    print(f"  • Obtenido: μ={mean_hour_max:.3f} ({int(mean_hour_max)}:{int((mean_hour_max % 1)*60):02d}), σ={std_hour_max*60:.1f} min")
    print(f"  • Rango: {np.min(all_hour_max):.2f} - {np.max(all_hour_max):.2f}")
    print(f"  • En rango: {np.sum((all_hour_max >= 15) & (all_hour_max <= 17))} de {len(all_hour_max)} ({100*np.sum((all_hour_max >= 15) & (all_hour_max <= 17))/len(all_hour_max):.1f}%)")
    
    # Crear gráficos de distribución
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # Temperaturas mínimas
    axes[0,0].hist(all_t_min, bins=50, alpha=0.7, density=True, color='blue')
    axes[0,0].axvline(TMIN_MEDIAN, color='red', linestyle='--', label=f'Objetivo: {TMIN_MEDIAN}°C')
    axes[0,0].axvline(np.mean(all_t_min), color='orange', linestyle='-', label=f'Obtenido: {np.mean(all_t_min):.1f}°C')
    axes[0,0].set_title('Distribución de Temperaturas Mínimas')
    axes[0,0].set_xlabel('Temperatura (°C)')
    axes[0,0].legend()
    
    # Temperaturas máximas
    axes[0,1].hist(all_t_max, bins=50, alpha=0.7, density=True, color='red')
    axes[0,1].axvline(TMAX_MEDIAN, color='blue', linestyle='--', label=f'Objetivo: {TMAX_MEDIAN}°C')
    axes[0,1].axvline(np.mean(all_t_max), color='orange', linestyle='-', label=f'Obtenido: {np.mean(all_t_max):.1f}°C')
    axes[0,1].set_title('Distribución de Temperaturas Máximas')
    axes[0,1].set_xlabel('Temperatura (°C)')
    axes[0,1].legend()
    
    # Horarios mínimos
    axes[1,0].hist(all_hour_min, bins=50, alpha=0.7, density=True, color='cyan')
    axes[1,0].axvline(TMIN_HOUR, color='red', linestyle='--', label=f'Objetivo: {TMIN_HOUR}:00')
    axes[1,0].axvline(np.mean(all_hour_min), color='orange', linestyle='-', label=f'Obtenido: {np.mean(all_hour_min):.1f}')
    axes[1,0].set_title('Distribución de Horarios de Temp. Mínimas')
    axes[1,0].set_xlabel('Hora del día')
    axes[1,0].legend()
    
    # Horarios máximos
    axes[1,1].hist(all_hour_max, bins=50, alpha=0.7, density=True, color='orange')
    axes[1,1].axvline(TMAX_HOUR, color='red', linestyle='--', label=f'Objetivo: {TMAX_HOUR}:00')
    axes[1,1].axvline(np.mean(all_hour_max), color='blue', linestyle='-', label=f'Obtenido: {np.mean(all_hour_max):.1f}')
    axes[1,1].set_title('Distribución de Horarios de Temp. Máximas')
    axes[1,1].set_xlabel('Hora del día')
    axes[1,1].legend()
    
    plt.tight_layout()
    plt.savefig('graphs/test_distribuciones_gaussianas.png', dpi=300, bbox_inches='tight')
    print(f"\n📊 Gráfico guardado: graphs/test_distribuciones_gaussianas.png")
    
    # Verificar que las distribuciones son gaussianas
    print(f"\n✅ VERIFICACIÓN DE GAUSSIANAS:")
    
    # Tolerancia para considerar "correcto" (5% de error)
    tol_temp = 0.05
    tol_hora = 0.05
    
    # Temperaturas
    error_tmin_mean = abs(np.mean(all_t_min) - TMIN_MEDIAN) / TMIN_MEDIAN
    error_tmin_std = abs(np.std(all_t_min) - TMIN_SIGMA) / TMIN_SIGMA
    error_tmax_mean = abs(np.mean(all_t_max) - TMAX_MEDIAN) / TMAX_MEDIAN
    error_tmax_std = abs(np.std(all_t_max) - TMAX_SIGMA) / TMAX_SIGMA
    
    # Horarios
    error_hmin_mean = abs(np.mean(all_hour_min) - TMIN_HOUR) / TMIN_HOUR
    error_hmin_std = abs(np.std(all_hour_min) - TMIN_HOUR_SIGMA) / TMIN_HOUR_SIGMA
    error_hmax_mean = abs(np.mean(all_hour_max) - TMAX_HOUR) / TMAX_HOUR
    error_hmax_std = abs(np.std(all_hour_max) - TMAX_HOUR_SIGMA) / TMAX_HOUR_SIGMA
    
    print(f"  • Temp. mínimas - Media: {'✅' if error_tmin_mean < tol_temp else '❌'} (error: {error_tmin_mean*100:.1f}%)")
    print(f"  • Temp. mínimas - Desv.: {'✅' if error_tmin_std < tol_temp else '❌'} (error: {error_tmin_std*100:.1f}%)")
    print(f"  • Temp. máximas - Media: {'✅' if error_tmax_mean < tol_temp else '❌'} (error: {error_tmax_mean*100:.1f}%)")
    print(f"  • Temp. máximas - Desv.: {'✅' if error_tmax_std < tol_temp else '❌'} (error: {error_tmax_std*100:.1f}%)")
    print(f"  • Hora mínimas - Media: {'✅' if error_hmin_mean < tol_hora else '❌'} (error: {error_hmin_mean*100:.1f}%)")
    print(f"  • Hora mínimas - Desv.: {'✅' if error_hmin_std < tol_hora else '❌'} (error: {error_hmin_std*100:.1f}%)")
    print(f"  • Hora máximas - Media: {'✅' if error_hmax_mean < tol_hora else '❌'} (error: {error_hmax_mean*100:.1f}%)")
    print(f"  • Hora máximas - Desv.: {'✅' if error_hmax_std < tol_hora else '❌'} (error: {error_hmax_std*100:.1f}%)")


if __name__ == "__main__":
    print("🧪 Test de Distribuciones Gaussianas")
    print("="*50)
    
    # Crear directorio de gráficos si no existe
    os.makedirs('graphs', exist_ok=True)
    
    test_temperature_distributions(n_samples=1000)
    
    print("\n🎉 Test completado!")
