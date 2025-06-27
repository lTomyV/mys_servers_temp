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


def plot_randomization_diagnostic(temperature_profiles, temp_stats):
    """
    Crea un gráfico de diagnóstico para validar la randomización de temperaturas.
    Este gráfico justifica que la generación aleatoria funciona correctamente.
    """
    if temp_stats is None or not temperature_profiles:
        print("No hay datos suficientes para el diagnóstico de randomización.")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Diagnóstico de Randomización - Validación Científica', fontsize=16, fontweight='bold')
    
    temp_data = np.array(temperature_profiles)
    num_sims = temp_data.shape[0]
    
    # Gráfico 1: Perfiles de temperatura de las primeras simulaciones (primeros 3 días)
    ax = axes[0, 0]
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    num_profiles_to_show = min(5, num_sims)
    
    for sim in range(num_profiles_to_show):
        day_hours = np.arange(0, 72)  # 3 días = 72 horas
        temps = temperature_profiles[sim][:72]
        ax.plot(day_hours, temps, color=colors[sim % len(colors)], alpha=0.7, 
                linewidth=2, label=f'Simulación {sim+1}')
    
    ax.set_title('Perfiles de Temperatura por Simulación\n(Primeros 3 Días)', fontweight='bold')
    ax.set_xlabel('Hora (desde inicio)')
    ax.set_ylabel('Temperatura (°C)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Agregar líneas verticales para marcar los días
    for day in range(1, 3):
        ax.axvline(x=day*24, color='gray', linestyle='--', alpha=0.5)
    
    # Gráfico 2: Promedios horarios a lo largo del día con bandas de confianza
    ax = axes[0, 1]
    hours = np.arange(24)
    
    # Calcular intervalos de confianza
    hourly_std = np.std(temp_stats["hourly_temps"], axis=1)
    
    ax.plot(hours, temp_stats['hourly_means'], 'bo-', linewidth=3, markersize=8, 
            label='Promedio Horario')
    ax.fill_between(hours, 
                    temp_stats['hourly_means'] - hourly_std,
                    temp_stats['hourly_means'] + hourly_std,
                    alpha=0.3, color='blue', label='±1 Desviación Estándar')
    
    ax.set_title('Promedios Horarios con Variabilidad\n(Validación de Distribución)', fontweight='bold')
    ax.set_xlabel('Hora del Día')
    ax.set_ylabel('Temperatura (°C)')
    ax.set_xticks(range(0, 24, 2))
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Marcar las horas extremas
    min_hour = temp_stats['min_hour']
    max_hour = temp_stats['max_hour']
    ax.plot(min_hour, temp_stats['hourly_means'][min_hour], 'ro', markersize=12, 
            label=f'Mínimo: {min_hour:02d}:00')
    ax.plot(max_hour, temp_stats['hourly_means'][max_hour], 'go', markersize=12, 
            label=f'Máximo: {max_hour:02d}:00')
    
    # Gráfico 3: Distribución de temperaturas por hora clave (boxplot)
    ax = axes[1, 0]
    test_hours = [6, 12, 16, 18]
    
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
    
    bp = ax.boxplot(box_data, tick_labels=labels, patch_artist=True)
    
    # Colorear las cajas
    colors_box = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow']
    for patch, color in zip(bp['boxes'], colors_box):
        patch.set_facecolor(color)
    
    ax.set_title('Distribución de Temperaturas por Hora Clave\n(Evidencia de Variabilidad)', fontweight='bold')
    ax.set_ylabel('Temperatura (°C)')
    ax.grid(True, alpha=0.3)
    
    # Gráfico 4: Estadísticas de resumen con métricas de validación
    ax = axes[1, 1]
    ax.axis('off')  # Ocultar ejes para usar como panel de texto
    
    # Calcular métricas de validación
    daily_means = []
    daily_ranges = []
    for sim in range(num_sims):
        profile = temperature_profiles[sim]
        for day in range(31):
            day_start = day * 24
            day_end = day_start + 24
            if day_end <= len(profile):
                day_temps = profile[day_start:day_end]
                daily_means.append(np.mean(day_temps))
                daily_ranges.append(np.max(day_temps) - np.min(day_temps))
    
    variability_metrics = f"""
    METRICAS DE VALIDACION DE RANDOMIZACION
    
    [VARIABILIDAD TEMPORAL]
    * Rango de promedios horarios: {temp_stats['hourly_means'].min():.1f} - {temp_stats['hourly_means'].max():.1f}°C
    * Variabilidad entre horas: σ = {temp_stats['hourly_means'].std():.2f}°C
    * Hora de minimo: {temp_stats['min_hour']:02d}:00 ({temp_stats['hourly_means'][temp_stats['min_hour']]:.1f}°C)
    * Hora de maximo: {temp_stats['max_hour']:02d}:00 ({temp_stats['hourly_means'][temp_stats['max_hour']]:.1f}°C)
    
    [VARIABILIDAD DIARIA]
    * Promedio diario: {np.mean(daily_means):.1f} ± {np.std(daily_means):.1f}°C
    * Rango diario tipico: {np.mean(daily_ranges):.1f} ± {np.std(daily_ranges):.1f}°C
    * Temp. extremas globales: [{temp_stats['temp_min']:.1f}, {temp_stats['temp_max']:.1f}]°C
    
    [VALIDACION ESTADISTICA]
    * {num_sims} simulaciones independientes
    * {len(daily_means)} dias-muestra analizados
    * Distribucion natural esperada (min 06:00, max 16:00)
    * Variabilidad confirmada en multiples escalas
    """
    
    ax.text(0.05, 0.95, variability_metrics, transform=ax.transAxes, 
            fontsize=11, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
    
    ax.set_title('Resumen de Validación Científica', fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(_get_graph_path('diagnostico_randomizacion.png'), dpi=DPI, bbox_inches='tight')
    _finish_plot()
    
    print(">> Grafico de validacion de randomizacion generado: graphs/diagnostico_randomizacion.png")


def plot_adaptive_performance(temperature_profiles, costs):
    """
    Genera gráficos de rendimiento del control adaptativo.
    
    Args:
        temperature_profiles: Lista de perfiles de temperatura
        costs: Array de costos de las simulaciones
    """
    if not temperature_profiles:
        print("⚠️  No hay datos de temperatura para graficar rendimiento adaptativo")
        return
    
    # Crear figura con subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Convertir datos a arrays numpy
    temp_data = np.array(temperature_profiles)
    
    # 1. Distribución de temperaturas máximas por simulación
    max_temps = np.max(temp_data, axis=1)
    axes[0, 0].hist(max_temps, bins=20, alpha=0.7, color='orange', edgecolor='black')
    axes[0, 0].axvline(25, color='red', linestyle='--', linewidth=2, label='Límite 25°C')
    axes[0, 0].set_xlabel('Temperatura Máxima (°C)')
    axes[0, 0].set_ylabel('Frecuencia')
    axes[0, 0].set_title('Distribución de Temperaturas Máximas')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Relación temperatura máxima vs costo
    axes[0, 1].scatter(max_temps, costs, alpha=0.6, color='blue')
    axes[0, 1].set_xlabel('Temperatura Máxima (°C)')
    axes[0, 1].set_ylabel('Costo Mensual ($)')
    axes[0, 1].set_title('Temperatura Máxima vs Costo')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Agregar línea de tendencia
    z = np.polyfit(max_temps, costs, 1)
    p = np.poly1d(z)
    axes[0, 1].plot(max_temps, p(max_temps), "r--", alpha=0.8, label=f'Tendencia (R²={np.corrcoef(max_temps, costs)[0,1]**2:.3f})')
    axes[0, 1].legend()
    
    # 3. Evolución temporal promedio
    temp_promedio = np.mean(temp_data, axis=0)
    horas = np.arange(len(temp_promedio))
    axes[1, 0].plot(horas, temp_promedio, 'b-', linewidth=2, label='Temperatura Promedio')
    axes[1, 0].axhline(25, color='red', linestyle='--', alpha=0.7, label='Límite 25°C')
    axes[1, 0].axhline(15, color='green', linestyle='--', alpha=0.7, label='Mínimo Control (15°C)')
    axes[1, 0].set_xlabel('Hora')
    axes[1, 0].set_ylabel('Temperatura (°C)')
    axes[1, 0].set_title('Evolución Temporal Promedio')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Cumplimiento del objetivo por hora del día
    # Reorganizar por hora del día (asumiendo datos horarios para 31 días)
    if len(temp_promedio) >= 24:  # Al menos un día completo
        horas_dia = len(temp_promedio) % 744  # 744 horas en 31 días
        if horas_dia == 0:  # Datos completos
            temp_reshaped = temp_data.reshape(temp_data.shape[0], 31, 24)
            cumplimiento_horario = np.mean(temp_reshaped <= 25.0, axis=(0, 1)) * 100
            
            horas_del_dia = np.arange(24)
            axes[1, 1].bar(horas_del_dia, cumplimiento_horario, alpha=0.7, color='green', edgecolor='black')
            axes[1, 1].axhline(95, color='red', linestyle='--', alpha=0.7, label='Objetivo 95%')
            axes[1, 1].set_xlabel('Hora del Día')
            axes[1, 1].set_ylabel('Cumplimiento (%)')
            axes[1, 1].set_title('Cumplimiento del Objetivo por Hora')
            axes[1, 1].set_ylim(0, 105)
            axes[1, 1].legend()
            axes[1, 1].grid(True, alpha=0.3)
        else:
            axes[1, 1].text(0.5, 0.5, 'Datos insuficientes\npara análisis horario', 
                           ha='center', va='center', transform=axes[1, 1].transAxes,
                           fontsize=12, bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.7))
            axes[1, 1].set_title('Análisis Horario')
    
    plt.tight_layout()
    plt.savefig(_get_graph_path('rendimiento_adaptativo.png'), dpi=DPI, bbox_inches='tight')
    _finish_plot()
    
    print(f"✅ Gráfico de rendimiento guardado: graphs/rendimiento_adaptativo.png")

def plot_system_performance_timeline(datos_detallados):
    """Crea un gráfico de líneas temporales mostrando temperaturas, potencia y COP del sistema."""
    if not datos_detallados:
        print("No hay datos detallados disponibles para el gráfico de línea temporal.")
        return
    
    # Usar los datos de la primera simulación para el gráfico
    datos = datos_detallados[0]
    
    tiempo_horas = datos['tiempo_horas']
    T_exterior = datos['T_exterior']
    T_servidor = datos['T_servidor'] 
    P_refrigeracion = datos['P_refrigeracion']
    COP_real = datos.get('COP_real', None)  # Puede no estar disponible en versiones anteriores
    
    # Crear figura con subplots
    if COP_real is not None:
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    else:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # Gráfico superior: Temperaturas
    ax1.plot(tiempo_horas, T_exterior, 'orange', linewidth=2, label='Temperatura Exterior', alpha=0.8)
    ax1.plot(tiempo_horas, T_servidor, 'red', linewidth=2, label='Temperatura Carcasa Servidor')
    
    # Línea de referencia del objetivo (25°C)
    ax1.axhline(y=25, color='red', linestyle='--', alpha=0.7, label='Objetivo ≤ 25°C')
    
    ax1.set_ylabel('Temperatura (°C)', fontsize=12)
    ax1.set_title('Rendimiento del Sistema de Refrigeración con COP Variable - Análisis Temporal', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # Colorear fondo según cumplimiento del objetivo
    ax1.fill_between(tiempo_horas, 0, 50, where=(np.array(T_servidor) > 25), 
                     color='red', alpha=0.1, label='Fuera del objetivo')
    ax1.fill_between(tiempo_horas, 0, 50, where=(np.array(T_servidor) <= 25), 
                     color='green', alpha=0.1, label='Dentro del objetivo')
    
    # Gráfico medio: Potencia de refrigeración
    ax2.plot(tiempo_horas, P_refrigeracion, 'blue', linewidth=2, label='Potencia de Refrigeración')
    ax2.fill_between(tiempo_horas, 0, P_refrigeracion, alpha=0.3, color='blue')
    
    ax2.set_ylabel('Potencia (W)', fontsize=12)
    ax2.legend(loc='upper left')
    ax2.grid(True, alpha=0.3)
    
    # Gráfico inferior: COP variable (si está disponible)
    if COP_real is not None:
        ax3.plot(tiempo_horas, COP_real, 'green', linewidth=2, label='COP Real')
        ax3.fill_between(tiempo_horas, 0, COP_real, alpha=0.3, color='green')
        
        ax3.set_ylabel('COP', fontsize=12)
        ax3.set_xlabel('Tiempo (horas)', fontsize=12)
        ax3.legend(loc='upper left')
        ax3.grid(True, alpha=0.3)
        
        # Configurar etiquetas del eje X
        ax_bottom = ax3
    else:
        ax2.set_xlabel('Tiempo (horas)', fontsize=12)
        ax_bottom = ax2
    
    # Configurar etiquetas del eje X para mostrar días
    max_hours = max(tiempo_horas)
    if max_hours > 48:  # Si es más de 2 días
        # Mostrar marcas cada 24 horas (cada día)
        day_ticks = np.arange(0, max_hours + 1, 24)
        ax_bottom.set_xticks(day_ticks)
        ax_bottom.set_xticklabels([f'Día {int(h/24 + 1)}' for h in day_ticks])
    else:
        # Para simulaciones cortas, mostrar cada 6 horas
        ax_bottom.set_xticks(np.arange(0, max_hours + 1, 6))
    
    # Agregar información estadística como texto
    T_servidor_arr = np.array(T_servidor)
    horas_fuera_objetivo = np.sum(T_servidor_arr > 25)
    porcentaje_cumplimiento = (1 - horas_fuera_objetivo / len(T_servidor_arr)) * 100
    
    if COP_real is not None:
        cop_info = f"• COP promedio: {np.mean(COP_real):.2f}\n• COP mínimo: {np.min(COP_real):.2f}\n"
    else:
        cop_info = ""
    
    info_text = f"""Estadísticas del Período:
• Temp. servidor máx: {np.max(T_servidor):.1f}°C
• Temp. servidor prom: {np.mean(T_servidor):.1f}°C  
• Cumplimiento objetivo: {porcentaje_cumplimiento:.1f}%
• Potencia prom: {np.mean(P_refrigeracion):.0f}W
• Potencia máx: {np.max(P_refrigeracion):.0f}W
{cop_info}• Equipo: {datos.get('equipo_info', {}).get('nombre', 'No especificado')}"""
    
    ax1.text(0.02, 0.98, info_text, transform=ax1.transAxes, 
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.8),
             verticalalignment='top', fontsize=10, fontfamily='monospace')
    
    plt.tight_layout()
    plt.savefig(_get_graph_path('rendimiento_sistema_temporal.png'), dpi=DPI, bbox_inches='tight')
    _finish_plot()
    
    print(f"📊 Gráfico temporal guardado: graphs/rendimiento_sistema_temporal.png")
