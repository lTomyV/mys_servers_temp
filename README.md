# Simulación Probabilística de Consumo Energético en una Sala de Servidores

## 1. Objetivo

Este proyecto estima la **distribución de probabilidad del costo mensual de energía** (HVAC + TI) para una sala de servidores ubicada en una ciudad calurosa de Argentina durante el mes de **enero**.  
Utiliza un modelo físico en Python + SciPy y un análisis de Monte Carlo con perfiles climáticos reales (Open-Meteo) de **15 años**.

---

## 2. Flujo de trabajo

```
┌────────────┐      ┌─────────────────┐      ┌────────────────────┐
│  PowerShell│──►  │ Descarga JSON   │──►  │  data/*.json       │
└────────────┘      └─────────────────┘      └─────────┬──────────┘
                                                      ▼
                                      ┌───────────────────────────┐
                                      │  app.py (Flask + SciPy)   │
                                      │  • Carga series horarias  │
                                      │  • Monte Carlo (200 runs) │
                                      │  • Modelo físico (ODE)    │
                                      └────────────┬──────────────┘
                                                   ▼
                                        JSON con resultados
                                                   ▼
                                   ┌──────────────────────────┐
                                   │ Front-end (Chart.js)     │
                                   │ • Hist. costo total      │
                                   │ • Hist. costo servidores │
                                   │ • Curvas COP             │
                                   │ • Distribución T horaria │
                                   └──────────────────────────┘
```

1. **Descarga de datos climáticos**  
   Ejecutar el script PowerShell:
   ```powershell
   New-Item -ItemType Directory -Path .\data -Force | Out-Null
   $lat="-31.6"; $lon="-60.7"
   0..14 | ForEach-Object {
       $yr = 2025-$_
       $url = "https://archive-api.open-meteo.com/v1/archive?latitude=$lat&longitude=$lon&start_date=$yr-01-01&end_date=$yr-01-31&hourly=temperature_2m&timezone=auto"
       Invoke-WebRequest -Uri $url -OutFile ".\data\santa_fe_${yr}_01.json"
   }
   ```

2. **Simulación**  
   ```bash
   python app.py
   ```
   El servidor Flask expone `/api/simulate`; el front-end lanza 200 corridas de Monte Carlo en segundo plano.

3. **Visualización**  
   Abrir `http://127.0.0.1:5000` y pulsar «Simular».

---

## 3. Arquitectura del modelo

| Bloque | Descripción |
| ------ | ----------- |
| **Generador climático** | Selecciona aleatoriamente una de las series JSON (744 valores) como condición de contorno. |
| **Modelo térmico** | Nodo lumped-capacity de 2 MJ/K; balance<br/>`dT/dt = (Q_servers + Q_transmission − Q_cooling)/C_th`. |
| **Transmisión** | `Q_transmission = U·A·(T_ambient − T_room)` con `A = 126 m²`, `U = 5.5 W/m²K`. |
| **HVAC** | `Q_max = 30 kW`; COP dependiente de T según catálogo degradado (económico/eficiente/premium). |
| **Control** | Banda muerta 22–26 °C: prende si `T_room > 26 °C` o si `COP>3` y `T_room>22 °C`. |
| **Energía TI** | Carga fija `Q_servers = 45 kW`. |
| **Costo** | `(E_HVAC + E_servers)·0.13 USD/kWh`. |

---

## 4. Correcciones realizadas

| Problema original | Consecuencia | Corrección |
|-------------------|--------------|------------|
| **C_th = 150 kJ/K** (∼360 K/h) | HVAC casi nunca encendía → costo muy bajo. | `C_th = 2 MJ/K` (aire + racks + estructura). |
| **COP ~4.8 @ 25 °C** (demasiado optimista) | Subestimación del consumo HVAC. | Curvas COP bajadas 15 %. |
| **Q_max = 18 kW** ≈ Q_servers | El control se saturaba y apagaba prematuramente. | `Q_max = 30 kW`. |
| **Tarifa 0.18 USD/kWh** (no coincidía con consigna) | Inconsistencia con enunciado. | `costo_kWh = 0.13`. |
| **15 kW de IT** (equivale a un solo rack) | Costos ∼1 900 USD → "barato". | `Q_servers = 45 kW` (2-3 racks típicos). |
| **U = 4 W/m²K** | Menor carga de transmisión. | `U = 5.5 W/m²K` (mampostería sin aislamiento). |
| **Un solo perfil climático** | Sin dispersión → histograma vacío / Costo90 = media. | Carga 15 años y selección aleatoria por simulación. |
| Falta de histograma TI | No se veía cuánto pesa el HVAC. | Histograma aparte `Costo Servidores`. |

---

## 5. Resultados con configuración actual (200 corridas)

| Métrica | Servidores | Total (HVAC + TI) |
|---------|-----------|--------------------|
| Media   | ≈ 4 350 USD | ≈ 5 000 USD |
| Desv. σ | 0          | ≈ 520 USD |
| Costo90 | 4 350 USD  | ≈ 5 650 USD |

El coste TI domina (~87 %), lo cual es coherente con un PUE ≈ 1.15–1.25 para equipos inverter.

---

## 6. Cómo modificar escenarios

| Parámetro | Ubicación | Comentario |
|-----------|-----------|------------|
| Potencia IT | `PARAMS_FISICOS['Q_servers']` | 30–60 kW según cantidad de racks. |
| Tarifa | `PARAMS_FISICOS['costo_kWh']` | Cambiar a tarifa local real. |
| Aislación | `PARAMS_FISICOS['U']` | 3 W/m²K (alto nivel de aislamiento) – 7 W/m²K (muy precario). |
| COP | `MODELOS_REFRIGERACION[...]` | Ajustar lambdas si se dispone de datos de placa. |
| Años climáticos | `data/*.json` | Añadir o quitar archivos para ampliar / reducir dispersión. |

---

## 7. Ejecución automática de Monte Carlo independiente (CLI)

```bash
python cli_montecarlo.py --runs 1000 --modelo eficiente
```
Genera `results_cli.json` y gráficos PNG sin lanzar la UI.

---

© 2025 – Trabajo Práctico Integrador – Modelado y Simulación de Sistemas (Ficticio)
