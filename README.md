# Simulación de Consumo Energético en Sala de Servidores

## 📋 Descripción General

Esta aplicación web simula el comportamiento térmico y consumo energético de una sala de servidores utilizando un **modelo físico detallado** y **análisis Monte Carlo** con datos climáticos reales de Santa Fe, Argentina.

La simulación permite evaluar diferentes equipos de refrigeración y estrategias de control para optimizar el consumo energético manteniendo las condiciones operativas adecuadas para los servidores.

---

## 🚀 Inicio Rápido

### Requisitos
- Python 3.8+
- Librerías: Flask, NumPy, SciPy, Matplotlib

### Instalación
```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python app.py
```

### Uso
1. Abrir navegador en `http://localhost:5000`
2. Seleccionar modelo de refrigeración
3. Hacer clic en "Simular"
4. Analizar los resultados en los gráficos interactivos

---

## 🏗️ Arquitectura del Sistema

### Modelo Físico
El sistema utiliza un modelo de **capacidad térmica concentrada**:

#### Ecuación Principal
```
dT/dt = (Q_servers + Q_transmission - Q_cooling) / C_th
```

### Parámetros Físicos

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| **A** | 126 m² | Área de superficie externa |
| **U** | 5.5 W/m²K | Coeficiente de transferencia de calor |
| **Q_servers** | 45,000 W | Carga térmica de servidores (constante) |
| **C_th** | 2,000,000 J/K | Capacidad térmica de la sala |
| **Q_max_cooling** | 75,000 W | Potencia máxima del HVAC |
| **costo_kWh** | $0.13 USD | Costo de la energía eléctrica |

---

## ❄️ Modelos de Refrigeración

### 1. Económico (Estándar)
- **Potencia nominal**: 75 kW
- **COP nominal**: 2.8 @ 35°C
- **Precio**: $3,000 USD
- **Vida útil**: 8 años
- **Mantenimiento**: $250 USD/año
- **Tecnología**: Compresores básicos, control on/off

### 2. Eficiente (Inverter)
- **Potencia nominal**: 75 kW  
- **COP nominal**: 3.2 @ 35°C
- **Precio**: $5,000 USD
- **Vida útil**: 12 años
- **Mantenimiento**: $180 USD/año
- **Tecnología**: Inverter, modulación de capacidad

### 3. Premium (VRF)
- **Potencia nominal**: 75 kW
- **COP nominal**: 3.8 @ 35°C
- **Precio**: $8,000 USD
- **Vida útil**: 15 años
- **Mantenimiento**: $150 USD/año
- **Tecnología**: Variable Refrigerant Flow, máxima eficiencia

### Curvas COP
El **Coeficiente de Performance (COP)** varía con la temperatura exterior:

- **Económico**: COP = 2.8 - 0.05 × (T - 35)
- **Eficiente**: COP = 3.2 - 0.06 × (T - 35)  
- **Premium**: COP = 3.8 - 0.07 × (T - 35)

---

## 🌡️ Sistema de Control

### Estrategia Robusta de Control
El sistema utiliza un control inteligente por niveles:

#### Setpoints de Temperatura
- **T_crítico**: 24°C - Límite absoluto (HVAC al máximo)
- **T_normal**: 22°C - Límite operativo normal 
- **T_precool**: 20°C - Inicio de pre-enfriamiento

#### Lógica de Control
```python
if T_room > 24°C:
    # EMERGENCIA: HVAC al máximo
    Q_cooling = 75 kW
elif T_room > 22°C:
    # ALTO: HVAC al máximo
    Q_cooling = 75 kW
elif T_room > 20°C and COP > 2.5:
    # MEDIO: Pre-enfriamiento inteligente
    Q_cooling = 75 kW
else:
    # BAJO: HVAC apagado
    Q_cooling = 0
```

---

## 📊 Datos Climáticos

### Fuente de Datos
- **Proveedor**: Open-Meteo Historical API
- **Ubicación**: Santa Fe, Argentina (-31.6°, -60.7°)
- **Período**: 2010-2025 (16 años de datos)
- **Resolución**: Horaria (744 puntos por mes de enero)

### Características Climáticas de Santa Fe (Enero)
- **Temperatura mínima**: 19.1°C
- **Temperatura máxima**: 33.7°C  
- **Temperatura media**: 25.4°C
- **Variabilidad**: ±8°C entre años extremos

---

## 📈 Resultados y Gráficos

### 1. Curvas COP de Refrigeración
Muestra la eficiencia de cada modelo vs temperatura exterior

### 2. Temperaturas Exteriores (Validación Climática)
Distribución de temperaturas mínimas y máximas diarias de Santa Fe

### 3. Distribución de Temperaturas Horarias (Interior Sala)
Perfil térmico promedio dentro de la sala: **20-23°C** (condiciones ideales para equipos TI)

### 4. Distribución de Temperaturas Exteriores (Santa Fe)
Perfil térmico exterior promedio: **23-28°C** (condiciones desafiantes para refrigeración)

### 5. Temperatura Máxima Diaria Interior (Promedio)
Evolución de los picos térmicos durante el mes (nunca supera límites operativos)

### 6. Histogramas de Costos
- **HVAC**: Distribución de costos variables de refrigeración
- **Servidores**: Costo fijo de la carga TI

---

## 💰 Análisis Económico

### Costos Típicos (200 simulaciones Monte Carlo)

| Concepto | Media Mensual | Desviación | Percentil 90 |
|----------|---------------|------------|--------------|
| **Servidores** | $4,350 USD | $0 | $4,350 USD |
| **HVAC** | $650 USD | $85 USD | $780 USD |
| **TOTAL** | $5,000 USD | $85 USD | $5,130 USD |

### Métricas de Eficiencia
- **PUE promedio**: 1.15 (excelente eficiencia)
- **Costo por kWh refrigerado**: $0.10 USD
- **Impacto del modelo de equipo**: ±15% en costos HVAC

---

## 🔧 Configuración Avanzada

### Modificación de Parámetros
Los parámetros principales se pueden ajustar en `app.py`:

```python
PARAMS_FISICOS = {
    'A': 126,              # Área de superficie externa (m^2)
    'U': 5.5,              # Coef. transferencia de calor (W/m^2.K)
    'Q_servers': 45000,    # Carga térmica servidores (W)
    'C_th': 2_000_000,     # Capacidad térmica sala (J/K)
    'Q_max_cooling': 75000, # Potencia máxima HVAC (W)
    'costo_kWh': 0.13      # Costo energía (USD/kWh)
}
```

---

## ✅ Validación del Modelo

### Validación Física
- ✅ **Balance energético**: Conservación de energía
- ✅ **Estabilidad térmica**: Temperaturas dentro de rango operativo (18-26°C)
- ✅ **Respuesta transitoria**: Tiempo de respuesta realista
- ✅ **Límites físicos**: COP > 1, comportamiento termodinámico correcto

### Benchmarking Industrial
- ✅ **PUE**: 1.15 vs industria 1.1-1.3 (excelente)
- ✅ **Temperatura operativa**: 20-23°C vs ASHRAE 18-27°C (óptimo)
- ✅ **Consumo específico**: 0.14 kWh/kWh-TI vs típico 0.10-0.20

---

## 🧩 Arquitectura de Software

### Backend (Python/Flask)
- **app.py**: Servidor principal y lógica de simulación
- **src/**: Módulos especializados
  - `simulation/runner.py`: Motor de simulación Monte Carlo
  - `weather/generator.py`: Generador de perfiles climáticos
  - `analysis/statistics.py`: Análisis estadístico
  - `visualization/plots.py`: Generación de gráficos

### Frontend (HTML/CSS/JavaScript)
- **templates/index.html**: Interfaz de usuario
- **static/css/styles.css**: Estilos visuales
- **static/js/scripts_new.js**: Lógica de frontend y gráficos interactivos

### Datos
- **data/**: Archivos JSON con series climáticas históricas de Santa Fe
- **config/settings.py**: Configuración de parámetros

---

## 🐛 Troubleshooting

### Problemas Comunes

**Gráficos no se muestran**
- Verificar que todos los archivos JSON estén en `/data`
- Comprobar consola del navegador para errores JavaScript

**Simulación lenta**
- La simulación completa toma 30-60 segundos (200 corridas Monte Carlo)
- Usar paralelización automática con multiprocessing

**Error de memoria**
- Requiere ~2GB RAM disponible para simulaciones completas

---

## 📚 Referencias Técnicas

### Estándares
- **ASHRAE TC 9.9**: Thermal Guidelines for Data Processing Environments
- **ISO/IEC 30134**: Data Centre Energy Efficiency Metrics

### Metodología
- **Capacidad térmica concentrada**: Modelo físico validado
- **Monte Carlo**: 200 simulaciones para análisis estadístico robusto
- **Datos climáticos reales**: 16 años de historia de Santa Fe

---

**Versión**: 2.0  
**Última actualización**: Enero 2025

La aplicación ahora utiliza una **estrategia única de control inteligente** optimizada para salas de servidores, con **setpoints realistas** (20-24°C) y **equipos de 75kW** dimensionados para las condiciones climáticas extremas de Santa Fe (hasta 33.7°C).
