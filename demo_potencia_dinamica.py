"""
Demostración de la potencia de refrigeración dinámica.
Este script muestra cómo la potencia varía hora por hora según las condiciones.
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.weather.generator import generate_weather_profile, generate_hourly_temperature_profile
from src.modelica.interface import ModelicaInterface
from pathlib import Path


def demo_dynamic_cooling():
    """Demuestra la potencia de refrigeración dinámica."""
    
    print("🔄 DEMOSTRACIÓN DE POTENCIA DE REFRIGERACIÓN DINÁMICA")
    print("="*60)
    
    # Generar perfil de temperatura de un día típico
    t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_weather_profile()
    
    # Usar el primer día generado
    daily_profile = {
        'min_temp': t_min_daily[0],
        'max_temp': t_max_daily[0], 
        'min_temp_hour': hour_min_daily[0],
        'max_temp_hour': hour_max_daily[0],
    }
    
    print(f"Perfil del día:")
    print(f"  Temperatura mínima: {daily_profile['min_temp']:.1f}°C a las {daily_profile['min_temp_hour']:.1f}h")
    print(f"  Temperatura máxima: {daily_profile['max_temp']:.1f}°C a las {daily_profile['max_temp_hour']:.1f}h")
    
    # Crear vector de tiempo (24 horas, cada 5 minutos)
    time_hours = np.linspace(0, 24, 24*12+1)  # Cada 5 minutos
    time_seconds = time_hours * 3600
    
    # Generar perfil de temperatura horario
    hourly_temps = generate_hourly_temperature_profile(
        [daily_profile['min_temp']], 
        [daily_profile['max_temp']], 
        [daily_profile['min_temp_hour']], 
        [daily_profile['max_temp_hour']]
    )
    
    # Interpolar para obtener temperaturas cada 5 minutos
    temp_profile = np.interp(time_hours, np.linspace(0, 24, len(hourly_temps)), hourly_temps)
    
    # Configurar interfaz de Modelica
    model_path = Path(__file__).parent / 'src' / 'modelica' / 'temperatura_servidor.mo'
    interface = ModelicaInterface(str(model_path))
    
    # Ejecutar simulación con control dinámico
    print("\nEjecutando simulación con control dinámico...")
    results = interface.optimize_cooling_power(temp_profile, time_seconds)
    
    # Mostrar estadísticas
    print(f"\n📊 RESULTADOS DE LA SIMULACIÓN:")
    print(f"  Temperatura máxima de carcasa: {results['max_case_temp']:.1f}°C")
    print(f"  Potencia promedio: {np.mean(results['cooling_power']):.0f}W")
    print(f"  Potencia mínima: {np.min(results['cooling_power']):.0f}W")
    print(f"  Potencia máxima: {np.max(results['cooling_power']):.0f}W")
    print(f"  Energía total: {results['total_energy']:.2f} kWh")
    
    # Crear gráfico detallado
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Potencia de Refrigeración Dinámica - Análisis Detallado', fontsize=16, fontweight='bold')
    
    # Gráfico 1: Temperatura exterior y potencia
    ax1 = axes[0, 0]
    ax1_twin = ax1.twinx()
    
    line1 = ax1.plot(time_hours, temp_profile, 'r-', linewidth=2, label='Temperatura Exterior')
    line2 = ax1_twin.plot(time_hours, results['cooling_power'], 'b-', linewidth=2, label='Potencia Refrigeración')
    
    ax1.set_xlabel('Hora del Día')
    ax1.set_ylabel('Temperatura Exterior (°C)', color='red')
    ax1_twin.set_ylabel('Potencia Refrigeración (W)', color='blue')
    ax1.tick_params(axis='y', labelcolor='red')
    ax1_twin.tick_params(axis='y', labelcolor='blue')
    ax1.grid(True, alpha=0.3)
    ax1.set_title('Temperatura Exterior vs Potencia de Refrigeración')
    
    # Crear leyenda combinada
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    
    # Gráfico 2: Temperaturas del sistema
    ax2 = axes[0, 1]
    ax2.plot(time_hours, results['T_server'], 'g-', linewidth=2, label='Temperatura Servidor')
    ax2.plot(time_hours, results['T_case'], 'orange', linewidth=2, label='Temperatura Carcasa')
    ax2.axhline(y=25.0, color='red', linestyle='--', linewidth=2, label='Límite 25°C')
    ax2.set_xlabel('Hora del Día')
    ax2.set_ylabel('Temperatura (°C)')
    ax2.set_title('Temperaturas del Sistema')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Gráfico 3: Distribución de potencia
    ax3 = axes[1, 0]
    ax3.hist(results['cooling_power'], bins=30, density=True, alpha=0.7, color='blue', edgecolor='black')
    ax3.axvline(x=np.mean(results['cooling_power']), color='red', linestyle='--', 
                label=f'Promedio: {np.mean(results["cooling_power"]):.0f}W')
    ax3.axvline(x=np.median(results['cooling_power']), color='orange', linestyle='--', 
                label=f'Mediana: {np.median(results["cooling_power"]):.0f}W')
    ax3.set_xlabel('Potencia de Refrigeración (W)')
    ax3.set_ylabel('Densidad de Probabilidad')
    ax3.set_title('Distribución de Potencia Durante el Día')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Gráfico 4: Correlación temperatura-potencia
    ax4 = axes[1, 1]
    scatter = ax4.scatter(temp_profile, results['cooling_power'], 
                         c=time_hours, cmap='viridis', alpha=0.6, s=20)
    
    # Ajuste lineal
    z = np.polyfit(temp_profile, results['cooling_power'], 1)
    p = np.poly1d(z)
    temp_range = np.linspace(min(temp_profile), max(temp_profile), 100)
    ax4.plot(temp_range, p(temp_range), "r--", alpha=0.8, linewidth=2,
             label=f'Tendencia: {z[0]:.1f}W/°C')
    
    ax4.set_xlabel('Temperatura Exterior (°C)')
    ax4.set_ylabel('Potencia de Refrigeración (W)')
    ax4.set_title('Correlación: Temperatura vs Potencia')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # Barra de color para el tiempo
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('Hora del Día')
    
    plt.tight_layout()
    
    # Guardar gráfico
    os.makedirs('graphs', exist_ok=True)
    plt.savefig('graphs/potencia_dinamica_detallada.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Crear gráfico de comparación con potencia constante
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('Comparación: Potencia Dinámica vs Constante', fontsize=16, fontweight='bold')
    
    # Simulación con potencia constante para comparación
    results_constant = interface.simulate_server_temperature(
        temp_profile, time_seconds, cooling_power=np.mean(results['cooling_power'])
    )
    
    # Gráfico superior: Potencias
    ax1 = axes[0]
    ax1_twin = ax1.twinx()
    
    line1 = ax1.plot(time_hours, temp_profile, 'k-', linewidth=2, alpha=0.7, label='Temperatura Exterior')
    line2 = ax1_twin.plot(time_hours, results['cooling_power'], 'b-', linewidth=3, label='Potencia Dinámica')
    line3 = ax1_twin.axhline(y=np.mean(results['cooling_power']), color='red', linestyle='--', 
                            linewidth=3, label='Potencia Constante')
    
    ax1.set_ylabel('Temperatura Exterior (°C)')
    ax1_twin.set_ylabel('Potencia de Refrigeración (W)')
    ax1.set_title('Comparación de Estrategias de Control')
    
    # Leyenda combinada
    lines = line1 + line2 + [line3]
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Gráfico inferior: Temperaturas resultantes
    ax2 = axes[1]
    ax2.plot(time_hours, results['T_case'], 'b-', linewidth=3, label='Carcasa - Control Dinámico')
    ax2.plot(time_hours, results_constant['T_case'], 'r--', linewidth=3, label='Carcasa - Control Constante')
    ax2.axhline(y=25.0, color='black', linestyle=':', linewidth=2, label='Límite 25°C')
    
    ax2.set_xlabel('Hora del Día')
    ax2.set_ylabel('Temperatura de Carcasa (°C)')
    ax2.set_title('Comparación de Temperaturas Resultantes')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('graphs/comparacion_control_dinamico.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Mostrar comparación de energía
    energy_dynamic = results['total_energy']
    energy_constant = results_constant['total_energy']
    energy_savings = energy_constant - energy_dynamic
    
    print(f"\n💡 COMPARACIÓN ENERGÉTICA:")
    print(f"  Control Dinámico: {energy_dynamic:.2f} kWh")
    print(f"  Control Constante: {energy_constant:.2f} kWh")
    print(f"  Ahorro energético: {energy_savings:.2f} kWh ({energy_savings/energy_constant*100:.1f}%)")
    
    print(f"\n📁 ARCHIVOS GENERADOS:")
    print(f"  graphs/potencia_dinamica_detallada.png")
    print(f"  graphs/comparacion_control_dinamico.png")
    
    return results


if __name__ == "__main__":
    demo_dynamic_cooling()
