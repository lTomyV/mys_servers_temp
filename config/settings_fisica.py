"""
Configuración del experimento de simulación de servidores con control adaptativo.
Actualizado para usar modelos físicos directos.
"""

# --- Configuración del Experimento ---
MODEL_TYPE = "FISICA"  # Usar modelo físico directo (sin OpenModelica)
NUM_SIMULATIONS = 50   # Número de simulaciones Monte Carlo
SIMULATION_DAYS = 31   # Duración de cada simulación en días
COST_PER_KWH = 0.13    # Costo de energía eléctrica por kWh

# --- Parámetros Estadísticos del Clima (datos reales) ---
TMIN_MEDIAN = 21
TMAX_MEDIAN = 37.5
TMIN_SIGMA = 1.177
TMAX_SIGMA = 3.56

# Horarios de extremos de temperatura
TMIN_HOUR = 6  # 6am
TMIN_HOUR_SIGMA = 0.5  # +- 30 min
TMAX_HOUR = 16  # 4pm
TMAX_HOUR_SIGMA = 1.0  # +- 1 hora

# --- Configuración de gráficos ---
FIGURE_SIZE_LARGE = (14, 8)
FIGURE_SIZE_MEDIUM = (10, 6)
DPI = 300
GRAPHS_DIR = "graphs"  # Directorio para guardar gráficos
SHOW_PLOTS = False  # Si True, abre los gráficos automáticamente (interrumpe la ejecución)
