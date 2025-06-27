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
    'Q_max_cooling': 60000,  # Potencia máxima del HVAC (W)
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
        'potencia_nominal': 60000,  # W
        'precio': 2500,  # USD
        'vida_util': 8,  # años
        'mantenimiento_anual': 200,  # USD/año
        # COP ≈ 2.8 @35°C; cae 0.05 por °C hacia arriba
        'cop_curve': lambda t: max(1.0, 2.8 - 0.05 * (t - 35))
    },
    'eficiente': {
        'nombre': 'Eficiente (Inverter)',
        'cop_nominal': 3.2,  # COP a 35°C exterior
        'potencia_nominal': 60000,  # W
        'precio': 4200,  # USD
        'vida_util': 12,  # años
        'mantenimiento_anual': 150,  # USD/año
        'cop_curve': lambda t: max(1.2, 3.2 - 0.06 * (t - 35))
    },
    'premium': {
        'nombre': 'Premium (VRF)',
        'cop_nominal': 3.8,  # COP a 35°C exterior
        'potencia_nominal': 60000,  # W
        'precio': 6800,  # USD
        'vida_util': 15,  # años
        'mantenimiento_anual': 120,  # USD/año
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
    estrategia: 'LineaBase' o 'Optimizado'
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
    
    # Lógica de control según estrategia
    if estrategia == 'LineaBase':
        # Estrategia de termostato simple
        if T_room > 24.0:
            Q_cooling = params_fisicos['Q_max_cooling']
        else:
            Q_cooling = 0
    else:  # Optimizado
        # Estrategia de pre-enfriamiento con banda muerta
        T_setpoint_normal = 24.0
        T_setpoint_precool = 21.0

        # Calcular COP actual
        cop_actual = calcular_cop(T_ambient, modelo_refrigeracion)

        # Siempre enfriar si superamos el setpoint normal (límite estricto)
        if T_room > T_setpoint_normal:
            Q_cooling = params_fisicos['Q_max_cooling']
        # Si estamos por debajo del límite, pre-enfriamos solo si es muy eficiente
        elif T_room > T_setpoint_precool and cop_actual > 3.5:
            Q_cooling = params_fisicos['Q_max_cooling']  # Enfriar solo si es muy eficiente
        else:
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

# Variable global para almacenar resultados de simulación en curso
simulation_results = None

# Función para ejecutar simulación en segundo plano
def run_simulation_background(modelo_refrigeracion='eficiente'):
    global simulation_results
    
    start_time = time.time()
    
    # Número de simulaciones para esta demo (reducido para velocidad)
    num_simulations = 200

    # Ejecutar simulaciones (una sola estrategia de control)
    costs, temp_profiles = run_monte_carlo_simulation("Optimizado", num_simulations, modelo_refrigeracion)
    cost_stats = calculate_cost_statistics(costs)

    # Análisis de temperaturas
    temp_stats = calculate_temperature_statistics(temp_profiles)

    # Generar datos para los gráficos
    randomization_data = get_randomization_diagnostic_data(temp_profiles)
    hourly_temp_data = get_hourly_temperature_distribution_data(temp_stats)
    cop_curves_data = get_cop_curves_data()

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

    # Costo eléctrico de los servidores (constante por simulación)
    servidor_kwh = (PARAMS_FISICOS['Q_servers'] * 744) / 1000  # kWh mes
    cost_servidores = servidor_kwh * PARAMS_FISICOS['costo_kWh']
    costs_servers = [cost_servidores] * num_simulations
    server_stats = calculate_cost_statistics(costs_servers)

    simulation_results = {
        'hourly_temps': hourly_temps,
        'costs': costs,
        'cost_stats': cost_stats,
        'randomization_data': randomization_data,
        'hourly_temp_data': hourly_temp_data,
        'cop_curves_data': cop_curves_data,
        'simulation_time': round(time.time() - start_time, 2),
        'modelo_refrigeracion': modelo_info_serializable,
        'status': 'complete',
        'costs_servers': costs_servers,
        'server_stats': server_stats,
        'daily_max_avg': daily_max_avg
    }

@app.route('/')
def index():
    # Obtener explicaciones de los gráficos
    explanations = {
        'temperature_distribution': 'Este gráfico muestra la distribución de temperaturas horarias durante el mes de enero. La curva representa la temperatura media para cada hora del día, permitiendo identificar los momentos más fríos y cálidos.',
        'cost_monthly': 'Este histograma muestra la distribución de probabilidad del costo mensual de energía del sistema completo (servidores + HVAC) para el mes de enero. La línea roja indica el costo promedio, mientras que la línea púrpura muestra el Costo90 (valor no superado con el 90% de probabilidad).',
        'randomization': 'Este gráfico valida científicamente la calidad de la randomización utilizada en las simulaciones de Monte Carlo, mostrando que las temperaturas generadas siguen distribuciones normales y pasan pruebas estadísticas de normalidad (Q-Q plots).',
        'cop_curves': 'Este gráfico muestra las curvas de Coeficiente de Rendimiento (COP) para diferentes modelos de equipos de refrigeración. El COP indica cuánta energía de refrigeración se produce por cada unidad de energía eléctrica consumida. Un COP más alto significa mayor eficiencia.'
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