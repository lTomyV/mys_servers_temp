"""
Modelo físico completo para simulación de     # Parámetros del controlador PID (más agresivos para mejor control)
    kp: float = 50.0   # Ganancia proporcional (aumentada)
    ki: float = 2.0    # Ganancia integral (aumentada)
    kd: float = 10.0   # Ganancia derivativa (aumentada) de servidores.
Incluye transferencia de calor a través de paredes de concreto y control dinámico de refrigeración.
"""

import numpy as np
import logging
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class SalaServidoresConfig:
    """Configuración de parámetros físicos de la sala de servidores."""
    
    # Parámetros de la sala
    largo_sala: float = 6.0  # m
    ancho_sala: float = 4.0  # m
    alto_sala: float = 3.0   # m
    
    # Parámetros de las paredes de concreto
    espesor_pared: float = 0.20  # m (20 cm de concreto)
    conductividad_concreto: float = 1.7  # W/(m·K) - concreto normal
    area_paredes_exteriores: float = 60.0  # m² - área total expuesta al exterior
    
    # Parámetros del aire interior
    densidad_aire: float = 1.2  # kg/m³
    calor_especifico_aire: float = 1005  # J/(kg·K)
    volumen_aire: float = 72.0  # m³ (6×4×3)
    
    # Parámetros del servidor
    masa_servidor: float = 50.0  # kg
    calor_especifico_servidor: float = 900.0  # J/(kg·K)
    potencia_servidor: float = 600.0  # W - calor generado por el servidor (más conservador)
    coef_transferencia_servidor: float = 15.0  # W/(m²·K) - convección aire-servidor (reducido)
    area_superficie_servidor: float = 2.5  # m² - área de transferencia
    
    # Parámetros de la carcasa del servidor
    masa_carcasa: float = 10.0  # kg
    espesor_carcasa: float = 0.005  # m (5 mm para menor conducción)
    conductividad_carcasa: float = 50.0  # W/(m·K) - conductividad más baja
    area_carcasa: float = 2.0  # m² - área de la carcasa
    
    # Parámetros del sistema de refrigeración
    eficiencia_refrigeracion: float = 3.0  # COP del sistema (más conservador)
    potencia_min_refrigeracion: float = 1500.0  # W (aumentado mucho más)
    potencia_max_refrigeracion: float = 8000.0  # W (incrementado significativamente)
    
    # Parámetros del controlador PID (mucho más conservadores)
    kp: float = 30.0   # Ganancia proporcional (muy reducida)
    ki: float = 1.0    # Ganancia integral (muy reducida)
    kd: float = 0.5    # Ganancia derivativa (muy reducida)
    temp_objetivo: float = 24.5  # °C - temperatura objetivo de la carcasa


class ModeloSalaServidores:
    """Modelo físico completo de la sala de servidores con control dinámico."""
    
    def __init__(self, config: SalaServidoresConfig = None):
        """
        Inicializa el modelo físico.
        
        Args:
            config: Configuración de parámetros físicos
        """
        self.config = config if config is not None else SalaServidoresConfig()
        self.logger = logging.getLogger(__name__)
        
        # Calcular constantes derivadas
        self._calcular_constantes()
        
        # Estado del controlador PID
        self.reset_controlador()
    
    def _calcular_constantes(self):
        """Calcula constantes derivadas de los parámetros."""
        c = self.config
        
        # Resistencia térmica de la pared de concreto
        self.resistencia_pared = c.espesor_pared / (c.conductividad_concreto * c.area_paredes_exteriores)
        
        # Capacidad térmica del aire interior
        self.capacidad_aire = c.densidad_aire * c.volumen_aire * c.calor_especifico_aire
        
        # Capacidad térmica del servidor
        self.capacidad_servidor = c.masa_servidor * c.calor_especifico_servidor
        
        # Capacidad térmica de la carcasa
        self.capacidad_carcasa = c.masa_carcasa * c.calor_especifico_servidor
        
        # Coeficiente de transferencia aire-servidor
        self.coef_aire_servidor = c.coef_transferencia_servidor * c.area_superficie_servidor
        
        # Coeficiente de transferencia servidor-carcasa (más conservador)
        # Usando resistencia térmica en lugar de conducción directa
        resistencia_carcasa = c.espesor_carcasa / (c.conductividad_carcasa * c.area_carcasa)
        self.coef_servidor_carcasa = 1.0 / (resistencia_carcasa + 1.0/(c.coef_transferencia_servidor * c.area_carcasa))
        
        # Limitar para evitar inestabilidad numérica
        self.coef_servidor_carcasa = min(self.coef_servidor_carcasa, 1000.0)
        
        self.logger.info(f"Constantes calculadas: R_pared={self.resistencia_pared:.4f} K/W")
    
    def reset_controlador(self):
        """Reinicia el estado del controlador PID."""
        self.integral_error = 0.0
        self.error_anterior = 0.0
        self.potencia_anterior = self.config.potencia_min_refrigeracion
    
    def calcular_transferencia_calor(self, 
                                   temp_exterior: float,
                                   temp_interior: float,
                                   temp_servidor: float,
                                   temp_carcasa: float) -> Tuple[float, float, float]:
        """
        Calcula los flujos de calor en el sistema.
        
        Args:
            temp_exterior: Temperatura exterior [°C]
            temp_interior: Temperatura interior de la sala [°C]
            temp_servidor: Temperatura interna del servidor [°C]
            temp_carcasa: Temperatura de la carcasa [°C]
            
        Returns:
            Tuple con (Q_pared, Q_aire_servidor, Q_servidor_carcasa) en W
        """
        # Flujo de calor a través de la pared (exterior → interior)
        Q_pared = (temp_exterior - temp_interior) / self.resistencia_pared
        
        # Flujo de calor del aire al servidor (convección)
        Q_aire_servidor = self.coef_aire_servidor * (temp_interior - temp_servidor)
        
        # Flujo de calor del servidor a la carcasa (conducción)
        Q_servidor_carcasa = self.coef_servidor_carcasa * (temp_servidor - temp_carcasa)
        
        return Q_pared, Q_aire_servidor, Q_servidor_carcasa
    
    def controlador_pid(self, temp_carcasa: float, temp_interior: float, temp_exterior: float, dt: float) -> float:
        """
        Controlador PID mejorado para la potencia de refrigeración.
        Incluye límites realistas y control de temperatura mínima de sala.
        
        Args:
            temp_carcasa: Temperatura actual de la carcasa [°C]
            temp_interior: Temperatura actual de la sala [°C]
            temp_exterior: Temperatura exterior [°C]
            dt: Paso de tiempo [s]
            
        Returns:
            Potencia de refrigeración requerida [W]
        """
        # Error actual (respecto al objetivo de la carcasa)
        error = temp_carcasa - self.config.temp_objetivo
        
        # Término proporcional (reducido para menos agresividad)
        P = self.config.kp * error
        
        # Término integral con saturación anti-windup
        self.integral_error += error * dt
        max_integral = 200.0  # Límite más conservador
        self.integral_error = np.clip(self.integral_error, -max_integral, max_integral)
        I = self.config.ki * self.integral_error
        
        # Término derivativo
        D = self.config.kd * (error - self.error_anterior) / dt if dt > 0 else 0.0
        self.error_anterior = error
        
        # Potencia base que responde agresivamente a la temperatura exterior
        # Usar la temperatura exterior directamente para calcular la carga base
        temp_exterior_normalizada = np.clip((temp_exterior - 15.0) / 25.0, 0.0, 1.0)
        
        # Potencia base muy agresiva para mantener control estricto
        potencia_base = self.config.potencia_min_refrigeracion + \
                       (self.config.potencia_max_refrigeracion - self.config.potencia_min_refrigeracion) * \
                       (0.3 + 0.7 * temp_exterior_normalizada)  # Mínimo 30% + escalado completo
        
        # Si la temperatura de la carcasa está alta, aumentar potencia base drásticamente
        if temp_carcasa > 22.0:  # Umbral más bajo para actuar antes
            factor_urgencia = (temp_carcasa - 22.0) / 3.0  # Factor de urgencia más agresivo
            potencia_base *= (1.0 + factor_urgencia * 1.0)  # Hasta 100% adicional
        
        # Salida del controlador PID (solo ajustes finos)
        ajuste_pid = P + I + D
        
        # Limitar ajuste PID para evitar sobreactuación
        max_ajuste = self.config.potencia_max_refrigeracion * 0.3  # Máximo 30% de ajuste
        ajuste_pid = np.clip(ajuste_pid, -max_ajuste, max_ajuste)
        
        potencia_total = potencia_base + ajuste_pid
        
        # Límites de seguridad
        potencia_limitada = np.clip(potencia_total, 
                                   self.config.potencia_min_refrigeracion,
                                   self.config.potencia_max_refrigeracion)
        
        # Protección contra sobre-enfriamiento de la sala
        # Si la temperatura de la sala está muy baja, reducir potencia
        if temp_interior < 18.0:  # Temperatura mínima de sala
            factor_reduccion = np.clip((temp_interior - 15.0) / 3.0, 0.1, 1.0)
            potencia_limitada *= factor_reduccion
        
        # Suavizado para evitar cambios bruscos
        alpha = 0.9  # Factor de suavizado más conservador
        potencia_final = alpha * potencia_limitada + (1 - alpha) * self.potencia_anterior
        self.potencia_anterior = potencia_final
        
        return potencia_final
    
    def simular_paso(self, 
                     temp_exterior: float,
                     temp_interior: float, 
                     temp_servidor: float,
                     temp_carcasa: float,
                     dt: float) -> Tuple[float, float, float, float]:
        """
        Simula un paso de tiempo del sistema completo.
        
        Args:
            temp_exterior: Temperatura exterior actual [°C]
            temp_interior: Temperatura interior actual [°C]
            temp_servidor: Temperatura del servidor actual [°C]
            temp_carcasa: Temperatura de la carcasa actual [°C]
            dt: Paso de tiempo [s]
            
        Returns:
            Tuple con (nueva_temp_interior, nueva_temp_servidor, nueva_temp_carcasa, potencia_refrigeracion)
        """
        # Calcular flujos de calor
        Q_pared, Q_aire_servidor, Q_servidor_carcasa = self.calcular_transferencia_calor(
            temp_exterior, temp_interior, temp_servidor, temp_carcasa
        )
        
        # Calcular potencia de refrigeración necesaria
        potencia_refrigeracion = self.controlador_pid(temp_carcasa, temp_interior, temp_exterior, dt)
        
        # Calor removido por el sistema de refrigeración
        Q_refrigeracion = potencia_refrigeracion * self.config.eficiencia_refrigeracion
        
        # Balance energético del aire interior
        dT_interior_dt = (Q_pared - Q_aire_servidor - Q_refrigeracion) / self.capacidad_aire
        nueva_temp_interior = temp_interior + dT_interior_dt * dt
        
        # Balance energético del servidor
        dT_servidor_dt = (self.config.potencia_servidor + Q_aire_servidor - Q_servidor_carcasa) / self.capacidad_servidor
        nueva_temp_servidor = temp_servidor + dT_servidor_dt * dt
        
        # Balance energético de la carcasa
        dT_carcasa_dt = Q_servidor_carcasa / self.capacidad_carcasa
        nueva_temp_carcasa = temp_carcasa + dT_carcasa_dt * dt
        
        return nueva_temp_interior, nueva_temp_servidor, nueva_temp_carcasa, potencia_refrigeracion
        
    def simular_perfil_completo(self, 
                               temperaturas_exterior: np.ndarray,
                               tiempo: np.ndarray,
                               temp_inicial: float = 22.0) -> Dict:
        """
        Simula el perfil completo de temperaturas.
        
        Args:
            temperaturas_exterior: Array de temperaturas exteriores [°C]
            tiempo: Array de tiempos [s]
            temp_inicial: Temperatura inicial del sistema [°C]
            
        Returns:
            Diccionario con resultados de la simulación
        """
        n_puntos = len(tiempo)
        
        # Arrays de resultados
        temp_interior = np.zeros(n_puntos)
        temp_servidor = np.zeros(n_puntos)
        temp_carcasa = np.zeros(n_puntos)
        potencia_refrigeracion = np.zeros(n_puntos)
        
        # Condiciones iniciales
        temp_interior[0] = temp_inicial
        temp_servidor[0] = temp_inicial + 2.0  # Servidor ligeramente más caliente
        temp_carcasa[0] = temp_inicial + 1.0   # Carcasa intermedia
        potencia_refrigeracion[0] = self.config.potencia_min_refrigeracion
        
        # Reiniciar controlador
        self.reset_controlador()
        
        # Simulación paso a paso con verificación de estabilidad
        for i in range(1, n_puntos):
            dt = tiempo[i] - tiempo[i-1]
            
            # Limitar paso de tiempo para estabilidad numérica
            dt = min(dt, 60.0)  # Máximo 1 minuto
            
            temp_interior[i], temp_servidor[i], temp_carcasa[i], potencia_refrigeracion[i] = \
                self.simular_paso(
                    temperaturas_exterior[i-1],
                    temp_interior[i-1],
                    temp_servidor[i-1], 
                    temp_carcasa[i-1],
                    dt
                )
            
            # Verificar estabilidad numérica
            if (not np.isfinite(temp_interior[i]) or 
                not np.isfinite(temp_servidor[i]) or 
                not np.isfinite(temp_carcasa[i])):
                self.logger.error(f"Inestabilidad numérica en paso {i}")
                # Usar valores del paso anterior
                temp_interior[i] = temp_interior[i-1]
                temp_servidor[i] = temp_servidor[i-1]
                temp_carcasa[i] = temp_carcasa[i-1]
                potencia_refrigeracion[i] = potencia_refrigeracion[i-1]
        
        # Calcular métricas
        max_temp_carcasa = np.max(temp_carcasa)
        tiempo_sobre_25 = np.sum(temp_carcasa > 25.0) * (tiempo[1] - tiempo[0]) / 3600  # horas
        energia_total = float(np.trapz(potencia_refrigeracion, dx=(tiempo[1] - tiempo[0])/3600)) / 1000  # kWh
        
        return {
            'tiempo': tiempo,
            'temp_exterior': temperaturas_exterior,
            'temp_interior': temp_interior,
            'temp_servidor': temp_servidor, 
            'temp_carcasa': temp_carcasa,
            'potencia_refrigeracion': potencia_refrigeracion,
            'max_temp_carcasa': max_temp_carcasa,
            'avg_temp_carcasa': np.mean(temp_carcasa),
            'tiempo_sobre_25C': tiempo_sobre_25,
            'energia_total_kwh': energia_total,
            'potencia_promedio': np.mean(potencia_refrigeracion),
            'potencia_maxima': np.max(potencia_refrigeracion),
        }
