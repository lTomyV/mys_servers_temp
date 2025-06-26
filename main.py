"""
Simulador principal de análisis de servidores con Monte Carlo.
"""

import sys
import os

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import NUM_SIMULATIONS
from src.simulation.runner import run_monte_carlo_simulation
from src.analysis.statistics import calculate_cost_statistics, calculate_temperature_statistics, compare_strategies
from src.visualization.plots import plot_cost_distribution, plot_temperature_density, print_comparison_table


def print_results(costs, strategy_name):
    """Imprime los resultados de una estrategia."""
    stats = calculate_cost_statistics(costs)
    
    print(f"\n--- Resultados para la estrategia: {strategy_name} ---")
    print(f"Costo Mensual Promedio: ${stats['mean']:.2f}")
    print(f"Desviación Estándar del Costo: ${stats['std']:.2f}")
    print(f"Costo Mediano: ${stats['median']:.2f}")
    print(f"Costo90 (Percentil 90): ${stats['costo90']:.2f}")
    
    return stats


def print_temperature_stats(temp_stats):
    """Imprime estadísticas de temperatura."""
    if temp_stats is None:
        return
    
    print("\n--- Estadísticas de Temperatura por Hora ---")
    print(f"Temperatura mínima registrada: {temp_stats['temp_min']:.1f}°C")
    print(f"Temperatura máxima registrada: {temp_stats['temp_max']:.1f}°C")
    print(f"Hora con temperatura promedio más baja: {temp_stats['min_hour']:02d}:00 "
          f"({temp_stats['hourly_means'][temp_stats['min_hour']]:.2f}°C)")
    print(f"Hora con temperatura promedio más alta: {temp_stats['max_hour']:02d}:00 "
          f"({temp_stats['hourly_means'][temp_stats['max_hour']]:.2f}°C)")
    
    # Agregar información adicional sobre variabilidad
    print(f"Rango de promedios horarios: [{temp_stats['hourly_means'].min():.2f}, "
          f"{temp_stats['hourly_means'].max():.2f}]°C")
    print(f"Variabilidad entre horas: σ = {temp_stats['hourly_means'].std():.2f}°C")
    
    # Mostrar algunos promedios horarios clave para verificar variabilidad
    key_hours = [0, 6, 12, 16, 18, 23]
    print("\nPromedios horarios de muestra:")
    for hour in key_hours:
        print(f"  {hour:02d}:00 → {temp_stats['hourly_means'][hour]:.2f}°C")


def main():
    """Función principal del simulador."""
    print("="*60)
    print("SIMULADOR DE ANÁLISIS DE SERVIDORES - MONTE CARLO")
    print("="*60)
    
    print(f"\nIniciando análisis con {NUM_SIMULATIONS} simulaciones por estrategia...")
    
    # Ejecutar simulaciones para ambas estrategias
    print("\n" + "="*60)
    costs_baseline, temp_profiles_baseline = run_monte_carlo_simulation("LineaBase", NUM_SIMULATIONS)
    results_baseline = print_results(costs_baseline, "Línea Base")
    plot_cost_distribution(costs_baseline, "Línea Base")
    
    print("\n" + "="*60)
    costs_optimized, temp_profiles_optimized = run_monte_carlo_simulation("Optimizado", NUM_SIMULATIONS)
    results_optimized = print_results(costs_optimized, "Optimizada")
    plot_cost_distribution(costs_optimized, "Optimizada")
    
    # Análisis de temperaturas (usar los perfiles de la estrategia base)
    print("\n" + "="*60)
    print("--- Generando análisis de temperaturas ---")
    temp_stats = calculate_temperature_statistics(temp_profiles_baseline)
    print_temperature_stats(temp_stats)
    plot_temperature_density(temp_stats)
    
    # Comparación de estrategias
    print("\n" + "="*60)
    comparison = compare_strategies(results_baseline, results_optimized)
    print_comparison_table(results_baseline, results_optimized, comparison)
    
    print("\n" + "="*60)
    print("ANÁLISIS COMPLETADO")
    print("="*60)
    print("Archivos generados en la carpeta 'graphs/':")
    print("- histograma_costos_Línea Base.png")
    print("- histograma_costos_Optimizada.png") 
    print("- distribucion_temperaturas_horarias.png")


if __name__ == "__main__":
    main()
