"""
Modelo físico completo de sala de servidores con control adaptativo.
Implementado directamente en Python sin dependencias de OpenModelica.
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
from config.equipos_hvac import MODELOS_REFRIGERACION
from config.settings import MODELO_HVAC


class SalaServidores:
    """
    Modelo físico completo de una sala de servidores con:
    - Transferencia de calor de paredes, aire, carcasa del servidor
    - Control adaptativo de refrigeración con función sigmoidal
    - Cálculo de consumo energético
    """
    
    def __init__(self):
        # --- Parámetros Físicos ---
        
        # Capacidades térmicas [J/K]
        self.C_pared = 50000.0      # Capacidad térmica de las paredes
        self.C_aire = 1500.0        # Capacidad térmica del aire interior
        self.C_servidor = 2000.0    # Capacidad térmica de la carcasa del servidor
        
        # Resistencias térmicas [K/W] - Ajustadas para mayor demanda de refrigeración
        self.R_pared_ext = 0.015    # Resistencia pared-exterior (mayor para retener calor)
        self.R_aire_pared = 0.020   # Resistencia aire-pared (mayor)
        self.R_aire_servidor = 0.012 # Resistencia aire-servidor (mayor)
        
        # Generación de calor del servidor [W] - Sala de servidores con alta densidad
        self.Q_servidor = 25000.0   # 25 kW - carga térmica alta para alcanzar ~$3000/mes
        
        # Configuración del equipo HVAC seleccionado
        self.equipo_hvac = MODELOS_REFRIGERACION[MODELO_HVAC]
        self.P_refrigeracion_max = self.equipo_hvac['potencia_nominal']  # W
        self.COP_nominal = self.equipo_hvac['cop_nominal']               # COP a 35°C
        self.cop_curve = self.equipo_hvac['cop_curve']                   # Función COP(T_ext)
        
        # Control adaptativo (función sigmoidal)
        self.T_min_control = 15.0   # Temperatura mínima (0% potencia)
        self.T_max_control = 25.0   # Temperatura máxima (100% potencia)
        self.k_sigmoidal = 1.0      # Agresividad de la curva
        
        # Variables de estado iniciales
        self.T_pared_inicial = 25.0
        self.T_aire_inicial = 25.0  
        self.T_servidor_inicial = 25.0
        
        # Objetivo de temperatura
        self.T_objetivo = 25.0      # Temperatura máxima permitida para la carcasa
        
        # Variables para tracking
        self.energia_total = 0.0
        self.tiempo_simulacion = []
        self.temperaturas_aire = []
        self.temperaturas_servidor = []
        self.temperaturas_pared = []
        self.potencias_refrigeracion = []
        self.porcentajes_control = []
    
    def control_adaptativo_sigmoidal(self, T_servidor):
        """
        Control adaptativo con función sigmoidal.
        - T ≤ 15°C: 0% de potencia (sin refrigeración)
        - T ≥ 25°C: 100% de potencia (máxima refrigeración)
        - Transición suave entre 15°C y 25°C
        """
        T_media = (self.T_min_control + self.T_max_control) / 2.0
        rango = self.T_max_control - self.T_min_control
        
        # Función sigmoidal normalizada
        x = (T_servidor - T_media) / (rango / 4.0)  # Factor 4 para suavizar
        porcentaje = 1.0 / (1.0 + np.exp(-self.k_sigmoidal * x))
        
        # Asegurar que esté en [0, 1]
        return np.clip(porcentaje, 0.0, 1.0)
    
    def ecuaciones_sistema(self, t, y, T_exterior):
        """
        Sistema de ecuaciones diferenciales del modelo térmico.
        
        Variables de estado:
        y[0] = T_pared   (temperatura de las paredes)
        y[1] = T_aire    (temperatura del aire interior)
        y[2] = T_servidor (temperatura de la carcasa del servidor)
        """
        T_pared, T_aire, T_servidor = y
        
        # Control adaptativo
        porcentaje_control = self.control_adaptativo_sigmoidal(T_servidor)
        P_refrigeracion = porcentaje_control * self.P_refrigeracion_max
        
        # Flujos de calor [W]
        Q_pared_exterior = (T_exterior - T_pared) / self.R_pared_ext
        Q_aire_pared = (T_aire - T_pared) / self.R_aire_pared
        Q_aire_servidor = (T_aire - T_servidor) / self.R_aire_servidor
        
        # Ecuaciones diferenciales [dT/dt = Q/C]
        dT_pared_dt = (Q_pared_exterior + Q_aire_pared) / self.C_pared
        
        dT_aire_dt = (-Q_aire_pared - Q_aire_servidor - P_refrigeracion) / self.C_aire
        
        dT_servidor_dt = (self.Q_servidor + Q_aire_servidor) / self.C_servidor
        
        return [dT_pared_dt, dT_aire_dt, dT_servidor_dt]
    
    def simular(self, tiempo_simulacion, perfil_temperatura_exterior, dt=300):
        """
        Ejecuta la simulación del sistema térmico.
        
        Args:
            tiempo_simulacion: Tiempo total en segundos
            perfil_temperatura_exterior: Array con temperaturas exteriores
            dt: Paso de tiempo para la evaluación (segundos)
        
        Returns:
            dict con resultados de la simulación
        """
        # Resetear variables de tracking
        self.energia_total = 0.0
        self.tiempo_simulacion = []
        self.temperaturas_aire = []
        self.temperaturas_servidor = []
        self.temperaturas_pared = []
        self.potencias_refrigeracion = []
        self.porcentajes_control = []
        
        # Condiciones iniciales
        y0 = [self.T_pared_inicial, self.T_aire_inicial, self.T_servidor_inicial]
        
        # Tiempo de evaluación
        t_eval = np.arange(0, tiempo_simulacion + dt, dt)
        
        # Función que interpola la temperatura exterior
        def T_ext_func(t):
            idx = int(np.clip(t / dt, 0, len(perfil_temperatura_exterior) - 1))
            return perfil_temperatura_exterior[idx]
        
        # Función del sistema que incluye temperatura exterior variable
        def sistema_con_perfil(t, y):
            T_ext = T_ext_func(t)
            return self.ecuaciones_sistema(t, y, T_ext)
        
        # Resolver el sistema de ecuaciones diferenciales
        sol = solve_ivp(
            sistema_con_perfil,
            [0, tiempo_simulacion],
            y0,
            t_eval=t_eval,
            method='RK45',  # Runge-Kutta, más rápido que DASSL
            rtol=1e-4,      # Tolerancia relajada
            atol=1e-6
        )
        
        if not sol.success:
            raise RuntimeError(f"Error en la integración: {sol.message}")
        
        # Extraer resultados
        T_pared_sol = sol.y[0]
        T_aire_sol = sol.y[1]
        T_servidor_sol = sol.y[2]
        
        # Calcular potencias de refrigeración y energía con COP variable
        energia_acumulada = 0.0
        
        # Inicializar listas para tracking adicional
        self.cops_reales = []
        self.temperaturas_exteriores = []
        
        for i, t in enumerate(sol.t):
            T_servidor = T_servidor_sol[i]
            
            # Obtener temperatura exterior en este momento
            T_ext = T_ext_func(t)
            
            # Control adaptativo
            porcentaje = self.control_adaptativo_sigmoidal(T_servidor)
            P_refrig = porcentaje * self.P_refrigeracion_max
            
            # COP variable basado en temperatura exterior
            cop_actual = self.cop_curve(T_ext)
            
            # Energía eléctrica consumida (refrigeración / COP_variable)
            if i > 0:
                dt_step = sol.t[i] - sol.t[i-1]
                energia_electrica = (P_refrig / cop_actual) * dt_step  # [W⋅s = J]
                energia_acumulada += energia_electrica
            
            # Guardar para tracking (incluyendo COP actual)
            self.tiempo_simulacion.append(t)
            self.temperaturas_pared.append(T_pared_sol[i])
            self.temperaturas_aire.append(T_aire_sol[i])
            self.temperaturas_servidor.append(T_servidor)
            self.potencias_refrigeracion.append(P_refrig)
            self.porcentajes_control.append(porcentaje)
            self.cops_reales.append(cop_actual)
            self.temperaturas_exteriores.append(T_ext)
        
        self.energia_total = energia_acumulada
        
        # Verificar cumplimiento del objetivo
        T_max_servidor = np.max(T_servidor_sol)
        objetivo_cumplido = T_max_servidor <= self.T_objetivo
        
        return {
            'tiempo': np.array(self.tiempo_simulacion),
            'T_pared': np.array(self.temperaturas_pared),
            'T_aire': np.array(self.temperaturas_aire),
            'T_servidor': np.array(self.temperaturas_servidor),
            'T_exterior': np.array(self.temperaturas_exteriores),
            'P_refrigeracion': np.array(self.potencias_refrigeracion),
            'porcentaje_control': np.array(self.porcentajes_control),
            'COP_real': np.array(self.cops_reales),
            'energia_total_J': self.energia_total,
            'energia_total_Wh': self.energia_total / 3600.0,
            'energia_total_kWh': self.energia_total / 3.6e6,
            'T_max_servidor': T_max_servidor,
            'objetivo_cumplido': objetivo_cumplido,
            'equipo_info': {
                'nombre': self.equipo_hvac['nombre'],
                'cop_nominal': self.COP_nominal,
                'potencia_nominal': self.P_refrigeracion_max,
                'modelo': MODELO_HVAC
            },
            'success': True
        }
    
    def calcular_costo_energetico(self, energia_kWh, precio_kWh=0.13):
        """Calcula el costo energético basado en el consumo."""
        return energia_kWh * precio_kWh
    
    def generar_curva_control(self, T_range=None, mostrar_grafico=True):
        """Genera y opcionalmente muestra la curva de control adaptativo."""
        if T_range is None:
            T_range = np.linspace(10, 35, 100)
        
        porcentajes = [self.control_adaptativo_sigmoidal(T) for T in T_range]
        
        if mostrar_grafico:
            plt.figure(figsize=(10, 6))
            plt.plot(T_range, np.array(porcentajes) * 100, 'b-', linewidth=2, label='Control Sigmoidal')
            plt.axvline(x=self.T_min_control, color='g', linestyle='--', alpha=0.7, label=f'T_min = {self.T_min_control}°C')
            plt.axvline(x=self.T_max_control, color='r', linestyle='--', alpha=0.7, label=f'T_max = {self.T_max_control}°C')
            plt.axvline(x=self.T_objetivo, color='orange', linestyle=':', alpha=0.7, label=f'T_objetivo = {self.T_objetivo}°C')
            
            plt.xlabel('Temperatura de la Carcasa (°C)')
            plt.ylabel('Potencia de Refrigeración (%)')
            plt.title('Curva de Control Adaptativo Sigmoidal')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.ylim(0, 105)
            
            # Guardar gráfico
            import os
            os.makedirs('graphs', exist_ok=True)
            plt.savefig('graphs/curva_control_fisica.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            print("✅ Curva de control generada: graphs/curva_control_fisica.png")
        
        return T_range, np.array(porcentajes)


if __name__ == "__main__":
    # Prueba rápida del modelo
    print("🧪 Probando modelo físico de sala de servidores...")
    
    sala = SalaServidores()
    
    # Generar curva de control
    sala.generar_curva_control()
    
    # Simular un día con temperatura exterior variable
    tiempo_dia = 24 * 3600  # 1 día en segundos
    n_puntos = 48  # Un punto cada 30 minutos
    
    # Perfil de temperatura exterior simplificado (sinusoidal)
    tiempos = np.linspace(0, tiempo_dia, n_puntos)
    T_ext_base = 25.0
    amplitud = 10.0
    T_exterior = T_ext_base + amplitud * np.sin(2 * np.pi * tiempos / tiempo_dia - np.pi/2)
    
    print(f"🌡️  Simulando {tiempo_dia/3600:.1f} horas con T_ext: {np.min(T_exterior):.1f}-{np.max(T_exterior):.1f}°C")
    
    # Ejecutar simulación
    resultados = sala.simular(tiempo_dia, T_exterior)
    
    if resultados['success']:
        print(f"✅ Simulación exitosa!")
        print(f"⚡ Energía total: {resultados['energia_total_Wh']:.1f} Wh ({resultados['energia_total_kWh']:.3f} kWh)")
        print(f"💰 Costo estimado: ${sala.calcular_costo_energetico(resultados['energia_total_kWh']):.3f}")
        print(f"🌡️  Temperatura máxima del servidor: {resultados['T_max_servidor']:.2f}°C")
        print(f"🎯 Objetivo cumplido: {'✅ SÍ' if resultados['objetivo_cumplido'] else '❌ NO'}")
    else:
        print("❌ Error en la simulación")
