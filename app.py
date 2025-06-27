from flask import Flask, render_template, jsonify, request
import os
import numpy as np
import json
import time
import re
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from scipy.stats import norm
import io
import base64
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import datetime
from scipy.integrate import solve_ivp
import threading
import multiprocessing
import glob

app = Flask(__name__)

# Directorio con archivos JSON de Open-Meteo (uno por año)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def _load_hourly_temps(path):
    """Lee un JSON Open-Meteo y devuelve np.array(744) en Celsius."""
    with open(path, 'r', encoding='utf-8') as f:
        j = json.load(f)
    temps_c = np.array(j['hourly']['temperature_2m'], dtype=float)
    return temps_c  # Mantener en Celsius

# Cargar todas las series disponibles
HOURLY_TEMPS_SERIES = []
for file in glob.glob(os.path.join(DATA_DIR, 'santa_fe_*_01.json')):
    try:
        HOURLY_TEMPS_SERIES.append(_load_hourly_temps(file))
    except Exception as e:
        print(f"No se pudo cargar {file}: {e}")

def _get_random_hourly_series():
    """Devuelve una serie horaria aleatoria o None si no hay datos."""
    if HOURLY_TEMPS_SERIES:
        idx = np.random.randint(0, len(HOURLY_TEMPS_SERIES))
        return HOURLY_TEMPS_SERIES[idx]
    return None

# Parámetros físicos del modelo
PARAMS_FISICOS = {
    'A': 126,  # Área de superficie externa (m^2)
    'U': 5.5,  # Coeficiente de transferencia de calor (W/m^2.K)
    'Q_servers': 45000,  # Carga térmica de los servidores (W)
    'C_th': 2_000_000,  # Capacidad térmica realista de la sala (J/K)
    'Q_max_cooling': 75000,  # Potencia máxima del HVAC (W) - aumentada de 60kW a 75kW
    'costo_kWh': 0.13  # Costo de la energía (USD/kWh)
}

# Parámetros climáticos
PARAMS_CLIMA = {
    'TMIN_MU': 20.1,
    'TMIN_SIGMA': 2.5,
    'DELTAT_MU': 11.4,
    'DELTAT_SIGMA': 3.0
}

# Modelos de equipos de refrigeración con datos reales
# Fuente: Datos técnicos de fabricantes de equipos HVAC comerciales
MODELOS_REFRIGERACION = {
    'economico': {
        'nombre': 'Economico (Estándar)',
        'cop_nominal': 2.8,  # COP a 35°C exterior
        'potencia_nominal': 75000,  # W - aumentada de 60kW a 75kW
        'precio': 3000,  # USD - ajustado por mayor capacidad
        'vida_util': 8,  # años
        'mantenimiento_anual': 250,  # USD/año - ajustado
        # COP ≈ 2.8 @35°C; cae 0.05 por °C hacia arriba
        'cop_curve': lambda t: max(1.0, 2.8 - 0.05 * (t - 35))
    },
    'eficiente': {
        'nombre': 'Eficiente (Inverter)',
        'cop_nominal': 3.2,  # COP a 35°C exterior
        'potencia_nominal': 75000,  # W - aumentada de 60kW a 75kW
        'precio': 5000,  # USD - ajustado por mayor capacidad
        'vida_util': 12,  # años
        'mantenimiento_anual': 180,  # USD/año - ajustado
        'cop_curve': lambda t: max(1.2, 3.2 - 0.06 * (t - 35))
    },
    'premium': {
        'nombre': 'Premium (VRF)',
        'cop_nominal': 3.8,  # COP a 35°C exterior
        'potencia_nominal': 75000,  # W - aumentada de 60kW a 75kW
        'precio': 8000,  # USD - ajustado por mayor capacidad
        'vida_util': 15,  # años
        'mantenimiento_anual': 150,  # USD/año - ajustado
        'cop_curve': lambda t: max(1.5, 3.8 - 0.07 * (t - 35))
    }
}

# Modelo de refrigeración seleccionado (por defecto)
MODELO_ACTUAL = 'eficiente'

# Función para calcular el COP basado en temperatura ambiente y modelo de refrigeración
def calcular_cop(t_amb_c, modelo=MODELO_ACTUAL):
    """Calcula el COP del HVAC en función de la temperatura ambiente y el modelo seleccionado."""
    return MODELOS_REFRIGERACION[modelo]['cop_curve'](t_amb_c)

# Función para calcular la temperatura ambiente en un momento dado
def perfil_temperatura_diaria(t, t_min, t_max):
    """Calcula la temperatura ambiente instantánea usando aproximación sinusoidal."""
    periodo = 86400.0  # 24 horas en segundos
    freq_ang = 2 * np.pi / periodo
    # Asume que T_max ocurre a las 15:00 (t=54000s) y T_min a las 5:00 (t=18000s)
    t_offset = 54000
    amplitud = (t_max - t_min) / 2
    linea_media = (t_max + t_min) / 2
    
    # Convertir t a segundos dentro del día actual
    t_day = t % periodo
    
    return linea_media + amplitud * np.cos(freq_ang * (t_day - t_offset))

# Esta función debe estar en el nivel superior para que multiprocessing funcione
def run_single_simulation(args):
    """Ejecuta una única instancia de simulación (apta para multiprocessing)."""
    if len(args) == 6:
        estrategia, t_min_profile, t_max_profile, modelo_refrigeracion, fisico_params, hourly_series = args
    else:
        estrategia, t_min_profile, t_max_profile, modelo_refrigeracion, fisico_params = args
        hourly_series = _get_random_hourly_series()
    
    t_final = 31 * 86400
    y0 = [24.0, 0]  # 24°C, 0 kWh
    t_eval = np.arange(0, t_final, 3600)
    
    # Ajustar capacidad de refrigeración al modelo de equipo
    local_params = fisico_params.copy()
    local_params['Q_max_cooling'] = MODELOS_REFRIGERACION[modelo_refrigeracion]['potencia_nominal']
    
    sol = solve_ivp(
        lambda t, y: modelo_sala_servidores(t, y, t_min_profile, t_max_profile, estrategia, modelo_refrigeracion, local_params, hourly_series),
        [0, t_final],
        y0,
        t_eval=t_eval,
        method='RK45',
        rtol=1e-2,  # Tolerancia relajada para mayor velocidad
        atol=1e-4
    )
    
    T_room_profile = sol.y[0]
    energia_total = sol.y[1][-1]
    total_energia = energia_total + local_params['Q_servers'] * t_final
    costo = (total_energia / 3.6e6) * local_params['costo_kWh']
    
    temp_profile_data = {
        'tiempo': sol.t.tolist(),
        'T_room': T_room_profile.tolist(),
        'T_min': t_min_profile.tolist(),
        'T_max': t_max_profile.tolist()
    }
    
    return costo, temp_profile_data

# Modelo físico de la sala de servidores (refactorizado para no usar globales)
def modelo_sala_servidores(t, y, t_min_profile, t_max_profile, estrategia, modelo_refrigeracion, params_fisicos, hourly_series=None):
    """
    Modelo dinámico de la sala de servidores.
    
    Parámetros:
    t: tiempo actual (s)
    y: vector de estado [T_room, energia_total]
    t_min_profile, t_max_profile: perfiles de temperatura min/max diarios
    estrategia: parámetro heredado (ya no se usa)
    modelo_refrigeracion: modelo de equipo de refrigeración a utilizar
    params_fisicos: parámetros físicos del modelo
    hourly_series: serie horaria aleatoria o None si no hay datos
    
    Retorna:
    dy/dt: derivadas de las variables de estado
    """
    T_room, energia_total = y
    
    # Determinar el día actual (0-30)
    dia = min(int(t / 86400), 30)
    
    # Obtener temperatura ambiente actual
    if hourly_series is not None and len(hourly_series) >= 744:
        idx = int(t // 3600) % 744
        T_ambient = hourly_series[idx]
    else:
        T_ambient = perfil_temperatura_diaria(t, t_min_profile[dia], t_max_profile[dia])
    
    # Calor transmitido desde el exterior
    Q_transmission = params_fisicos['A'] * params_fisicos['U'] * (T_ambient - T_room)
    
    # Estrategia de control robusta con límites estrictos para sala de servidores
    T_setpoint_critico = 24.0  # Límite crítico absoluto
    T_setpoint_normal = 22.0   # Límite normal de operación
    T_setpoint_precool = 20.0  # Inicio de pre-enfriamiento

    # Calcular COP actual
    cop_actual = calcular_cop(T_ambient, modelo_refrigeracion)

    # Control por niveles de temperatura
    if T_room > T_setpoint_critico:
        # EMERGENCIA: Temperatura crítica - HVAC al máximo
        Q_cooling = params_fisicos['Q_max_cooling']
    elif T_room > T_setpoint_normal:
        # ALTO: Supera límite normal - HVAC al máximo
        Q_cooling = params_fisicos['Q_max_cooling']
    elif T_room > T_setpoint_precool:
        # MEDIO: Pre-enfriamiento inteligente
        if cop_actual > 2.5:  # Umbral más bajo para mayor actividad
            Q_cooling = params_fisicos['Q_max_cooling']
        else:
            Q_cooling = 0
    else:
        # BAJO: Temperatura óptima - HVAC apagado
        Q_cooling = 0
    
    # Derivada de la temperatura
    dT_room_dt = (params_fisicos['Q_servers'] + Q_transmission - Q_cooling) / params_fisicos['C_th']
    
    # Calcular potencia eléctrica consumida
    cop = calcular_cop(T_ambient, modelo_refrigeracion)
    P_electric = Q_cooling / max(cop, 1e-6) if Q_cooling > 1e-6 else 0
    
    # Derivada de la energía total
    dE_dt = P_electric
    
    return [dT_room_dt, dE_dt]

# Función para ejecutar la simulación de Monte Carlo de forma optimizada y en paralelo
def run_monte_carlo_simulation(estrategia, num_simulations=100, modelo_refrigeracion=MODELO_ACTUAL):
    """Ejecuta simulaciones de Monte Carlo para una estrategia dada usando procesamiento en paralelo."""
    
    # Generar todos los perfiles climáticos de antemano
    all_climate_profiles = [generate_weather_profile() for _ in range(num_simulations)]
    
    # Preparar argumentos para el pool de procesos
    tasks = [(estrategia, t_min, t_max, modelo_refrigeracion, PARAMS_FISICOS) for t_min, t_max in all_climate_profiles]
    
    costs = []
    temp_profiles = []
    
    try:
        # Usar un pool de procesos para paralelizar las simulaciones
        with multiprocessing.Pool() as pool:
            # Usar map para distribuir las tareas y recoger los resultados
            results = pool.map(run_single_simulation, tasks, chunksize=1)
            
        # Para optimizar, solo guardamos un subconjunto de perfiles de temperatura completos
        max_profiles_to_save = min(10, num_simulations)
        
        for i, (cost, temp_profile) in enumerate(results):
            costs.append(cost)
            if i < max_profiles_to_save:
                temp_profiles.append(temp_profile)
                
    except Exception as e:
        print(f"Error durante el procesamiento en paralelo: {e}")
        # Si falla, se podría implementar una ejecución secuencial como fallback
        return [], []
    
    return costs, temp_profiles

# Función para generar perfiles climáticos
def generate_weather_profile():
    """Genera un perfil de 31 días de T_min y T_max."""
    # Si disponemos de la serie real, derivar min y max diarios de ella
    if HOURLY_TEMPS_SERIES:
        t_min_profile = []
        t_max_profile = []
        for d in range(31):
            series = HOURLY_TEMPS_SERIES[np.random.randint(0, len(HOURLY_TEMPS_SERIES))]
            day_slice = series[d*24:(d+1)*24]
            t_min_profile.append(float(np.min(day_slice)))
            t_max_profile.append(float(np.max(day_slice)))
        return np.array(t_min_profile), np.array(t_max_profile)

    # Fallback estocástico si no hay datos reales
    t_min_profile = np.random.normal(PARAMS_CLIMA['TMIN_MU'], PARAMS_CLIMA['TMIN_SIGMA'], 31)
    delta_t_profile = np.random.normal(PARAMS_CLIMA['DELTAT_MU'], PARAMS_CLIMA['DELTAT_SIGMA'], 31)
    delta_t_profile = np.clip(delta_t_profile, 6, 15)  # acotar a rango físico
    t_max_profile = t_min_profile + delta_t_profile
    return t_min_profile, t_max_profile

# Función para calcular estadísticas de costos
def calculate_cost_statistics(costs):
    """Calcula estadísticas de costos."""
    return {
        'mean': float(np.mean(costs)),
        'median': float(np.median(costs)),
        'std': float(np.std(costs)),
        'costo90': float(np.percentile(costs, 90)),
        'min': float(np.min(costs)),
        'max': float(np.max(costs))
    }

# Función para calcular estadísticas de temperatura
def calculate_temperature_statistics(temp_profiles):
    """Calcula estadísticas de temperatura."""
    # Extraer todas las temperaturas
    all_temps = []
    hourly_temps = [[] for _ in range(24)]
    
    for profile in temp_profiles:
        for i, t in enumerate(profile['tiempo']):
            hour = int((t % 86400) / 3600)
            temp = profile['T_room'][i]  # Ya están en Celsius
            all_temps.append(temp)
            hourly_temps[hour].append(temp)
    
    # Calcular medias horarias
    hourly_means = np.array([np.mean(temps) for temps in hourly_temps])
    
    # Encontrar horas con temperaturas extremas
    min_hour = np.argmin(hourly_means)
    max_hour = np.argmax(hourly_means)
    
    return {
        'temp_min': float(min(all_temps)),
        'temp_max': float(max(all_temps)),
        'hourly_means': hourly_means.tolist(),
        'min_hour': int(min_hour),
        'max_hour': int(max_hour)
    }

# Funciones para preparar datos de gráficos (reemplazan a las funciones que generaban imágenes)
def get_randomization_diagnostic_data(temp_profiles):
    """Prepara datos para el gráfico de diagnóstico de randomización."""
    if not temp_profiles:
        return {'t_mins': [], 't_maxs': []}
    
    t_mins = []
    t_maxs = []
    for profile in temp_profiles:
        t_mins.extend(profile['T_min'])
        t_maxs.extend(profile['T_max'])
    
    t_mins_c = np.array(t_mins).tolist()  # Ya están en Celsius
    t_maxs_c = np.array(t_maxs).tolist()  # Ya están en Celsius
    
    return {'t_mins': t_mins_c, 't_maxs': t_maxs_c}

def get_hourly_temperature_distribution_data(temp_stats):
    """Prepara datos para el gráfico de distribución de temperaturas horarias."""
    return {
        'hourly_means': temp_stats['hourly_means'],
        'min_hour': temp_stats['min_hour'],
        'max_hour': temp_stats['max_hour']
    }

def get_ambient_temperature_distribution_data():
    """Prepara datos para mostrar la distribución de temperaturas exteriores."""
    if not HOURLY_TEMPS_SERIES:
        return {'hourly_means': [], 'min_temp': 0, 'max_temp': 40}
    
    # Tomar una muestra de series para calcular el promedio horario
    hourly_temps = [[] for _ in range(24)]
    
    for series in HOURLY_TEMPS_SERIES[:5]:  # Usar las primeras 5 series
        for day in range(31):  # 31 días
            for hour in range(24):
                idx = day * 24 + hour
                if idx < len(series):
                    hourly_temps[hour].append(series[idx])
    
    # Calcular medias horarias
    hourly_means = [np.mean(temps) if temps else 20 for temps in hourly_temps]
    
    # Encontrar temperaturas extremas
    all_temps = [temp for series in HOURLY_TEMPS_SERIES[:5] for temp in series]
    min_temp = min(all_temps) if all_temps else 15
    max_temp = max(all_temps) if all_temps else 35
    
    return {
        'hourly_means': hourly_means,
        'min_temp': min_temp,
        'max_temp': max_temp
    }

def get_cop_curves_data():
    """Prepara datos para el gráfico de curvas COP."""
    temps = np.linspace(15, 45, 100).tolist()
    curves = {}
    
    colors = {
        'economico': 'rgba(54, 162, 235, 0.8)',
        'eficiente': 'rgba(75, 192, 192, 0.8)',
        'premium': 'rgba(255, 99, 132, 0.8)'
    }
    
    for modelo, datos in MODELOS_REFRIGERACION.items():
        curves[modelo] = {
            'nombre': datos['nombre'],
            'cops': [datos['cop_curve'](t) for t in temps],
            'color': colors.get(modelo, 'rgba(201, 203, 207, 0.8)')
        }
        
    return {'temps': temps, 'curves': curves}

def get_energy_consumption_data(temp_profiles):
    """Prepara datos para el gráfico de consumo energético acumulado."""
    if not temp_profiles:
        return {'time_hours': [], 'energy_cumulative': []}
    
    # Tomar el primer perfil como ejemplo
    profile = temp_profiles[0]
    time_hours = [t/3600 for t in profile['tiempo']]  # Convertir a horas
    
    # Simular consumo energético basado en diferencias de temperatura
    energy_cumulative = []
    cumulative = 0
    
    for i, t in enumerate(profile['tiempo']):
        if i > 0:
            # Estimar consumo basado en la actividad del HVAC
            temp_diff = abs(profile['T_room'][i] - 22)  # Diferencia con temperatura objetivo
            if temp_diff > 2:  # HVAC activo
                power_consumption = 15  # kW aproximado
                time_step = (profile['tiempo'][i] - profile['tiempo'][i-1]) / 3600  # horas
                cumulative += power_consumption * time_step
        energy_cumulative.append(cumulative)
    
    return {'time_hours': time_hours, 'energy_cumulative': energy_cumulative}

def get_temperature_vs_ambient_data(temp_profiles):
    """Prepara datos para correlación temperatura interior vs exterior."""
    if not temp_profiles:
        return {'ambient_temps': [], 'room_temps': []}
    
    ambient_temps = []
    room_temps = []
    
    # Tomar muestras de varios perfiles
    for profile in temp_profiles[:3]:  # Usar los primeros 3 perfiles
        for i in range(0, len(profile['T_room']), 24):  # Muestras diarias
            if i < len(profile['T_min']):
                # Usar temperatura máxima del día como representativa
                ambient_temp = profile['T_max'][min(i//24, len(profile['T_max'])-1)]
                room_temp = profile['T_room'][i]
                ambient_temps.append(ambient_temp)
                room_temps.append(room_temp)
    
    return {'ambient_temps': ambient_temps, 'room_temps': room_temps}

def get_control_efficiency_data(temp_profiles):
    """Prepara datos para análisis de eficiencia del control."""
    if not temp_profiles:
        return {'hours': [], 'hvac_active': [], 'efficiency_score': 0}
    
    profile = temp_profiles[0]
    hours = list(range(24))
    hvac_active_by_hour = [0] * 24
    
    # Analizar actividad del HVAC por hora del día
    for i, t in enumerate(profile['tiempo']):
        hour = int((t % 86400) / 3600)
        temp = profile['T_room'][i]
        
        # Estimar si HVAC está activo (temperatura fuera del rango óptimo)
        if temp > 24 or temp < 21:
            hvac_active_by_hour[hour] += 1
    
    # Normalizar a porcentaje
    total_samples_per_hour = len(profile['tiempo']) // 24
    hvac_active_percent = [count / max(total_samples_per_hour, 1) * 100 for count in hvac_active_by_hour]
    
    # Calcular score de eficiencia (menor actividad = mayor eficiencia)
    efficiency_score = 100 - np.mean(hvac_active_percent)
    
    return {
        'hours': hours, 
        'hvac_active': hvac_active_percent,
        'efficiency_score': round(efficiency_score, 1)
    }

def get_cost_breakdown_data(costs_hvac, costs_servers):
    """Prepara datos para el desglose de costos."""
    return {
        'hvac_costs': costs_hvac,
        'server_costs': costs_servers,
        'hvac_mean': float(np.mean(costs_hvac)),
        'server_mean': float(np.mean(costs_servers)),
        'total_mean': float(np.mean(costs_hvac) + np.mean(costs_servers)),
        'hvac_percentage': float(np.mean(costs_hvac) / (np.mean(costs_hvac) + np.mean(costs_servers)) * 100),
        'server_percentage': float(np.mean(costs_servers) / (np.mean(costs_hvac) + np.mean(costs_servers)) * 100)
    }

# Variable global para almacenar resultados de simulación en curso
simulation_results = None

# Función para ejecutar simulación en segundo plano
def run_simulation_background(modelo_refrigeracion='eficiente'):
    global simulation_results
    
    start_time = time.time()
    
    # Número de simulaciones para esta demo (reducido para velocidad)
    num_simulations = 200

    # Ejecutar simulaciones (una sola estrategia de control robusta)
    costs, temp_profiles = run_monte_carlo_simulation("SalaServidores", num_simulations, modelo_refrigeracion)
    cost_stats = calculate_cost_statistics(costs)

    # Análisis de temperaturas
    temp_stats = calculate_temperature_statistics(temp_profiles)

    # Costo eléctrico de los servidores (constante por simulación)
    servidor_kwh = (PARAMS_FISICOS['Q_servers'] * 744) / 1000  # kWh mes
    cost_servidores = servidor_kwh * PARAMS_FISICOS['costo_kWh']
    costs_servers = [cost_servidores] * num_simulations
    server_stats = calculate_cost_statistics(costs_servers)

    # Generar datos para los gráficos
    randomization_data = get_randomization_diagnostic_data(temp_profiles)
    hourly_temp_data = get_hourly_temperature_distribution_data(temp_stats)
    ambient_temp_data = get_ambient_temperature_distribution_data()
    cop_curves_data = get_cop_curves_data()
    
    # Nuevos gráficos educativos
    energy_consumption_data = get_energy_consumption_data(temp_profiles)
    control_efficiency_data = get_control_efficiency_data(temp_profiles)
    cost_breakdown_data = get_cost_breakdown_data(costs, costs_servers)

    # Generar datos horarios para el heatmap
    hourly_temps = []
    for day in range(31):
        for hour in range(24):
            if temp_profiles:
                profile_idx = np.random.randint(0, len(temp_profiles))
                profile = temp_profiles[profile_idx]
                idx = day * 24 + hour
                if idx < len(profile['tiempo']):
                    temp = profile['T_room'][idx]  # Ya están en Celsius
                    hourly_temps.append({'day': day + 1, 'hour': hour, 'temperature': round(temp, 2)})

    # --- Temperatura máxima diaria promedio ---
    daily_max_matrix = []
    for profile in temp_profiles:
        day_max = []
        for d in range(31):
            start = d * 24
            end = start + 24
            slice_t = np.array(profile['T_room'][start:end])  # Ya están en Celsius
            day_max.append(float(np.max(slice_t)))
        daily_max_matrix.append(day_max)
    if daily_max_matrix:
        daily_max_avg = np.mean(daily_max_matrix, axis=0).tolist()
    else:
        daily_max_avg = []

    # Preparar respuesta

    modelo_info_serializable = MODELOS_REFRIGERACION[modelo_refrigeracion].copy()
    if 'cop_curve' in modelo_info_serializable:
        del modelo_info_serializable['cop_curve']

    simulation_results = {
        'hourly_temps': hourly_temps,
        'costs': costs,
        'cost_stats': cost_stats,
        'randomization_data': randomization_data,
        'hourly_temp_data': hourly_temp_data,
        'ambient_temp_data': ambient_temp_data,
        'cop_curves_data': cop_curves_data,
        'energy_consumption_data': energy_consumption_data,
        'control_efficiency_data': control_efficiency_data,
        'cost_breakdown_data': cost_breakdown_data,
        'simulation_time': round(time.time() - start_time, 2),
        'modelo_refrigeracion': modelo_info_serializable,
        'status': 'complete',
        'daily_max_avg': daily_max_avg,
        'costs_servers': costs_servers,
        'server_stats': server_stats
    }

@app.route('/')
def index():
    # Obtener explicaciones de los gráficos
    explanations = {
        'temperature_distribution': 'Este gráfico muestra la distribución de temperaturas horarias durante el mes de enero. La curva representa la temperatura media para cada hora del día, permitiendo identificar los momentos más fríos y cálidos.',
        'cost_monthly': 'Este histograma muestra la distribución de probabilidad del costo mensual de energía del sistema completo (servidores + HVAC) para el mes de enero. La línea roja indica el costo promedio, mientras que la línea púrpura muestra el Costo90 (valor no superado con el 90% de probabilidad).',
        'randomization': 'Este gráfico valida científicamente la calidad de la randomización utilizada en las simulaciones de Monte Carlo, mostrando las distribuciones de temperaturas EXTERIORES (ambiente) de Santa Fe que alimentan el modelo. Las temperaturas mostradas son del clima exterior, no del interior de la sala.',
        'cop_curves': 'Este gráfico muestra las curvas de Coeficiente de Rendimiento (COP) para diferentes modelos de equipos de refrigeración. El COP indica cuánta energía de refrigeración se produce por cada unidad de energía eléctrica consumida. Un COP más alto significa mayor eficiencia.',
        'daily_max_temp': 'Este gráfico muestra la temperatura máxima diaria promedio de la sala de servidores durante el mes. Permite identificar patrones de comportamiento térmico y verificar que el sistema de control mantiene las temperaturas dentro de rangos seguros (típicamente 18-26°C para centros de datos).',
        'energy_consumption': 'Gráfico que muestra el consumo energético acumulado del sistema HVAC a lo largo del tiempo, permitiendo identificar períodos de mayor demanda energética y la eficiencia del sistema de control.',
        'temperature_vs_ambient': 'Correlación entre la temperatura exterior y la temperatura interior de la sala, mostrando cómo las condiciones climáticas afectan el rendimiento del sistema de refrigeración.',
        'control_efficiency': 'Análisis de la eficiencia del sistema de control, mostrando qué porcentaje del tiempo el HVAC está activo y cómo responde a las variaciones de temperatura.',
        'cost_breakdown': 'Desglose detallado de los costos operativos, separando el consumo de los servidores del consumo del sistema HVAC, fundamental para análisis económicos.'
    }
    
    # Modelos de refrigeración disponibles
    modelos = {key: value['nombre'] for key, value in MODELOS_REFRIGERACION.items()}
    
    return render_template('index.html', explanations=explanations, modelos=modelos)

@app.route('/api/simulate', methods=['POST'])
def simulate():
    global simulation_results
    
    # Obtener el modelo de refrigeración seleccionado
    data = request.get_json() or {}
    modelo_refrigeracion = data.get('modelo', 'eficiente')
    
    if modelo_refrigeracion not in MODELOS_REFRIGERACION:
        modelo_refrigeracion = 'eficiente'
    
    # Reiniciar resultados
    simulation_results = {'status': 'running'}
    
    # Iniciar simulación en segundo plano
    thread = threading.Thread(target=run_simulation_background, args=(modelo_refrigeracion,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/api/simulation_status')
def simulation_status():
    global simulation_results
    
    if simulation_results is None:
        return jsonify({'status': 'not_started'})
    
    return jsonify(simulation_results)

@app.route('/api/modelos_refrigeracion')
def get_modelos_refrigeracion():
    # Crear una versión serializable de los modelos (sin las funciones lambda)
    modelos_serializables = {}
    for key, modelo in MODELOS_REFRIGERACION.items():
        modelo_copia = modelo.copy()
        # Eliminar la función lambda que no es serializable
        if 'cop_curve' in modelo_copia:
            del modelo_copia['cop_curve']
        modelos_serializables[key] = modelo_copia
    
    # Añadir información de depuración
    print("API /api/modelos_refrigeracion llamada, devolviendo:", modelos_serializables)
    return jsonify(modelos_serializables)

if __name__ == '__main__':
    multiprocessing.freeze_support() # Necesario para Windows
    app.run(debug=True) 