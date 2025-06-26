"""
Configuración del experimento de simulación de servidores.
"""

# --- Configuración del Experimento ---
MODEL_NAME = "AnalisisServidores.Modelos.SimulacionCompleta"
NUM_SIMULATIONS = 100  # Número de simulaciones a ejecutar
SIMULATION_TIME = 31 * 86400  # 31 días en segundos
COST_PER_KWH = 0.13

# --- Parámetros Estadísticos del Clima (datos reales) ---
TMIN_MEDIAN = 21
TMAX_MEDIAN = 38
TMIN_SIGMA = 1.177
TMAX_SIGMA = 4.62

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
