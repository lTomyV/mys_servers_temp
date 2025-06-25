package AnalisisServidores
  "Librería para el análisis probabilístico y optimización de la refrigeración de salas de servidores."

  // Sub-paquetes para organizar los componentes
  package Modelos "Contiene los modelos de sistema completos"
    extends Modelica.Icons.ModelsPackage;
    // Modelos completos se definen aquí (ver A.4)
  end Modelos;

  package Componentes "Contiene los componentes físicos y de control"
    extends Modelica.Icons.ComponentsPackage;
    // Componentes individuales se definen aquí (ver A.2)
  end Componentes;

  package Funciones "Contiene funciones auxiliares"
    extends Modelica.Icons.FunctionsPackage;
    // Funciones como el perfil de temperatura se definen aquí (ver A.3)
  end Funciones;

  package Datos "Contiene registros y tipos de datos"
    extends Modelica.Icons.TypesPackage;
    // Parámetros climáticos y físicos
    record ParametrosClimaticos
      "Parámetros estadísticos para el clima de Enero"
      parameter Modelica.Units.SI.Temperature Tmin_mu = 20.1 + 273.15 "Media de T_min diaria (K)";
      parameter Modelica.Units.SI.Temperature Tmin_sigma = 2.5 "Desviación estándar de T_min diaria (K)";
      parameter Real DeltaT_mu = 11.4 "Media del rango de T diario (K)";
      parameter Real DeltaT_sigma = 3.0 "Desviación estándar del rango de T diario (K)";
    end ParametrosClimaticos;

    record ParametrosFisicos
      "Parámetros físicos de la sala de servidores y HVAC"
      parameter Modelica.Units.SI.Area A = 126 "Área de superficie externa (m^2)";
      parameter Real U = 2.5 "Coeficiente de transferencia de calor (W/m^2.K)";
      parameter Modelica.Units.SI.Power Q_servers = 10000 "Carga térmica de los servidores (W)";
      parameter Modelica.Units.SI.HeatCapacity C_th = 150000 "Capacidad térmica de la sala (J/K)";
      parameter Modelica.Units.SI.Power Q_max_cooling = 15000 "Potencia máxima de refrigeración del HVAC (W)";
      parameter Modelica.Units.SI.CostRate costo_kWh = 0.13 "Costo de la energía (USD/kWh)";
    end ParametrosFisicos;

  end Datos;

end AnalisisServidores;