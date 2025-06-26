"""
Módulo para análisis estadístico de resultados.
"""

import numpy as np


def calculate_cost_statistics(costs):
    """Calcula estadísticas de costos."""
    return {
        "mean": np.mean(costs),
        "median": np.median(costs),
        "std": np.std(costs),
        "costo90": np.percentile(costs, 90),
        "min": np.min(costs),
        "max": np.max(costs)
    }


def calculate_temperature_statistics(temperature_profiles):
    """Calcula estadísticas de temperatura por hora del día."""
    if not temperature_profiles:
        return None
    
    # Convertir lista de perfiles a array numpy
    temp_data = np.array(temperature_profiles)
    
    # Reestructurar para obtener temperaturas por hora del día
    num_simulations = temp_data.shape[0]
    hours_per_day = 24
    days = 31
    
    # Reorganizar datos: para cada hora del día (0-23), obtener todas las temperaturas
    hourly_temps = np.zeros((hours_per_day, num_simulations * days))
    
    for sim in range(num_simulations):
        for day in range(days):
            for hour in range(hours_per_day):
                global_hour_idx = day * hours_per_day + hour
                hourly_temps[hour, sim * days + day] = temp_data[sim, global_hour_idx]
    
    # Calcular estadísticas por hora
    hourly_means = np.mean(hourly_temps, axis=1)
    hourly_p25 = np.percentile(hourly_temps, 25, axis=1)
    hourly_p75 = np.percentile(hourly_temps, 75, axis=1)
    
    return {
        "hourly_means": hourly_means,
        "hourly_p25": hourly_p25,
        "hourly_p75": hourly_p75,
        "hourly_temps": hourly_temps,
        "temp_min": np.min(temp_data),
        "temp_max": np.max(temp_data),
        "min_hour": np.argmin(hourly_means),
        "max_hour": np.argmax(hourly_means)
    }


def compare_strategies(results_baseline, results_optimized):
    """Compara dos estrategias y calcula mejoras."""
    mean_improvement = (1 - results_optimized['mean'] / results_baseline['mean']) * 100
    costo90_improvement = (1 - results_optimized['costo90'] / results_baseline['costo90']) * 100
    
    return {
        "mean_improvement": mean_improvement,
        "costo90_improvement": costo90_improvement
    }
