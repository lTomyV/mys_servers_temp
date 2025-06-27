"""
Módulo para ejecutar simulaciones de OpenModelica con control adaptativo.
Mantiene limpio el directorio principal usando carpetas temporales.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import numpy as np

# Agregar el directorio raíz al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.settings import MODEL_NAME, SIMULATION_TIME, SIMULATION_INTERVALS, COST_PER_KWH
from src.weather.generator import generate_weather_profile, generate_hourly_temperature_profile


def create_and_run_adaptive_simulation(run_id):
    """
    Crea un script.mos para simulación adaptativa, lo ejecuta en directorio temporal
    y devuelve el costo y temperaturas.
    """
    
    # Crear directorio temporal para esta simulación
    temp_dir = os.path.join("temp", f"sim_{run_id}")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Guardar directorio actual
    original_dir = os.getcwd()
    
    try:
        # Cambiar al directorio temporal
        os.chdir(temp_dir)
        
        # Copiar el archivo .mo al directorio temporal
        shutil.copy2(os.path.join(original_dir, "AnalisisServidores.mo"), ".")
        
        # Generar perfil climático para esta ejecución
        t_min_daily, t_max_daily, hour_min_daily, hour_max_daily = generate_weather_profile()
        
        # Generar perfil horario de temperatura
        hourly_temps = generate_hourly_temperature_profile(t_min_daily, t_max_daily, hour_min_daily, hour_max_daily)

        # Crear el contenido del script.mos optimizado para velocidad
        mos_script_content = f"""
        loadFile("AnalisisServidores.mo");
        setCommandLineOptions("-d=newInst,--maxSizeLinearTearing=4000,--maxSizeNonlinearTearing=4000");
        simulate(
            {MODEL_NAME},
            startTime=0,
            stopTime={SIMULATION_TIME},
            numberOfIntervals={SIMULATION_INTERVALS},
            method="euler",
            tolerance=1e-4,
            fileNamePrefix="SimulacionAdaptativa_{run_id}"
        );
        quit();
        """
        
        # Escribir el script a un archivo
        script_path = f"run_{run_id}.mos"
        with open(script_path, "w") as f:
            f.write(mos_script_content)
        
        # Ejecutar OpenModelica
        omc_path = r"C:\Program Files\OpenModelica1.25.1-64bit\bin\omc.exe"
        print(f"🚀 Ejecutando simulación adaptativa {run_id}...")
        print(f"📁 Directorio de trabajo: {os.getcwd()}")
        print(f"📄 Script: {script_path}")
        
        process = subprocess.run([omc_path, script_path], 
                                capture_output=True, 
                                text=True, 
                                timeout=300)  # 5 minutos timeout para 1 día
        
        print(f"🔍 Return code: {process.returncode}")
        if process.stdout:
            print(f"📤 Stdout: {process.stdout[:500]}...")
        if process.stderr:
            print(f"📥 Stderr: {process.stderr[:500]}...")
        
        if process.returncode != 0:
            print(f"❌ Error en simulación {run_id}")
            print(f"   Stdout: {process.stdout}")
            print(f"   Stderr: {process.stderr}")
            return None, None
        
        # Buscar archivo de resultados .mat
        mat_file = f"SimulacionAdaptativa_{run_id}_res.mat"
        if os.path.exists(mat_file):
            # Extraer energía final y temperaturas
            energia_wh = extract_final_energy_from_results(mat_file)
            temperaturas = extract_temperatures_from_results(mat_file)
            
            if energia_wh is not None:
                # Convertir a costo mensual
                energia_kwh = energia_wh / 1000.0
                costo_mensual = energia_kwh * COST_PER_KWH
                
                print(f"✅ Simulación {run_id} completada: ${costo_mensual:.2f}")
                return costo_mensual, temperaturas
            else:
                print(f"⚠️  No se pudo extraer energía de simulación {run_id}")
                return None, None
        else:
            print(f"❌ No se encontró archivo .mat para simulación {run_id}")
            return None, None
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout en simulación {run_id}")
        return None, None
    except Exception as e:
        print(f"❌ Error inesperado en simulación {run_id}: {e}")
        return None, None
    
    finally:
        # Volver al directorio original
        os.chdir(original_dir)
        
        # Opcional: Limpiar directorio temporal (comentar si quieres conservar archivos)
        try:
            shutil.rmtree(temp_dir)
        except:
            pass  # No importa si no se puede limpiar


def extract_final_energy_from_results(result_file):
    """Extrae la energía final del archivo de resultados usando mapeo de posiciones."""
    try:
        import scipy.io
        
        if os.path.exists(result_file):
            data = scipy.io.loadmat(result_file)
            
            # Primero intentar método directo
            if 'energiaTotal' in data:
                energia_valores = data['energiaTotal'][0]
                return energia_valores[-1]
            
            # Usar mapeo de posiciones para OpenModelica
            if 'data_2' in data:
                datos_temporales = data['data_2']
                
                # Basado en el análisis:
                # Variable_0: tiempo (0 a 86400)
                # Variable_1: energía acumulada (0 a ~50000)
                if datos_temporales.shape[0] > 1:
                    tiempo = datos_temporales[0, :]
                    energia = datos_temporales[1, :]
                    
                    # Verificar que parece energía (creciente)
                    if len(energia) > 1 and energia[-1] > energia[0]:
                        print(f"🔍 Energía encontrada en posición 1: {energia[0]:.1f} → {energia[-1]:.1f} Wh")
                        return energia[-1]
                
                # Si no funciona, mostrar info para debug
                print(f"Variables disponibles: {[k for k in data.keys() if not k.startswith('_')]}")
                print(f"Forma data_2: {datos_temporales.shape}")
                if datos_temporales.shape[0] > 1:
                    print(f"Variable_1 (posible energía): {datos_temporales[1, 0]:.1f} → {datos_temporales[1, -1]:.1f}")
                return None
            else:
                print(f"Variables disponibles: {[k for k in data.keys() if not k.startswith('_')]}")
                return None
        else:
            return None
            
    except ImportError:
        print("⚠️  scipy no disponible para leer archivos .mat")
        return None
    except Exception as e:
        print(f"⚠️  Error extrayendo energía: {e}")
        return None


def extract_temperatures_from_results(result_file):
    """Extrae temperaturas del archivo de resultados usando mapeo de posiciones."""
    try:
        import scipy.io
        
        if os.path.exists(result_file):
            data = scipy.io.loadmat(result_file)
            
            # Primero intentar método directo
            if 'temperaturaInterior' in data:
                temps = data['temperaturaInterior'][0]
                # Remuestrear a intervalos horarios para análisis
                if len(temps) > 12:
                    indices_horarios = np.arange(0, len(temps), 12)
                    return temps[indices_horarios]
                else:
                    return temps
            
            # Usar mapeo de posiciones para OpenModelica
            if 'data_2' in data:
                datos_temporales = data['data_2']
                
                # Basado en el análisis:
                # Variable_2: temperatura interior (23-35°C)
                # Variable_4: temperatura carcasa (25-35°C)
                if datos_temporales.shape[0] > 4:
                    temp_interior = datos_temporales[2, :]  # Posición 2
                    temp_carcasa = datos_temporales[4, :]   # Posición 4
                    
                    # Verificar que están en rango de temperatura
                    if 15 < np.mean(temp_carcasa) < 50:  # Rango razonable para temperatura
                        print(f"🌡️  Temperaturas encontradas: Interior {temp_interior[0]:.1f}-{temp_interior[-1]:.1f}°C, Carcasa {temp_carcasa[0]:.1f}-{temp_carcasa[-1]:.1f}°C")
                        
                        # Remuestrear a intervalos horarios si es necesario
                        if len(temp_carcasa) > 12:
                            indices_horarios = np.arange(0, len(temp_carcasa), 12)
                            return temp_carcasa[indices_horarios]
                        else:
                            return temp_carcasa
                
                return None
            else:
                return None
        else:
            return None
            
    except ImportError:
        print("⚠️  scipy no disponible para leer archivos .mat")
        return None
    except Exception as e:
        print(f"⚠️  Error extrayendo temperaturas: {e}")
        return None


def run_monte_carlo_adaptive(num_simulations):
    """Ejecuta simulaciones Monte Carlo con control adaptativo."""
    
    print(f"\n🎯 Iniciando {num_simulations} simulaciones Monte Carlo con control adaptativo...")
    print(f"📁 Los archivos temporales se guardarán en: temp/sim_X/")
    
    # Crear directorio temp principal
    os.makedirs("temp", exist_ok=True)
    
    costs = []
    temperature_profiles = []
    successful_runs = 0
    
    for i in range(num_simulations):
        print(f"\n📊 Simulación {i+1}/{num_simulations}")
        
        cost, temps = create_and_run_adaptive_simulation(i+1)
        
        if cost is not None:
            costs.append(cost)
            if temps is not None:
                temperature_profiles.append(temps)
            successful_runs += 1
        
        # Mostrar progreso cada 10 simulaciones
        if (i+1) % 10 == 0:
            print(f"📈 Progreso: {i+1}/{num_simulations} ({successful_runs} exitosas)")
    
    print(f"\n🎉 Completadas {successful_runs}/{num_simulations} simulaciones exitosas")
    
    if successful_runs == 0:
        raise RuntimeError("❌ No se completó ninguna simulación exitosamente")
    
    return np.array(costs), temperature_profiles


if __name__ == "__main__":
    # Prueba rápida
    print("🧪 Ejecutando prueba de una simulación...")
    cost, temps = create_and_run_adaptive_simulation(999)
    
    if cost is not None:
        print(f"✅ Prueba exitosa: ${cost:.2f}")
        if temps is not None:
            print(f"📊 Temperaturas: {len(temps)} puntos, rango {np.min(temps):.1f}-{np.max(temps):.1f}°C")
    else:
        print("❌ Prueba falló")
