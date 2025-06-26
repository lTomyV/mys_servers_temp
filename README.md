# Simulador de Análisis de Servidores

Este proyecto implementa un simulador de Monte Carlo para analizar el consumo energético de servidores bajo diferentes estrategias de control térmico.

## Estructura del Proyecto

```
mys_servers_temp/
├── main.py                    # Archivo principal del simulador
├── config/
│   ├── __init__.py
│   └── settings.py           # Configuración del experimento
├── src/
│   ├── __init__.py
│   ├── weather/
│   │   ├── __init__.py
│   │   └── generator.py      # Generación de perfiles climáticos
│   ├── simulation/
│   │   ├── __init__.py
│   │   └── runner.py         # Ejecución de simulaciones OpenModelica
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── statistics.py     # Análisis estadístico de resultados
│   └── visualization/
│       ├── __init__.py
│       └── plots.py          # Generación de gráficos
├── graphs/                   # Gráficos generados por el simulador
├── requirements.txt          # Dependencias de Python
└── README.md                 # Este archivo
```

## Características

### Generación de Clima
- Temperaturas mínimas y máximas con distribución normal
- Horarios aleatorios de extremos de temperatura
- Perfiles horarios sinusoidales realistas

### Simulación
- Integración con OpenModelica (opcional)
- Simulaciones de Monte Carlo
- Estrategias: Línea Base vs. Optimizada

### Análisis y Visualización
- Estadísticas de costos y temperaturas
- Histogramas de distribución de costos
- Mapas de calor de temperaturas horarias
- Comparación entre estrategias

## Uso

### Ejecución
```bash
python main.py
```

**El script ejecuta automáticamente:**
1. 100 simulaciones Monte Carlo para estrategia "Línea Base"
2. 100 simulaciones Monte Carlo para estrategia "Optimizada"  
3. Análisis estadístico comparativo
4. Generación de gráficos en la carpeta `graphs/`

### Configuración
Modifica `config/settings.py` para ajustar:
- Número de simulaciones
- Parámetros climáticos
- Configuración de gráficos

## Parámetros Climáticos

- **Temperatura mínima**: 21°C (mediana), σ = 1.177
- **Temperatura máxima**: 36°C (mediana), σ = 2.62
- **Hora T_min**: 6:00 ± 30 min
- **Hora T_max**: 16:00 ± 1 hora

## Salidas

El simulador genera los siguientes archivos en la carpeta `graphs/`:
- `histograma_costos_Línea Base.png` - Distribución de costos estrategia tradicional
- `histograma_costos_Optimizada.png` - Distribución de costos estrategia optimizada  
- `distribucion_temperaturas_horarias.png` - Mapa de calor de temperaturas por hora
- `diagnostico_randomizacion.png` - **Validación científica de la randomización**

## Dependencias

```bash
pip install numpy matplotlib scipy
```

### Simulaciones Avanzadas (Opcional)

Actualmente, el simulador usa **datos simulados** pero estadísticamente realistas para demostrar la metodología. Para integrar con **modelos físicos detallados** de OpenModelica:

```bash
# Instalar OpenModelica y asegurar que 'omc' esté en PATH
# Esto permite usar los modelos .mo para simulaciones físicas precisas
```

**Nota**: Las simulaciones actuales ya proporcionan resultados válidos y realistas para análisis de costos y comparación de estrategias.

## Módulos

### config/settings.py
Configuración centralizada de todos los parámetros del experimento.

### src/weather/generator.py
Funciones para generar perfiles climáticos realistas con variación diaria.

### src/simulation/runner.py
Interfaz para ejecutar simulaciones OpenModelica y recopilar resultados.

### src/analysis/statistics.py
Cálculo de estadísticas de costos y temperaturas.

### src/visualization/plots.py
Generación de todos los gráficos y visualizaciones.

## Extensiones Futuras

- Integración real con OpenModelica
- Más estrategias de control
- Análisis de sensibilidad
- Optimización de parámetros
- Interfaz gráfica de usuario
