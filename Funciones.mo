package Funciones
  "Funciones auxiliares para el modelo"
  extends Modelica.Icons.FunctionsPackage;

  function perfilTemperaturaDiaria
    "Calcula la temperatura ambiente instantánea usando una aproximación cosenoidal"
    input Modelica.Units.SI.Time t "Tiempo actual de la simulación (s)";
    input Modelica.Units.SI.Temperature T_min "Temperatura mínima del día (K)";
    input Modelica.Units.SI.Temperature T_max "Temperatura máxima del día (K)";
    output Modelica.Units.SI.Temperature T_ambient "Temperatura ambiente instantánea (K)";
  protected
    Real periodo = 86400.0 "Periodo de 24 horas en segundos";
    Real freq_ang = 2 * Modelica.Constants.pi / periodo;
    // Asume que la T_max ocurre a las 15:00 (t=54000s) y T_min a las 5:00 (t=18000s)
    // El centro del coseno (pico) debe estar en t=54000s
    Real t_offset = 54000;
    Modelica.Units.SI.Temperature amplitud = (T_max - T_min) / 2;
    Modelica.Units.SI.Temperature linea_media = (T_max + T_min) / 2;
  algorithm
    T_ambient := linea_media + amplitud * cos(freq_ang * (t - t_offset));
  end perfilTemperaturaDiaria;

  function calcularCOP
    "Calcula el COP del HVAC en función de la temperatura ambiente"
    input Modelica.Units.SI.Temperature T_amb_K "Temperatura ambiente en Kelvin";
    output Real COP "Coeficiente de Rendimiento";
  protected
    Modelica.Units.SI.Temperature T_amb_C = T_amb_K - 273.15;
  algorithm
    COP := if T_amb_C <= 20 then 4.5
         else if T_amb_C >= 45 then 1.25
         else 4.5 - 0.15 * (T_amb_C - 20);
  end calcularCOP;

end Funciones;