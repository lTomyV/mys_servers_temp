"""
Configuración del experimento de simulación de servidores con control adaptativo.
Actualizado para usar modelos físicos directos.
"""

# --- Configuración del Experimento ---
MODEL_TYPE = "FISICA"  # Usar modelo físico directo (sin OpenModelica)
NUM_SIMULATIONS = 50   # Número de simulaciones Monte Carlo
SIMULATION_DAYS = 31   # Duración de cada simulación en días
COST_PER_KWH = 0.13    # Costo de energía eléctrica por kWh (según consigna del profesor)

# --- Parámetros Estadísticos del Clima (datos reales) ---
TMIN_MEDIAN = 21       # Mediana de temperaturas mínimas
TMAX_MEDIAN = 37       # Mediana de temperaturas máximas  
TMIN_SIGMA = 1.33      # Desviación estándar de temperaturas mínimas (rango 16°-25°)
TMAX_SIGMA = 2.0       # Desviación estándar de temperaturas máximas (rango 30°-42°)

# Horarios de extremos de temperatura
TMIN_HOUR = 6  # 6am
TMIN_HOUR_SIGMA = 0.167  # Para rango 5.5-6.5 (±0.5/3, distribución gaussiana ajustada)
TMAX_HOUR = 16  # 4pm
TMAX_HOUR_SIGMA = 0.33  # Para rango 15-17 (±1, 99.7% en ±3σ)

# --- Configuración de gráficos ---
FIGURE_SIZE_LARGE = (14, 8)
FIGURE_SIZE_MEDIUM = (10, 6)
DPI = 300
GRAPHS_DIR = "graphs"  # Directorio para guardar gráficos
SHOW_PLOTS = False  # Si True, abre los gráficos automáticamente (interrumpe la ejecución)

# --- Configuración de Paralelización ---
MAX_WORKERS = None  # None = auto-detectar, o especificar número de hilos
ENABLE_PARALLEL = False  # True = usar paralelización, False = secuencial

# --- Configuración de Equipos HVAC ---
MODELO_HVAC = "eficiente"  # Opciones: 'economico', 'eficiente', 'premium'
