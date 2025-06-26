"""
Módulo para generar gráficos y visualizaciones.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from config.settings import FIGURE_SIZE_LARGE, FIGURE_SIZE_MEDIUM, DPI, GRAPHS_DIR, SHOW_PLOTS


def _ensure_graphs_dir():
    """Asegura que el directorio de gráficos existe."""
    if not os.path.exists(GRAPHS_DIR):
        os.makedirs(GRAPHS_DIR)


def _get_graph_path(filename):
    """Obtiene la ruta completa para guardar un gráfico."""
    _ensure_graphs_dir()
    return os.path.join(GRAPHS_DIR, filename)


def _finish_plot():
    """Finaliza un plot: lo muestra si está configurado o lo cierra para liberar memoria."""
    if SHOW_PLOTS:
        plt.show()
    else:
        plt.close()


def plot_cost_distribution(costs, strategy_name):
    """Crea un histograma de distribución de costos."""
    mean_cost = np.mean(costs)
    costo_90 = np.percentile(costs, 90)
    
    plt.figure(figsize=FIGURE_SIZE_MEDIUM)
    plt.hist(costs, bins=50, density=True, alpha=0.7, label=f'Distribución de Costos ({strategy_name})')
    plt.axvline(mean_cost, color='red', linestyle='dashed', linewidth=2, 
                label=f'Costo Promedio (${mean_cost:.2f})')
    plt.axvline(costo_90, color='purple', linestyle='dashed', linewidth=2, 
                label=f'Costo90 (${costo_90:.2f})')
    plt.title(f'Distribución de Probabilidad del Costo Mensual - Estrategia {strategy_name}')
    plt.xlabel('Costo Mensual (U$D)')
    plt.ylabel('Densidad de Probabilidad')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(_get_graph_path(f'histograma_costos_{strategy_name}.png'), dpi=DPI, bbox_inches='tight')
    _finish_plot()  # Cerrar la figura para liberar memoria


def plot_temperature_density(temp_stats):
    """Crea un gráfico de densidad de temperaturas por hora del día."""
    if temp_stats is None:
        print("No hay datos de temperatura para graficar.")
        return
    
    hourly_temps = temp_stats["hourly_temps"]
    hourly_means = temp_stats["hourly_means"]
    hourly_p25 = temp_stats["hourly_p25"]
    hourly_p75 = temp_stats["hourly_p75"]
    temp_min = temp_stats["temp_min"]
    temp_max = temp_stats["temp_max"]
    
    # Crear el gráfico de densidad
    plt.figure(figsize=FIGURE_SIZE_LARGE)
    
    # Crear arrays para el mapa de calor
    hours = np.arange(0, 24)
    temp_bins = np.linspace(temp_min - 1, temp_max + 1, 100)
    
    # Crear matriz de densidad
    density_matrix = np.zeros((len(temp_bins)-1, len(hours)))
    
    for i, hour in enumerate(hours):
        hour_temps = hourly_temps[hour, :]
        hist, _ = np.histogram(hour_temps, bins=temp_bins, density=True)
        density_matrix[:, i] = hist
    
    # Crear el mapa de calor
    X, Y = np.meshgrid(hours, temp_bins[:-1])
    
    plt.contourf(X, Y, density_matrix, levels=50, cmap='Reds', alpha=0.8)
    plt.colorbar(label='Densidad de Probabilidad')
    
    # Agregar líneas de estadísticas
    plt.plot(hours, hourly_means, 'cyan', linewidth=3, label='Temperatura Promedio')
    plt.plot(hours, hourly_p25, 'lightblue', linewidth=2, linestyle='--', label='Percentil 25')
    plt.plot(hours, hourly_p75, 'lightblue', linewidth=2, linestyle='--', label='Percentil 75')
    
    plt.xlabel('Hora del Día')
    plt.ylabel('Temperatura (°C)')
    plt.title('Distribución de Temperaturas por Hora del Día\n(Áreas más oscuras = mayor frecuencia)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(range(0, 24, 2))
    
    # Configurar etiquetas del eje X para mostrar formato de hora
    hour_labels = [f'{h:02d}:00' for h in range(0, 24, 2)]
    plt.gca().set_xticklabels(hour_labels)
    
    plt.tight_layout()
    plt.savefig(_get_graph_path('distribucion_temperaturas_horarias.png'), dpi=DPI, bbox_inches='tight')
    _finish_plot()  # Cerrar la figura para liberar memoria


def print_comparison_table(results_baseline, results_optimized, comparison):
    """Imprime tabla comparativa de resultados."""
    print("\n\n--- Tabla Comparativa de Resultados ---")
    print(f"{'Métrica':<25} {'Línea Base':<15} {'Optimizada':<15} {'Mejora (%)':<15}")
    print("-" * 70)
    
    print(f"{'Costo Promedio (U$D)':<25} ${results_baseline['mean']:.2f}{'':<7} "
          f"${results_optimized['mean']:.2f}{'':<7} {comparison['mean_improvement']:.2f}%")
    print(f"{'Costo90 (U$D)':<25} ${results_baseline['costo90']:.2f}{'':<7} "
          f"${results_optimized['costo90']:.2f}{'':<7} {comparison['costo90_improvement']:.2f}%")
    print("-" * 70)
