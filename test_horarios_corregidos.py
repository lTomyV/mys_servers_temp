"""
Test para verificar que los horarios de temperaturas extremas estén en los rangos correctos.
- Temperatura mínima: 5.5 a 6.5 horas
- Temperatura máxima: 15 a 17 horas  
"""

import numpy as np
import matplotlib.pyplot as plt
from src.weather.generator import generate_daily_extremes
from config.settings import GRAPHS_DIR
import os

def test_rangos_horarios():
    """Genera una muestra grande y verifica que los horarios estén en los rangos correctos."""
    print("🧪 Probando rangos de horarios de temperaturas extremas...")
    
    # Generar una muestra grande para estadísticas robustas
    num_samples = 5000
    t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_daily_extremes(num_samples)
    
    # Verificar rangos
    tmin_in_range = np.sum((hour_min_daily >= 5.5) & (hour_min_daily <= 6.5))
    tmax_in_range = np.sum((hour_max_daily >= 15.0) & (hour_max_daily <= 17.0))
    
    tmin_percentage = (tmin_in_range / num_samples) * 100
    tmax_percentage = (tmax_in_range / num_samples) * 100
    
    print(f"📊 Resultados de {num_samples} muestras:")
    print(f"  Temperaturas mínimas en rango [5.5, 6.5]: {tmin_in_range}/{num_samples} ({tmin_percentage:.1f}%)")
    print(f"  Temperaturas máximas en rango [15.0, 17.0]: {tmax_in_range}/{num_samples} ({tmax_percentage:.1f}%)")
    
    # Estadísticas detalladas
    print(f"\n📈 Estadísticas de horarios:")
    print(f"  Hora mín - Media: {np.mean(hour_min_daily):.2f}, Desv: {np.std(hour_min_daily):.3f}")
    print(f"  Hora mín - Rango: [{np.min(hour_min_daily):.2f}, {np.max(hour_min_daily):.2f}]")
    print(f"  Hora máx - Media: {np.mean(hour_max_daily):.2f}, Desv: {np.std(hour_max_daily):.3f}")
    print(f"  Hora máx - Rango: [{np.min(hour_max_daily):.2f}, {np.max(hour_max_daily):.2f}]")
    
    # Crear gráficos
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Histograma de horarios de temperatura mínima
    ax1.hist(hour_min_daily, bins=50, alpha=0.7, color='blue', edgecolor='black')
    ax1.axvline(5.5, color='red', linestyle='--', label='Límite inferior (5.5)')
    ax1.axvline(6.5, color='red', linestyle='--', label='Límite superior (6.5)')
    ax1.axvline(6.0, color='green', linestyle='-', label='Centro (6.0)')
    ax1.set_xlabel('Hora del día')
    ax1.set_ylabel('Frecuencia')
    ax1.set_title('Distribución de Horarios de Temperatura Mínima')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Histograma de horarios de temperatura máxima
    ax2.hist(hour_max_daily, bins=50, alpha=0.7, color='red', edgecolor='black')
    ax2.axvline(15.0, color='blue', linestyle='--', label='Límite inferior (15.0)')
    ax2.axvline(17.0, color='blue', linestyle='--', label='Límite superior (17.0)')
    ax2.axvline(16.0, color='green', linestyle='-', label='Centro (16.0)')
    ax2.set_xlabel('Hora del día')
    ax2.set_ylabel('Frecuencia')
    ax2.set_title('Distribución de Horarios de Temperatura Máxima')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Histograma de temperaturas mínimas
    ax3.hist(t_min_daily, bins=50, alpha=0.7, color='lightblue', edgecolor='black')
    ax3.axvline(21, color='green', linestyle='-', label='Mediana (21°C)')
    ax3.set_xlabel('Temperatura (°C)')
    ax3.set_ylabel('Frecuencia')
    ax3.set_title('Distribución de Temperaturas Mínimas')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Histograma de temperaturas máximas
    ax4.hist(t_max_daily, bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
    ax4.axvline(37, color='green', linestyle='-', label='Mediana (37°C)')
    ax4.set_xlabel('Temperatura (°C)')
    ax4.set_ylabel('Frecuencia')
    ax4.set_title('Distribución de Temperaturas Máximas')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Guardar gráfico
    if not os.path.exists(GRAPHS_DIR):
        os.makedirs(GRAPHS_DIR)
    
    output_path = os.path.join(GRAPHS_DIR, "test_horarios_corregidos.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"💾 Gráfico guardado: {output_path}")
    
    plt.show()
    
    # Verificación de éxito
    if tmin_percentage >= 95 and tmax_percentage >= 95:
        print("\n✅ ¡TEST EXITOSO! Los horarios están en los rangos correctos")
    else:
        print("\n❌ TEST FALLIDO: Los horarios no están en los rangos esperados")
        print("   Revisa los parámetros de configuración")
    
    return tmin_percentage, tmax_percentage

if __name__ == "__main__":
    test_rangos_horarios()
