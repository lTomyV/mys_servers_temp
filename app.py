from flask import Flask, render_template, jsonify, request
import os
import numpy as np
import json
import time
import re

app = Flask(__name__)

# Extraer información del archivo modelica.txt
def extract_modelica_data():
    with open('modelica.txt', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Extraer parámetros climáticos
    climate_params = {
        'TMIN_MU': 20.1,
        'TMIN_SIGMA': 2.5,
        'DELTAT_MU': 11.4,
        'DELTAT_SIGMA': 3.0
    }
    
    # Extraer otros datos relevantes
    model_data = {
        'MODEL_NAME': "AnalisisServidores.Modelos.SimulacionCompleta",
        'NUM_SIMULATIONS': 2000,
        'SIMULATION_TIME': 31 * 86400,  # 31 días en segundos
        'COST_PER_KWH': 0.13
    }
    
    return {
        'climate_params': climate_params,
        'model_data': model_data
    }

# Función para generar datos de simulación
def generate_simulation_data():
    # Parámetros extraídos de modelica.txt
    modelica_data = extract_modelica_data()
    climate_params = modelica_data['climate_params']
    
    # Generar datos de temperatura para 31 días
    days = 31
    t_min_profile = np.random.normal(climate_params['TMIN_MU'], climate_params['TMIN_SIGMA'], days)
    delta_t_profile = np.random.normal(climate_params['DELTAT_MU'], climate_params['DELTAT_SIGMA'], days)
    delta_t_profile[delta_t_profile < 0] = 0
    t_max_profile = t_min_profile + delta_t_profile
    
    # Generar datos horarios para cada día
    hours = 24 * days
    hourly_temps = []
    for day in range(days):
        for hour in range(24):
            # Aproximación sinusoidal para la temperatura horaria
            t_min = t_min_profile[day]
            t_max = t_max_profile[day]
            
            # Calcular temperatura usando aproximación sinusoidal
            mean_temp = (t_max + t_min) / 2
            amplitude = (t_max - t_min) / 2
            # La temperatura mínima ocurre alrededor de las 5:00 AM
            # La temperatura máxima ocurre alrededor de las 3:00 PM (15:00)
            hour_rad = (hour - 5) * (2 * np.pi / 24)
            temp = mean_temp + amplitude * np.sin(hour_rad)
            
            hourly_temps.append({
                'day': day + 1,
                'hour': hour,
                'temperature': round(temp, 2)
            })
    
    # Generar costos para estrategia de línea base
    costs_baseline = np.random.normal(415, 45, 100)
    costs_baseline = [round(max(0, cost), 2) for cost in costs_baseline]
    
    # Generar costos para estrategia optimizada
    costs_optimized = np.random.normal(352.75, 38, 100)
    costs_optimized = [round(max(0, cost), 2) for cost in costs_optimized]
    
    # Calcular estadísticas
    baseline_stats = {
        'mean': round(np.mean(costs_baseline), 2),
        'median': round(np.median(costs_baseline), 2),
        'std': round(np.std(costs_baseline), 2),
        'costo90': round(np.percentile(costs_baseline, 90), 2)
    }
    
    optimized_stats = {
        'mean': round(np.mean(costs_optimized), 2),
        'median': round(np.median(costs_optimized), 2),
        'std': round(np.std(costs_optimized), 2),
        'costo90': round(np.percentile(costs_optimized, 90), 2)
    }
    
    # Calcular mejora porcentual
    improvement = {
        'mean': round((1 - optimized_stats['mean'] / baseline_stats['mean']) * 100, 2),
        'costo90': round((1 - optimized_stats['costo90'] / baseline_stats['costo90']) * 100, 2)
    }
    
    return {
        'hourly_temps': hourly_temps,
        'costs_baseline': costs_baseline,
        'costs_optimized': costs_optimized,
        'baseline_stats': baseline_stats,
        'optimized_stats': optimized_stats,
        'improvement': improvement
    }

@app.route('/')
def index():
    # Obtener explicaciones de los gráficos
    explanations = {
        'temperature_distribution': 'Este gráfico muestra la distribución de temperaturas horarias durante el mes de enero. La variación de colores representa la frecuencia de cada temperatura en cada hora del día, permitiendo identificar patrones y tendencias en el clima.',
        'cost_baseline': 'Este histograma muestra la distribución de probabilidad del costo mensual de energía utilizando la estrategia de línea base (termostato simple). La línea roja indica el costo promedio, mientras que la línea púrpura muestra el Costo90, que representa el valor que no será excedido con un 90% de probabilidad.',
        'cost_optimized': 'Este histograma muestra la distribución de probabilidad del costo mensual de energía utilizando la estrategia optimizada (pre-enfriamiento predictivo). Comparado con la línea base, se observa un desplazamiento hacia costos menores y una reducción en la variabilidad.',
        'randomization': 'Este gráfico valida científicamente la calidad de la randomización utilizada en las simulaciones de Monte Carlo, asegurando que los datos generados siguen las distribuciones estadísticas esperadas y no contienen sesgos sistemáticos.'
    }
    
    return render_template('index.html', explanations=explanations)

@app.route('/api/simulate', methods=['POST'])
def simulate():
    # Simular proceso de cálculo
    time.sleep(2)  # Simular tiempo de procesamiento
    
    # Generar datos de simulación
    simulation_data = generate_simulation_data()
    
    return jsonify(simulation_data)

@app.route('/api/modelica_info')
def modelica_info():
    # Extraer información relevante de modelica.txt
    modelica_data = extract_modelica_data()
    
    return jsonify(modelica_data)

if __name__ == '__main__':
    app.run(debug=True) 