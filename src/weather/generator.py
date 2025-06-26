"""
Módulo para generación de perfiles climáticos y de temperatura.
"""

import numpy as np
from scipy.stats import truncnorm
from config.settings import (
    TMIN_MEDIAN, TMAX_MEDIAN, TMIN_SIGMA, TMAX_SIGMA,
    TMIN_HOUR, TMIN_HOUR_SIGMA, TMAX_HOUR, TMAX_HOUR_SIGMA
)


def generate_weather_profile():
    """Genera un perfil de 31 días de temperaturas con variación horaria."""
    # Generar temperaturas diarias
    t_min_daily = np.random.normal(TMIN_MEDIAN, TMIN_SIGMA, 31)
    t_max_daily = np.random.normal(TMAX_MEDIAN, TMAX_SIGMA, 31)
    
    # Generar horarios de extremos con distribución normal truncada
    # Para hora mínima: 6am ± 30 min = rango [5.5, 6.5] con distribución normal centrada en 6
    # Usar sigma = 0.25 para buena concentración en el centro
    sigma_min = 0.25
    a_min = (TMIN_HOUR - TMIN_HOUR_SIGMA - TMIN_HOUR) / sigma_min
    b_min = (TMIN_HOUR + TMIN_HOUR_SIGMA - TMIN_HOUR) / sigma_min
    hour_min_daily = truncnorm.rvs(a_min, b_min, loc=TMIN_HOUR, scale=sigma_min, size=31)
    
    # Para hora máxima: 4pm ± 1 hora = rango [15, 17] con distribución normal centrada en 16
    # Usar sigma = 0.4 para que 99.7% esté dentro del rango ±1h (3 sigmas)
    sigma_max = 0.4
    a_max = (TMAX_HOUR - TMAX_HOUR_SIGMA - TMAX_HOUR) / sigma_max
    b_max = (TMAX_HOUR + TMAX_HOUR_SIGMA - TMAX_HOUR) / sigma_max
    hour_max_daily = truncnorm.rvs(a_max, b_max, loc=TMAX_HOUR, scale=sigma_max, size=31)
    
    # Asegurar que los horarios estén en rango válido (por si acaso)
    hour_min_daily = np.clip(hour_min_daily, 0, 23.99)
    hour_max_daily = np.clip(hour_max_daily, 0, 23.99)
    
    return t_min_daily, t_max_daily, hour_min_daily, hour_max_daily


def generate_hourly_temperature_profile(t_min_daily, t_max_daily, hour_min_daily, hour_max_daily):
    """Genera un perfil de temperatura horario para N días usando función sinusoidal ajustada."""
    hours_per_day = 24
    num_days = len(t_min_daily)
    total_hours = num_days * hours_per_day
    hourly_temps = np.zeros(total_hours)
    
    for day in range(num_days):
        t_min = t_min_daily[day]
        t_max = t_max_daily[day]
        hour_min = hour_min_daily[day]
        hour_max = hour_max_daily[day]
        
        # Crear perfil usando sinusoide simple desplazada
        day_hours = np.arange(0, 24)
        
        # Parámetros básicos
        temp_avg = (t_min + t_max) / 2
        amplitude = (t_max - t_min) / 2
        
        # Crear perfil base centrado en las horas objetivo
        # El mínimo típicamente ocurre 6 horas antes del máximo
        # Usar el promedio de los horarios para centrar la función
        center_hour = hour_max
        
        daily_temps = np.zeros(hours_per_day)
        
        for i, hour in enumerate(day_hours):
            # Fase ajustada para que el máximo esté en hour_max
            phase = 2 * np.pi * (hour - center_hour) / 24
            # Coseno desplazado: máximo en phase=0, mínimo en phase=π
            daily_temps[i] = temp_avg + amplitude * np.cos(phase)
        
        # Ahora ajustar los valores específicos para que coincidan exactamente
        # con los horarios aleatorios generados
        hour_min_idx = int(round(hour_min)) % 24
        hour_max_idx = int(round(hour_max)) % 24
        
        # Forzar los valores exactos en las horas correctas
        daily_temps[hour_min_idx] = t_min
        daily_temps[hour_max_idx] = t_max
        
        # Suavizar ligeramente las transiciones inmediatas para evitar discontinuidades
        # Solo si no están muy cerca entre sí
        if abs(hour_min_idx - hour_max_idx) > 2:
            # Suavizar mínimo
            if hour_min_idx > 0:
                daily_temps[hour_min_idx - 1] = (daily_temps[hour_min_idx - 1] + t_min) / 2
            if hour_min_idx < 23:
                daily_temps[hour_min_idx + 1] = (daily_temps[hour_min_idx + 1] + t_min) / 2
            
            # Suavizar máximo
            if hour_max_idx > 0:
                daily_temps[hour_max_idx - 1] = (daily_temps[hour_max_idx - 1] + t_max) / 2
            if hour_max_idx < 23:
                daily_temps[hour_max_idx + 1] = (daily_temps[hour_max_idx + 1] + t_max) / 2
        
        # Almacenar en el array total
        start_idx = day * hours_per_day
        end_idx = start_idx + hours_per_day
        hourly_temps[start_idx:end_idx] = daily_temps
    
    return hourly_temps
