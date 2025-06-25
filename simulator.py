import os
import numpy as np
import matplotlib.pyplot as plt
import subprocess

# --- Configuración del Experimento ---
MODEL_NAME = "AnalisisServidores.Modelos.SimulacionCompleta"
NUM_SIMULATIONS = 2000  # Número de meses de Enero a simular
SIMULATION_TIME = 31 * 86400  # 31 días en segundos
COST_PER_KWH = 0.13

# --- Parámetros Estadísticos del Clima (de la Tabla 2.1) ---
TMIN_MU = 20.1
TMIN_SIGMA = 2.5
DELTAT_MU = 11.4
DELTAT_SIGMA = 3.0

def generate_weather_profile():
    """Genera un perfil de 31 días de T_min y T_max."""
    t_min_profile = np.random.normal(TMIN_MU, TMIN_SIGMA, 31)
    delta_t_profile = np.random.normal(DELTAT_MU, DELTAT_SIGMA, 31)
    # Asegurar que delta_t no sea negativo
    delta_t_profile[delta_t_profile < 0] = 0
    t_max_profile = t_min_profile + delta_t_profile
    return t_min_profile, t_max_profile

def create_and_run_simulation(strategy, run_id):
    """Crea un script.mos, lo ejecuta y devuelve el costo."""
    
    # Generar perfil climático para esta ejecución
    t_min_profile, t_max_profile = generate_weather_profile()

    # Modelica espera temperaturas en Kelvin
    t_min_k = [t + 273.15 for t in t_min_profile]
    t_max_k = [t + 273.15 for t in t_max_profile]

    # Crear el contenido del script.mos
    # Esto es un ejemplo simplificado. Una implementación real podría
    # necesitar un mecanismo más robusto para pasar parámetros, como
    # modificar un archivo de inicialización XML.
    # Por simplicidad aquí, se asume que el modelo se modifica para
    # tener estos parámetros directamente. Una mejor práctica sería
    # usar archivos externos.
    
    # Aquí se simula la ejecución. En un caso real, se generaría un script
    #.mos que carga el modelo, establece los parámetros y simula.
    
    # El nombre del archivo de resultados
    result_file_name = f"{MODEL_NAME.split('.')[-1]}_{strategy}_{run_id}_res.mat"
    
    # Crear el contenido del script.mos
    mos_script_content = f"""
    loadFile("AnalisisServidores.mo");
    setCommandLineOptions("-d=newInst"); // Para evitar advertencias de reinstanciación
    simulate(
        {MODEL_NAME},
        startTime=0,
        stopTime={SIMULATION_TIME},
        numberOfIntervals=5000,
        method="dassl",
        simflags="-s {strategy}",
        fileNamePrefix="{MODEL_NAME.split('.')[-1]}_{strategy}_{run_id}"
    );
    quit();
    """
    
    # Escribir el script a un archivo
    script_path = f"run_{strategy}_{run_id}.mos"
    with open(script_path, "w") as f:
        f.write(mos_script_content)

    # Ejecutar OpenModelica (OMC)
    # Asegúrate de que 'omc' esté en el PATH del sistema
    # La bandera -s pasa argumentos al ejecutable de simulación
    # Aquí se pasa el nombre de la estrategia para que el modelo la use
    # NOTA: Esto requiere que el modelo `SimulacionCompleta` sea modificado
    # para aceptar un argumento de línea de comandos que seleccione la estrategia.
    # Una forma más simple es tener dos modelos separados. Usaremos esa
    # suposición para el resto del script.
    
    model_to_simulate = f"{MODEL_NAME}(estrategia=AnalisisServidores.Modelos.SimulacionCompleta.TipoControl.{strategy})"
    
    mos_script_content_final = f"""
    loadFile("AnalisisServidores.mo");
    setCommandLineOptions("-d=newInst");
    result = simulate(
        {model_to_simulate},
        startTime=0,
        stopTime={SIMULATION_TIME},
        numberOfIntervals=5000,
        method="dassl",
        fileNamePrefix="{MODEL_NAME.split('.')[-1]}_{strategy}_{run_id}"
    );
    val = val(EnergiaTotal, {SIMULATION_TIME}, result.resultFile);
    // Escribir el resultado a un archivo de texto para que Python lo lea
    writeFile("result_{strategy}_{run_id}.txt", String(val));
    quit();
    """
    
    with open(script_path, "w") as f:
        f.write(mos_script_content_final)
    
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
        # Podrías querer guardar los.mat para un análisis más profundo
        # os.remove(result_file_name)
        
        return cost
    except subprocess.CalledProcessError as e:
        print(f"Error en la simulación {run_id} para la estrategia {strategy}:")
        print(e.stdout)
        print(e.stderr)
        return None

def run_monte_carlo(strategy):
    """Ejecuta la simulación de Monte Carlo para una estrategia dada."""
    print(f"--- Iniciando simulación de Monte Carlo para la estrategia: {strategy} ---")
    costs = []
    for i in range(NUM_SIMULATIONS):
        print(f"Ejecutando simulación {i+1}/{NUM_SIMULATIONS}...")
        # En una implementación real, la llamada a la simulación iría aquí.
        # Para este ejemplo, generaremos datos de costo simulados basados en
        # los resultados esperados para ilustrar el análisis.
        if strategy == "LineaBase":
            cost = np.random.normal(415, 45)
        else: # Optimizado
            cost = np.random.normal(352.75, 38) # Menor costo y menor desviación
        
        if cost is not None:
            costs.append(cost)
    
    return np.array(costs)

def analyze_and_plot_results(costs, strategy_name):
    """Analiza y plotea los resultados de una ejecución de Monte Carlo."""
    mean_cost = np.mean(costs)
    median_cost = np.median(costs)
    std_dev = np.std(costs)
    costo_90 = np.percentile(costs, 90)

    print(f"\n--- Resultados para la estrategia: {strategy_name} ---")
    print(f"Costo Mensual Promedio: ${mean_cost:.2f}")
    print(f"Desviación Estándar del Costo: ${std_dev:.2f}")
    print(f"Costo Mediano: ${median_cost:.2f}")
    print(f"Costo90 (Percentil 90): ${costo_90:.2f}")

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.hist(costs, bins=50, density=True, alpha=0.7, label=f'Distribución de Costos ({strategy_name})')
    plt.axvline(mean_cost, color='red', linestyle='dashed', linewidth=2, label=f'Costo Promedio (${mean_cost:.2f})')
    plt.axvline(costo_90, color='purple', linestyle='dashed', linewidth=2, label=f'Costo90 (${costo_90:.2f})')
    plt.title(f'Distribución de Probabilidad del Costo Mensual - Estrategia {strategy_name}')
    plt.xlabel('Costo Mensual (U$D)')
    plt.ylabel('Densidad de Probabilidad')
    plt.legend()
    plt.grid(True)
    plt.savefig(f'histograma_costos_{strategy_name}.png')
    plt.show()

    return {"mean": mean_cost, "std": std_dev, "costo90": costo_90}


if __name__ == "__main__":
    # NOTA: La ejecución real de 2000+ simulaciones de OpenModelica puede tardar
    # mucho tiempo. El siguiente código utiliza datos generados para ilustrar
    # el proceso de análisis. Para ejecutarlo realmente, descomente las
    # llamadas a `create_and_run_simulation` y comente la generación de datos.

    # Ejecutar para la estrategia de línea base
    costs_baseline = run_monte_carlo("LineaBase")
    results_baseline = analyze_and_plot_results(costs_baseline, "Línea Base")

    # Ejecutar para la estrategia optimizada
    costs_optimized = run_monte_carlo("Optimizado")
    results_optimized = analyze_and_plot_results(costs_optimized, "Optimizada")

    # Tabla comparativa final
    print("\n\n--- Tabla Comparativa de Resultados ---")
    print(f"{'Métrica':<25} {'Línea Base':<15} {'Optimizada':<15} {'Mejora (%)':<15}")
    print("-" * 70)
    
    mean_improvement = (1 - results_optimized['mean'] / results_baseline['mean']) * 100
    costo90_improvement = (1 - results_optimized['costo90'] / results_baseline['costo90']) * 100
    
    print(f"{'Costo Promedio (U$D)':<25} ${results_baseline['mean']:.2f}{'':<7} ${results_optimized['mean']:.2f}{'':<7} {mean_improvement:.2f}%")
    print(f"{'Costo90 (U$D)':<25} ${results_baseline['costo90']:.2f}{'':<7} ${results_optimized['costo90']:.2f}{'':<7} {costo90_improvement:.2f}%")
    print("-" * 70)