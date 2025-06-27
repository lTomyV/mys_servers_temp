"""
Script para verificar que las distribuciones de temperatura están correctas.
"""
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Agregar el directorio raíz al path
sys.path.append('.')

from src.weather.generator import generate_weather_profile, generate_hourly_temperature_profile
from config.settings import TMIN_MEDIAN, TMAX_MEDIAN, TMIN_SIGMA, TMAX_SIGMA

def test_distribuciones_temperatura():
    """Prueba las distribuciones de temperatura para verificar que sean correctas."""
    
    print("🧪 Probando distribuciones de temperatura...")
    print(f"Parámetros configurados:")
    print(f"  T_min: μ={TMIN_MEDIAN}°C, σ={TMIN_SIGMA}°C")
    print(f"  T_max: μ={TMAX_MEDIAN}°C, σ={TMAX_SIGMA}°C")
    
    # Generar muchas muestras para verificar la distribución
    n_muestras = 1000
    t_mins = []
    t_maxs = []
    
    for i in range(n_muestras):
        t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_weather_profile()
        t_mins.extend(t_min_daily)
        t_maxs.extend(t_max_daily)
    
    t_mins = np.array(t_mins)
    t_maxs = np.array(t_maxs)
    
    print(f"\nResultados de {n_muestras * 31} muestras:")
    print(f"T_min - Media: {np.mean(t_mins):.2f}°C (esperado: {TMIN_MEDIAN}°C)")
    print(f"T_min - Desv.Est: {np.std(t_mins):.3f}°C (esperado: {TMIN_SIGMA}°C)")
    print(f"T_min - Rango: {np.min(t_mins):.1f}°C - {np.max(t_mins):.1f}°C")
    
    print(f"T_max - Media: {np.mean(t_maxs):.2f}°C (esperado: {TMAX_MEDIAN}°C)")
    print(f"T_max - Desv.Est: {np.std(t_maxs):.3f}°C (esperado: {TMAX_SIGMA}°C)")
    print(f"T_max - Rango: {np.min(t_maxs):.1f}°C - {np.max(t_maxs):.1f}°C")
    
    # Crear histogramas
    plt.figure(figsize=(15, 6))
    
    plt.subplot(1, 2, 1)
    plt.hist(t_mins, bins=50, alpha=0.7, color='blue', density=True)
    plt.axvline(TMIN_MEDIAN, color='red', linestyle='--', label=f'Mediana esperada: {TMIN_MEDIAN}°C')
    plt.axvline(np.mean(t_mins), color='orange', linestyle='--', label=f'Media obtenida: {np.mean(t_mins):.1f}°C')
    plt.title('Distribución de Temperaturas Mínimas')
    plt.xlabel('Temperatura (°C)')
    plt.ylabel('Densidad')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    plt.hist(t_maxs, bins=50, alpha=0.7, color='red', density=True)
    plt.axvline(TMAX_MEDIAN, color='blue', linestyle='--', label=f'Mediana esperada: {TMAX_MEDIAN}°C')
    plt.axvline(np.mean(t_maxs), color='orange', linestyle='--', label=f'Media obtenida: {np.mean(t_maxs):.1f}°C')
    plt.title('Distribución de Temperaturas Máximas')
    plt.xlabel('Temperatura (°C)')
    plt.ylabel('Densidad')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('graphs/test_distribuciones_temperatura.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Gráfico guardado: graphs/test_distribuciones_temperatura.png")
    
    # Verificar tolerancias
    error_min_media = abs(np.mean(t_mins) - TMIN_MEDIAN)
    error_max_media = abs(np.mean(t_maxs) - TMAX_MEDIAN)
    error_min_sigma = abs(np.std(t_mins) - TMIN_SIGMA)
    error_max_sigma = abs(np.std(t_maxs) - TMAX_SIGMA)
    
    if error_min_media < 0.5 and error_max_media < 0.5:
        print("✅ Medias correctas")
    else:
        print(f"❌ Error en medias: T_min={error_min_media:.2f}, T_max={error_max_media:.2f}")
    
    if error_min_sigma < 0.2 and error_max_sigma < 0.2:
        print("✅ Desviaciones estándar correctas")
    else:
        print(f"❌ Error en desviaciones: T_min={error_min_sigma:.3f}, T_max={error_max_sigma:.3f}")

def test_perfil_horario():
    """Prueba un perfil horario específico."""
    print(f"\n🧪 Probando perfil horario de un día...")
    
    # Generar un perfil para prueba
    t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_weather_profile()
    
    # Tomar el primer día
    temps_horarias = generate_hourly_temperature_profile(t_min_daily[:1], t_max_daily[:1], 
                                                       hour_min_daily[:1], hour_max_daily[:1])
    
    print(f"Día de prueba:")
    print(f"  T_min: {t_min_daily[0]:.1f}°C a las {hour_min_daily[0]:.1f}h")
    print(f"  T_max: {t_max_daily[0]:.1f}°C a las {hour_max_daily[0]:.1f}h")
    print(f"  Rango horario: {np.min(temps_horarias):.1f}°C - {np.max(temps_horarias):.1f}°C")
    
    # Graficar
    plt.figure(figsize=(12, 6))
    hours = np.arange(24)
    plt.plot(hours, temps_horarias, 'b-', linewidth=2, label='Perfil de temperatura')
    plt.scatter([hour_min_daily[0]], [t_min_daily[0]], color='blue', s=100, label=f'T_min: {t_min_daily[0]:.1f}°C')
    plt.scatter([hour_max_daily[0]], [t_max_daily[0]], color='red', s=100, label=f'T_max: {t_max_daily[0]:.1f}°C')
    
    plt.xlabel('Hora del día')
    plt.ylabel('Temperatura (°C)')
    plt.title('Perfil de Temperatura Horario - Día de Prueba')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(range(0, 24, 2))
    plt.savefig('graphs/test_perfil_horario.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Gráfico guardado: graphs/test_perfil_horario.png")

if __name__ == "__main__":
    os.makedirs('graphs', exist_ok=True)
    test_distribuciones_temperatura()
    test_perfil_horario()
    print(f"\n🎉 Pruebas completadas. Revisa los gráficos en la carpeta graphs/")
