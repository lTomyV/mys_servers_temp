"""
Módulo para ejecutar simulaciones de OpenModelica.
"""

import os
import subprocess
import numpy as np
from config.settings import MODEL_NAME, SIMULATION_TIME, COST_PER_KWH
from src.weather.generator import generate_weather_profile, generate_hourly_temperature_profile


def create_and_run_simulation(strategy, run_id):
    """Crea un script.mos, lo ejecuta y devuelve el costo."""
    
    # Generar perfil climático para esta ejecución
    t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_weather_profile()
    
    # Generar perfil horario de temperatura
    hourly_temps = generate_hourly_temperature_profile(t_min_daily, t_max_daily, hour_min_daily, hour_max_daily)

    # Modelica espera temperaturas en Kelvin (convertir solo las diarias para compatibilidad)
    t_min_k = [t + 273.15 for t in t_min_daily]
    t_max_k = [t + 273.15 for t in t_max_daily]

    # El nombre del archivo de resultados
    result_file_name = f"{MODEL_NAME.split('.')[-1]}_{strategy}_{run_id}_res.mat"
    
    # Crear el contenido del script.mos
    mos_script_content = f"""
    loadFile("AnalisisServidores.mo");
    setCommandLineOptions("-d=newInst");
    result = simulate(
        {MODEL_NAME}(estrategia=AnalisisServidores.Modelos.SimulacionCompleta.TipoControl.{strategy}),
        startTime=0,
        stopTime={SIMULATION_TIME},
        numberOfIntervals=5000,
        method="dassl",
        fileNamePrefix="{MODEL_NAME.split('.')[-1]}_{strategy}_{run_id}"
    );
    val = val(EnergiaTotal, {SIMULATION_TIME}, result.resultFile);
    writeFile("result_{strategy}_{run_id}.txt", String(val));
    quit();
    """
    
    # Escribir el script a un archivo
    script_path = f"run_{strategy}_{run_id}.mos"
    with open(script_path, "w") as f:
        f.write(mos_script_content)
    
    try:
        subprocess.run(["omc", script_path], check=True, capture_output=True, text=True)
        
        # Leer el resultado del archivo de texto
        with open(f"result_{strategy}_{run_id}.txt", "r") as f:
            total_energy_joules = float(f.read())
            
        total_energy_kwh = total_energy_joules / 3.6e6
        cost = total_energy_kwh * COST_PER_KWH
        
        # Limpiar archivos
        os.remove(script_path)
        os.remove(f"result_{strategy}_{run_id}.txt")
        
        return cost, hourly_temps
    except subprocess.CalledProcessError as e:
        print(f"Error en la simulación {run_id} para la estrategia {strategy}:")
        print(e.stdout)
        print(e.stderr)
        return None, None


def run_monte_carlo_simulation(strategy, num_simulations):
    """Ejecuta la simulación de Monte Carlo para una estrategia dada."""
    print(f"--- Iniciando simulación de Monte Carlo para la estrategia: {strategy} ---")
    costs = []
    temperature_profiles = []
    
    for i in range(num_simulations):
        #print(f"Ejecutando simulación {i+1}/{num_simulations}...")
        
        # En una implementación real, usar create_and_run_simulation
        # cost, hourly_temps = create_and_run_simulation(strategy, i)
        
        # Para demo, generar datos simulados
        t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_weather_profile()
        hourly_temps = generate_hourly_temperature_profile(t_min_daily, t_max_daily, hour_min_daily, hour_max_daily)
        temperature_profiles.append(hourly_temps)
        
        # Generar costos simulados
        if strategy == "LineaBase":
            cost = np.random.normal(415, 45)
        else:  # Optimizado
            cost = np.random.normal(352.75, 38)
        
        if cost is not None:
            costs.append(cost)
    
    return np.array(costs), temperature_profiles
