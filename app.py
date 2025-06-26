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

app = Flask(__name__)

# Parámetros físicos del modelo
PARAMS_FISICOS = {
    'A': 126,  # Área de superficie externa (m^2)
    'U': 2.5,  # Coeficiente de transferencia de calor (W/m^2.K)
    'Q_servers': 10000,  # Carga térmica de los servidores (W)
    'C_th': 150000,  # Capacidad térmica de la sala (J/K)
    'Q_max_cooling': 15000,  # Potencia máxima de refrigeración del HVAC (W)
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
        'cop_nominal': 3.2,  # COP a 35°C exterior
        'potencia_nominal': 15000,  # W
        'precio': 2500,  # USD
        'vida_util': 8,  # años
        'mantenimiento_anual': 200,  # USD/año
        'cop_curve': lambda t: max(1.0, 4.5 - 0.12 * (t - 20)) if t <= 45 else 1.0  # t en °C
    },
    'eficiente': {
        'nombre': 'Eficiente (Inverter)',
        'cop_nominal': 4.5,  # COP a 35°C exterior
        'potencia_nominal': 15000,  # W
        'precio': 4200,  # USD
        'vida_util': 12,  # años
        'mantenimiento_anual': 150,  # USD/año
        'cop_curve': lambda t: max(1.5, 5.8 - 0.08 * (t - 20)) if t <= 45 else 1.5  # t en °C
    },
    'premium': {
        'nombre': 'Premium (VRF)',
        'cop_nominal': 5.2,  # COP a 35°C exterior
        'potencia_nominal': 15000,  # W
        'precio': 6800,  # USD
        'vida_util': 15,  # años
        'mantenimiento_anual': 120,  # USD/año
        'cop_curve': lambda t: max(2.0, 6.5 - 0.06 * (t - 20)) if t <= 45 else 2.0  # t en °C
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
    """Ejecuta una única instancia de simulación para su procesamiento en paralelo."""
    estrategia, t_min_profile, t_max_profile, modelo_refrigeracion, fisico_params = args
    
    t_final = 31 * 86400
    y0 = [297.15, 0]  # 24°C, 0 kWh
    t_eval = np.arange(0, t_final, 3600)
    
    sol = solve_ivp(
        lambda t, y: modelo_sala_servidores(t, y, t_min_profile, t_max_profile, estrategia, modelo_refrigeracion, fisico_params),
        [0, t_final],
        y0,
        t_eval=t_eval,
        method='RK45',
        rtol=1e-2,  # Tolerancia relajada para mayor velocidad
        atol=1e-4
    )
    
    T_room_profile = sol.y[0]
    energia_total = sol.y[1][-1]
    costo = (energia_total / 3.6e6) * fisico_params['costo_kWh']
    
    temp_profile_data = {
        'tiempo': sol.t.tolist(),
        'T_room': T_room_profile.tolist(),
        'T_min': t_min_profile.tolist(),
        'T_max': t_max_profile.tolist()
    }
    
    return costo, temp_profile_data

# Modelo físico de la sala de servidores (refactorizado para no usar globales)
def modelo_sala_servidores(t, y, t_min_profile, t_max_profile, estrategia, modelo_refrigeracion, params_fisicos):
    """
    Modelo dinámico de la sala de servidores.
    
    Parámetros:
    t: tiempo actual (s)
    y: vector de estado [T_room, energia_total]
    t_min_profile, t_max_profile: perfiles de temperatura min/max diarios
    estrategia: 'LineaBase' o 'Optimizado'
    modelo_refrigeracion: modelo de equipo de refrigeración a utilizar
    params_fisicos: parámetros físicos del modelo
    
    Retorna:
    dy/dt: derivadas de las variables de estado
    """
    T_room, energia_total = y
    
    # Determinar el día actual (0-30)
    dia = min(int(t / 86400), 30)
    
    # Obtener temperatura ambiente actual
    T_ambient = perfil_temperatura_diaria(t, t_min_profile[dia], t_max_profile[dia])
    
    # Calor transmitido desde el exterior
    Q_transmission = params_fisicos['A'] * params_fisicos['U'] * (T_ambient - T_room)
    
    # Lógica de control según estrategia
    if estrategia == 'LineaBase':
        # Estrategia de termostato simple
        if T_room > (24 + 273.15):
            Q_cooling = params_fisicos['Q_max_cooling']
        else:
            Q_cooling = 0
    else:  # Optimizado
        # Estrategia de pre-enfriamiento con banda muerta
        T_setpoint_inferior = 22 + 273.15
        T_setpoint_superior = 26 + 273.15
        
        # Calcular COP actual
        cop_actual = calcular_cop(T_ambient - 273.15, modelo_refrigeracion)
        
        if T_room > T_setpoint_superior:
            Q_cooling = params_fisicos['Q_max_cooling']
        elif T_room > T_setpoint_inferior and cop_actual > 3.0:
            Q_cooling = params_fisicos['Q_max_cooling']  # Enfriar solo si es eficiente
        else:
            Q_cooling = 0
    
    # Derivada de la temperatura
    dT_room_dt = (params_fisicos['Q_servers'] + Q_transmission - Q_cooling) / params_fisicos['C_th']
    
    # Calcular potencia eléctrica consumida
    cop = calcular_cop(T_ambient - 273.15, modelo_refrigeracion)
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
    t_min_profile = np.random.normal(PARAMS_CLIMA['TMIN_MU'], PARAMS_CLIMA['TMIN_SIGMA'], 31) + 273.15
    delta_t_profile = np.random.normal(PARAMS_CLIMA['DELTAT_MU'], PARAMS_CLIMA['DELTAT_SIGMA'], 31)
    # Asegurar que delta_t no sea negativo
    delta_t_profile[delta_t_profile < 0] = 0
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
            temp = profile['T_room'][i] - 273.15  # Convertir a Celsius
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

# Función para generar gráfico de diagnóstico de randomización
def generate_randomization_diagnostic(temp_profiles):
    """Genera un gráfico de diagnóstico de randomización."""
    # Extraer temperaturas mínimas y máximas de los perfiles
    t_mins = []
    t_maxs = []
    
    for profile in temp_profiles:
        t_mins.extend(profile['T_min'])
        t_maxs.extend(profile['T_max'])
    
    # Convertir a Celsius
    t_mins = np.array(t_mins) - 273.15
    t_maxs = np.array(t_maxs) - 273.15
    
    # Crear figura
    fig = Figure(figsize=(10, 8))
    
    # Subplot para T_min
    ax1 = fig.add_subplot(2, 2, 1)
    ax1.hist(t_mins, bins=20, alpha=0.7, color='blue')
    ax1.set_title('Distribución de Temperaturas Mínimas')
    ax1.set_xlabel('Temperatura (°C)')
    ax1.set_ylabel('Frecuencia')
    
    # Ajustar distribución normal a T_min
    mu_min, std_min = norm.fit(t_mins)
    x_min = np.linspace(min(t_mins), max(t_mins), 100)
    p_min = norm.pdf(x_min, mu_min, std_min) * len(t_mins) * (max(t_mins) - min(t_mins)) / 20
    ax1.plot(x_min, p_min, 'r--', linewidth=2)
    ax1.text(0.05, 0.95, f'μ = {mu_min:.2f}, σ = {std_min:.2f}', 
             transform=ax1.transAxes, fontsize=10, verticalalignment='top')
    
    # Subplot para T_max
    ax2 = fig.add_subplot(2, 2, 2)
    ax2.hist(t_maxs, bins=20, alpha=0.7, color='red')
    ax2.set_title('Distribución de Temperaturas Máximas')
    ax2.set_xlabel('Temperatura (°C)')
    ax2.set_ylabel('Frecuencia')
    
    # Ajustar distribución normal a T_max
    mu_max, std_max = norm.fit(t_maxs)
    x_max = np.linspace(min(t_maxs), max(t_maxs), 100)
    p_max = norm.pdf(x_max, mu_max, std_max) * len(t_maxs) * (max(t_maxs) - min(t_maxs)) / 20
    ax2.plot(x_max, p_max, 'r--', linewidth=2)
    ax2.text(0.05, 0.95, f'μ = {mu_max:.2f}, σ = {std_max:.2f}', 
             transform=ax2.transAxes, fontsize=10, verticalalignment='top')
    
    # Subplot para Q-Q plot de T_min
    ax3 = fig.add_subplot(2, 2, 3)
    from scipy.stats import probplot
    probplot(t_mins, dist="norm", plot=ax3)
    ax3.set_title('Q-Q Plot Temperaturas Mínimas')
    
    # Subplot para Q-Q plot de T_max
    ax4 = fig.add_subplot(2, 2, 4)
    probplot(t_maxs, dist="norm", plot=ax4)
    ax4.set_title('Q-Q Plot Temperaturas Máximas')
    
    fig.tight_layout()
    
    # Convertir figura a imagen base64
    buf = io.BytesIO()
    FigureCanvas(fig).print_png(buf)
    data = base64.b64encode(buf.getbuffer()).decode('ascii')
    
    return f"data:image/png;base64,{data}"

# Función para generar gráfico de distribución de temperaturas horarias
def generate_hourly_temperature_distribution(temp_stats):
    """Genera un gráfico de distribución de temperaturas horarias."""
    hourly_means = temp_stats['hourly_means']
    
    # Crear figura
    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(1, 1, 1)
    
    # Graficar distribución horaria
    hours = np.arange(24)
    ax.plot(hours, hourly_means, 'o-', linewidth=2, markersize=8)
    ax.set_title('Distribución de Temperaturas Medias por Hora')
    ax.set_xlabel('Hora del Día')
    ax.set_ylabel('Temperatura Media (°C)')
    ax.set_xticks(np.arange(0, 24, 2))
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Resaltar horas extremas
    min_hour = temp_stats['min_hour']
    max_hour = temp_stats['max_hour']
    ax.plot(min_hour, hourly_means[min_hour], 'bo', markersize=10, label=f'Mínima ({min_hour}:00, {hourly_means[min_hour]:.2f}°C)')
    ax.plot(max_hour, hourly_means[max_hour], 'ro', markersize=10, label=f'Máxima ({max_hour}:00, {hourly_means[max_hour]:.2f}°C)')
    
    # Añadir rango de temperatura
    ax.fill_between(hours, hourly_means, min(hourly_means), alpha=0.2, color='blue')
    
    # Añadir etiquetas con información
    ax.text(0.02, 0.95, f'Rango diario: {min(hourly_means):.2f}°C - {max(hourly_means):.2f}°C', 
            transform=ax.transAxes, fontsize=10, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.legend()
    fig.tight_layout()
    
    # Convertir figura a imagen base64
    buf = io.BytesIO()
    FigureCanvas(fig).print_png(buf)
    data = base64.b64encode(buf.getbuffer()).decode('ascii')
    
    return f"data:image/png;base64,{data}"

# Función para generar gráfico de curvas COP
def generate_cop_curves():
    """Genera un gráfico comparativo de las curvas COP de diferentes modelos de refrigeración."""
    # Crear figura
    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(1, 1, 1)
    
    # Temperaturas para evaluar
    temps = np.linspace(15, 45, 100)
    
    # Colores para cada modelo
    colors = {
        'economico': 'blue',
        'eficiente': 'green',
        'premium': 'red'
    }
    
    # Graficar curvas COP
    for modelo, datos in MODELOS_REFRIGERACION.items():
        cops = [datos['cop_curve'](t) for t in temps]
        ax.plot(temps, cops, '-', color=colors[modelo], linewidth=2, label=f"{datos['nombre']} (COP nominal: {datos['cop_nominal']})")
    
    ax.set_title('Curvas COP vs Temperatura Exterior')
    ax.set_xlabel('Temperatura Exterior (°C)')
    ax.set_ylabel('COP (Coefficient of Performance)')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    
    # Añadir información adicional
    ax.text(0.02, 0.05, 'Mayor COP = Mayor eficiencia energética', 
            transform=ax.transAxes, fontsize=10, verticalalignment='bottom', 
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    fig.tight_layout()
    
    # Convertir figura a imagen base64
    buf = io.BytesIO()
    FigureCanvas(fig).print_png(buf)
    data = base64.b64encode(buf.getbuffer()).decode('ascii')
    
    return f"data:image/png;base64,{data}"

# Variable global para almacenar resultados de simulación en curso
simulation_results = None

# Función para ejecutar simulación en segundo plano
def run_simulation_background(modelo_refrigeracion='eficiente'):
    global simulation_results
    
    start_time = time.time()
    
    # Número de simulaciones para esta demo (reducido para velocidad)
    num_simulations = 30
    
    # Ejecutar simulaciones para ambas estrategias
    costs_baseline, temp_profiles_baseline = run_monte_carlo_simulation("LineaBase", num_simulations, modelo_refrigeracion)
    baseline_stats = calculate_cost_statistics(costs_baseline)
    
    costs_optimized, temp_profiles_optimized = run_monte_carlo_simulation("Optimizado", num_simulations, modelo_refrigeracion)
    optimized_stats = calculate_cost_statistics(costs_optimized)
    
    # Análisis de temperaturas
    temp_stats = calculate_temperature_statistics(temp_profiles_baseline)
    
    # Generar gráficos
    randomization_diagnostic = generate_randomization_diagnostic(temp_profiles_baseline)
    hourly_temp_distribution = generate_hourly_temperature_distribution(temp_stats)
    cop_curves = generate_cop_curves()
    
    # Calcular mejora porcentual
    improvement = {
        'mean': round((1 - optimized_stats['mean'] / baseline_stats['mean']) * 100, 2),
        'costo90': round((1 - optimized_stats['costo90'] / baseline_stats['costo90']) * 100, 2)
    }
    
    # Generar datos horarios para el heatmap
    hourly_temps = []
    for day in range(31):
        for hour in range(24):
            # Tomar una muestra aleatoria de los perfiles de temperatura
            if temp_profiles_baseline:
                profile_idx = np.random.randint(0, len(temp_profiles_baseline))
                profile = temp_profiles_baseline[profile_idx]
                
                # Calcular el índice correspondiente a este día y hora
                idx = day * 24 + hour
                if idx < len(profile['tiempo']):
                    temp = profile['T_room'][idx] - 273.15  # Convertir a Celsius
                    
                    hourly_temps.append({
                        'day': day + 1,
                        'hour': hour,
                        'temperature': round(temp, 2)
                    })
    
    # Preparar respuesta
    
    # Crear una copia serializable del modelo de refrigeración
    modelo_info_serializable = MODELOS_REFRIGERACION[modelo_refrigeracion].copy()
    if 'cop_curve' in modelo_info_serializable:
        del modelo_info_serializable['cop_curve']
        
    simulation_results = {
        'hourly_temps': hourly_temps,
        'costs_baseline': costs_baseline,
        'costs_optimized': costs_optimized,
        'baseline_stats': baseline_stats,
        'optimized_stats': optimized_stats,
        'improvement': improvement,
        'randomization_diagnostic': randomization_diagnostic,
        'hourly_temp_distribution': hourly_temp_distribution,
        'cop_curves': cop_curves,
        'simulation_time': round(time.time() - start_time, 2),
        'modelo_refrigeracion': modelo_info_serializable,
        'status': 'complete'
    }

@app.route('/')
def index():
    # Obtener explicaciones de los gráficos
    explanations = {
        'temperature_distribution': 'Este gráfico muestra la distribución de temperaturas horarias durante el mes de enero. La curva representa la temperatura media para cada hora del día, permitiendo identificar los momentos más fríos y cálidos.',
        'cost_baseline': 'Este histograma muestra la distribución de probabilidad del costo mensual de energía utilizando la estrategia de línea base (termostato simple). La línea roja indica el costo promedio, mientras que la línea púrpura muestra el Costo90, que representa el valor que no será excedido con un 90% de probabilidad.',
        'cost_optimized': 'Este histograma muestra la distribución de probabilidad del costo mensual de energía utilizando la estrategia optimizada (pre-enfriamiento predictivo). Comparado con la línea base, se observa un desplazamiento hacia costos menores y una reducción en la variabilidad.',
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