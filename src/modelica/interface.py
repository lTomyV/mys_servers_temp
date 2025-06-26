"""
Interfaz para integrar los modelos de Modelica con la simulación de Monte Carlo.
Maneja la comunicación entre Python y OpenModelica.
"""

import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import tempfile
import subprocess
import json
import logging
from pathlib import Path

class ModelicaInterface:
    """Interfaz para ejecutar simulaciones de Modelica desde Python."""
    
    def __init__(self, model_path: str, working_dir: str = None):
        """
        Inicializa la interfaz de Modelica.
        
        Args:
            model_path: Ruta al archivo .mo principal
            working_dir: Directorio de trabajo (opcional)
        """
        self.model_path = Path(model_path)
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.logger = logging.getLogger(__name__)
        
        # Verificar que OpenModelica esté disponible
        self.omc_path = self._find_openmodelica()
        self.modelica_available = self._check_openmodelica()
        
    def _find_openmodelica(self) -> Optional[str]:
        """Busca la instalación de OpenModelica en ubicaciones típicas de Windows."""
        # Ubicaciones típicas de instalación en Windows
        possible_paths = [
            "omc",  # Si está en PATH
            r"C:\OpenModelica\bin\omc.exe",
            r"C:\Program Files\OpenModelica\bin\omc.exe",
            r"C:\Program Files (x86)\OpenModelica\bin\omc.exe",
        ]
        
        # También buscar en variables de entorno
        om_home = os.environ.get('OPENMODELICAHOME')
        if om_home:
            omc_path = os.path.join(om_home, 'bin', 'omc.exe')
            possible_paths.insert(1, omc_path)  # Alta prioridad después de PATH
        
        # Buscar versiones específicas
        for drive in ['C:', 'D:', 'E:']:
            for version in ['1.21.0', '1.22.0', '1.23.0', '1.24.0', '1.25.0', '1.25.1']:
                possible_paths.append(f"{drive}\\OpenModelica{version}\\bin\\omc.exe")
                possible_paths.append(f"{drive}\\Program Files\\OpenModelica{version}-64bit\\bin\\omc.exe")
        
        for path in possible_paths:
            try:
                if path == "omc":
                    # Probar si está en PATH
                    result = subprocess.run([path, '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        return path
                else:
                    # Verificar si el archivo existe
                    if os.path.isfile(path):
                        result = subprocess.run([path, '--version'], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            return path
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                continue
        
        return None
        
    def _check_openmodelica(self) -> bool:
        """Verifica que OpenModelica esté instalado y accesible."""
        if not self.omc_path:
            self.logger.warning("OpenModelica no encontrado en ubicaciones típicas")
            self.logger.info("Para instalar OpenModelica, visite: https://openmodelica.org/download/")
            return False
            
        try:
            result = subprocess.run([self.omc_path, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.info(f"OpenModelica encontrado en: {self.omc_path}")
                self.logger.info(f"Versión: {result.stdout.strip()}")
                return True
            else:
                self.logger.warning(f"OpenModelica no responde correctamente: {result.stderr}")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, RuntimeError) as e:
            self.logger.warning(f"Error al verificar OpenModelica: {e}")
            return False
    
    def simulate_server_temperature(self, 
                                  exterior_temp: np.ndarray,
                                  time_vector: np.ndarray,
                                  cooling_power: float = 1000.0,
                                  initial_temp: float = 20.0) -> Dict:
        """
        Simula la temperatura del servidor usando el modelo de Modelica.
        Si OpenModelica no está disponible, usa un modelo simplificado.
        
        Args:
            exterior_temp: Temperatura exterior [°C] como función del tiempo
            time_vector: Vector de tiempo [s]
            cooling_power: Potencia de refrigeración [W]
            initial_temp: Temperatura inicial del servidor [°C]
            
        Returns:
            Dict con resultados de la simulación
        """
        try:
            return self._run_modelica_simulation(
                exterior_temp, time_vector, cooling_power, initial_temp
            )
        except Exception as e:
            self.logger.warning(f"Simulación de Modelica falló: {e}")
            self.logger.info("Usando modelo físico simplificado como respaldo")
            return self._run_simplified_simulation(
                exterior_temp, time_vector, cooling_power, initial_temp
            )
    
    def _run_modelica_simulation(self, 
                               exterior_temp: np.ndarray,
                               time_vector: np.ndarray,
                               cooling_power: float,
                               initial_temp: float) -> Dict:
        """Ejecuta la simulación usando OpenModelica."""
        
        if not self.modelica_available or not self.omc_path:
            raise RuntimeError("OpenModelica no está disponible")
        
        # Crear archivo de entrada temporal con los datos
        input_data = self._create_input_file(exterior_temp, time_vector)
        
        # Convertir la ruta del modelo para OpenModelica (usar barras normales)
        model_path_str = str(self.model_path).replace('\\', '/')
        
        # Script de OpenModelica
        mo_script = f"""
        loadFile("{model_path_str}");
        simulate(temperatura_servidor, 
                startTime=0, 
                stopTime={time_vector[-1]}, 
                numberOfIntervals={len(time_vector)-1},
                outputFormat="csv");
        """
        
        # Ejecutar simulación
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mos', delete=False) as f:
            f.write(mo_script)
            script_path = f.name
        
        try:
            result = subprocess.run(
                [self.omc_path, script_path],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise RuntimeError(f"Error en simulación de Modelica: {result.stderr}")
            
            self.logger.info("Simulación de Modelica ejecutada exitosamente")
            self.logger.debug(f"Salida de OMC: {result.stdout}")
            
            # Leer resultados
            return self._parse_modelica_results()
            
        finally:
            os.unlink(script_path)
    
    def _run_simplified_simulation(self, 
                                 exterior_temp: np.ndarray,
                                 time_vector: np.ndarray,
                                 cooling_power: float,
                                 initial_temp: float) -> Dict:
        """
        Modelo físico completo de sala de servidores con paredes de concreto.
        Simula transferencia de calor exterior → sala → servidor → carcasa.
        """
        
        # Importar el modelo físico completo
        from ..simulation.modelo_fisico_completo import ModeloSalaServidores, SalaServidoresConfig
        
        # Configurar el modelo con parámetros realistas
        config = SalaServidoresConfig(
            # Sala de servidores típica
            largo_sala=6.0,
            ancho_sala=4.0, 
            alto_sala=3.0,
            
            # Paredes de concreto
            espesor_pared=0.25,  # 25 cm
            conductividad_concreto=1.7,  # W/(m·K)
            area_paredes_exteriores=65.0,  # m²
            
            # Servidor con mayor potencia
            potencia_servidor=1200.0,  # W
            masa_servidor=80.0,  # kg
            
            # Sistema de refrigeración eficiente
            eficiencia_refrigeracion=3.5,  # COP
            potencia_min_refrigeracion=300.0,  # W
            potencia_max_refrigeracion=12000.0,  # W
            
            # Control PID ajustado para respuesta rápida
            kp=200.0,
            ki=15.0,
            kd=8.0,
            temp_objetivo=24.5,  # Mantener bajo 25°C
        )
        
        # Crear modelo
        modelo = ModeloSalaServidores(config)
        
        # Ejecutar simulación
        resultados = modelo.simular_perfil_completo(
            temperaturas_exterior=exterior_temp,
            tiempo=time_vector,
            temp_inicial=initial_temp
        )
        
        # Adaptar formato de salida para compatibilidad
        return {
            'time': resultados['tiempo'],
            'T_exterior': resultados['temp_exterior'],
            'T_interior': resultados['temp_interior'],  # Nueva: temperatura de la sala
            'T_server': resultados['temp_servidor'],
            'T_case': resultados['temp_carcasa'],
            'cooling_power': resultados['potencia_refrigeracion'],  # Ahora es variable
            'max_case_temp': resultados['max_temp_carcasa'],
            'avg_case_temp': resultados['avg_temp_carcasa'],
            'time_above_25C': resultados['tiempo_sobre_25C'],
            'total_energy': resultados['energia_total_kwh'],
            'avg_cooling_power': resultados['potencia_promedio'],
            'max_cooling_power': resultados['potencia_maxima'],
        }
    
    def optimize_cooling_power(self, 
                             exterior_temp: np.ndarray,
                             time_vector: np.ndarray,
                             target_temp: float = 25.0,
                             tolerance: float = 0.5) -> Dict:
        """
        Optimiza la potencia de refrigeración para mantener T_case < target_temp.
        Ahora con control dinámico hora por hora.
        
        Args:
            exterior_temp: Temperatura exterior
            time_vector: Vector de tiempo
            target_temp: Temperatura objetivo máxima [°C]
            tolerance: Tolerancia en la temperatura [°C]
            
        Returns:
            Dict con los resultados de simulación con control dinámico
        """
        
        # Con el nuevo modelo, la potencia ya es optimizada dinámicamente
        # Solo necesitamos ejecutar la simulación una vez
        results = self.simulate_server_temperature(
            exterior_temp, time_vector, cooling_power=1000.0, initial_temp=20.0
        )
        
        # Calcular potencia promedio para compatibilidad
        avg_power = np.mean(results['cooling_power'])
        results['optimal_power'] = avg_power
        
        return results
    
    def _create_input_file(self, exterior_temp: np.ndarray, time_vector: np.ndarray) -> str:
        """Crea archivo de entrada para Modelica."""
        data = pd.DataFrame({
            'time': time_vector,
            'T_exterior': exterior_temp
        })
        
        input_file = self.working_dir / 'temp_input.csv'
        data.to_csv(input_file, index=False)
        return str(input_file)
    
    def _parse_modelica_results(self) -> Dict:
        """Parsea los resultados de la simulación de Modelica."""
        # Buscar archivo de resultados en varias ubicaciones
        possible_patterns = [
            '*_res.csv',
            '*_res.mat',
            'temperatura_servidor_res.csv',
            'temperatura_servidor_res.mat',
        ]
        
        result_files = []
        for pattern in possible_patterns:
            files = list(self.working_dir.glob(pattern))
            result_files.extend(files)
        
        self.logger.debug(f"Archivos encontrados: {[str(f) for f in result_files]}")
        
        if not result_files:
            # Listar todos los archivos en el directorio para debugging
            all_files = list(self.working_dir.iterdir())
            self.logger.error(f"No se encontraron archivos de resultados")
            self.logger.debug(f"Archivos en directorio: {[f.name for f in all_files]}")
            raise FileNotFoundError("No se encontraron archivos de resultados de Modelica")
        
        # Usar el archivo más reciente
        result_file = max(result_files, key=os.path.getctime)
        self.logger.info(f"Leyendo resultados desde: {result_file}")
        
        try:
            if result_file.suffix.lower() == '.csv':
                data = pd.read_csv(result_file)
            else:
                # Para archivos .mat, necesitaríamos scipy.io
                raise NotImplementedError("Soporte para archivos .mat no implementado")
            
            return {
                'time': data['time'].values,
                'T_exterior': data.get('T_exterior', pd.Series([])).values,
                'T_server': data.get('T_server', pd.Series([])).values,
                'T_case': data.get('T_case', pd.Series([])).values,
                'cooling_power': data.get('cooling_power', pd.Series([])).values,
                'max_case_temp': np.max(data.get('T_case', [0])),
                'avg_case_temp': np.mean(data.get('T_case', [0])),
            }
        except Exception as e:
            self.logger.error(f"Error al leer archivo de resultados: {e}")
            raise


class ModelicaSimulationRunner:
    """Ejecutor de simulaciones de Monte Carlo con Modelica."""
    
    def __init__(self, model_path: str, config: Dict):
        """
        Inicializa el ejecutor de simulaciones.
        
        Args:
            model_path: Ruta al modelo de Modelica
            config: Configuración de la simulación
        """
        self.model_interface = ModelicaInterface(model_path)
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def run_daily_simulation(self, 
                           daily_profile: Dict,
                           day_number: int = 1) -> Dict:
        """
        Ejecuta una simulación diaria completa.
        
        Args:
            daily_profile: Perfil de temperatura diario
            day_number: Número del día (para logging)
            
        Returns:
            Resultados de la simulación del día
        """
        
        # Crear vector de tiempo (24 horas, resolución de 1 minuto)
        time_hours = np.linspace(0, 24, 24*60+1)
        time_seconds = time_hours * 3600
        
        # Interpolar temperatura exterior
        temp_profile = self._interpolate_temperature_profile(
            daily_profile, time_hours
        )
        
        # Optimizar potencia de refrigeración
        results = self.model_interface.optimize_cooling_power(
            temp_profile, time_seconds
        )
        
        # Agregar información del día
        results.update({
            'day_number': day_number,
            'min_exterior_temp': daily_profile['min_temp'],
            'max_exterior_temp': daily_profile['max_temp'],
            'min_temp_hour': daily_profile['min_temp_hour'],
            'max_temp_hour': daily_profile['max_temp_hour'],
        })
        
        self.logger.info(
            f"Día {day_number}: T_ext={daily_profile['min_temp']:.1f}-{daily_profile['max_temp']:.1f}°C, "
            f"T_case_max={results['max_case_temp']:.1f}°C, "
            f"P_opt={results['optimal_power']:.0f}W, "
            f"E_total={results['total_energy']:.2f}kWh"
        )
        
        return results
    
    def _interpolate_temperature_profile(self, 
                                       daily_profile: Dict, 
                                       time_hours: np.ndarray) -> np.ndarray:
        """
        Interpola el perfil de temperatura diario.
        
        Args:
            daily_profile: Datos del perfil diario
            time_hours: Vector de tiempo en horas
            
        Returns:
            Temperatura interpolada para cada punto temporal
        """
        
        # Puntos de control para la interpolación
        min_hour = daily_profile['min_temp_hour']
        max_hour = daily_profile['max_temp_hour']
        min_temp = daily_profile['min_temp']
        max_temp = daily_profile['max_temp']
        
        # Crear curva sinusoidal suavizada
        # Asumir que min_temp ocurre al amanecer y max_temp en la tarde
        temp_profile = np.zeros_like(time_hours)
        
        for i, hour in enumerate(time_hours):
            # Modelo sinusoidal simple con offset
            phase = (hour - min_hour) * 2 * np.pi / 24
            temp_amplitude = (max_temp - min_temp) / 2
            temp_mean = (max_temp + min_temp) / 2
            
            # Ajuste para que el máximo ocurra a la hora correcta
            phase_shift = (max_hour - min_hour) * 2 * np.pi / 24 - np.pi/2
            
            temp_profile[i] = temp_mean + temp_amplitude * np.sin(phase - phase_shift)
        
        # Suavizar con un poco de ruido realista
        noise = np.random.normal(0, 0.5, len(temp_profile))
        temp_profile += noise
        
        return temp_profile
    
    def run_monte_carlo_simulation(self, 
                                 daily_profiles: List[Dict],
                                 save_individual_results: bool = False) -> Dict:
        """
        Ejecuta la simulación completa de Monte Carlo.
        
        Args:
            daily_profiles: Lista de perfiles diarios
            save_individual_results: Si guardar resultados individuales
            
        Returns:
            Resultados agregados de la simulación
        """
        
        all_results = []
        total_energy = 0.0
        max_case_temps = []
        optimal_powers = []
        
        self.logger.info(f"Iniciando simulación Monte Carlo con {len(daily_profiles)} días")
        
        for i, profile in enumerate(daily_profiles, 1):
            try:
                results = self.run_daily_simulation(profile, i)
                all_results.append(results)
                
                total_energy += results['total_energy']
                max_case_temps.append(results['max_case_temp'])
                optimal_powers.append(results['optimal_power'])
                
                # Progress update cada 10%
                if i % max(1, len(daily_profiles) // 10) == 0:
                    progress = 100 * i / len(daily_profiles)
                    self.logger.info(f"Progreso: {progress:.0f}% ({i}/{len(daily_profiles)} días)")
                    
            except Exception as e:
                self.logger.error(f"Error en día {i}: {e}")
                continue
        
        # Calcular estadísticas agregadas
        aggregated_results = {
            'total_days': len(all_results),
            'total_energy_kwh': total_energy,
            'average_daily_energy_kwh': total_energy / len(all_results) if all_results else 0,
            'max_case_temperature': np.max(max_case_temps) if max_case_temps else 0,
            'mean_max_case_temperature': np.mean(max_case_temps) if max_case_temps else 0,
            'std_max_case_temperature': np.std(max_case_temps) if max_case_temps else 0,
            'mean_optimal_power': np.mean(optimal_powers) if optimal_powers else 0,
            'std_optimal_power': np.std(optimal_powers) if optimal_powers else 0,
            'days_above_25C': sum(1 for temp in max_case_temps if temp > 25.0),
            'percentage_days_above_25C': 100 * sum(1 for temp in max_case_temps if temp > 25.0) / len(max_case_temps) if max_case_temps else 0,
        }
        
        if save_individual_results:
            aggregated_results['individual_results'] = all_results
            
        self.logger.info("Simulación Monte Carlo completada")
        self.logger.info(f"Energía total: {aggregated_results['total_energy_kwh']:.1f} kWh")
        self.logger.info(f"Temperatura máxima de carcasa: {aggregated_results['max_case_temperature']:.1f}°C")
        self.logger.info(f"Días con T > 25°C: {aggregated_results['days_above_25C']} ({aggregated_results['percentage_days_above_25C']:.1f}%)")
        
        return aggregated_results
