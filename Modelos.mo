package Modelos
  "Modelos de sistema completos para simulación"
  extends Modelica.Icons.ModelsPackage;

  model SimulacionCompleta
    "Modelo integrado para la simulación de un mes"

    parameter AnalisisServidores.Datos.ParametrosFisicos params_fisicos;
    parameter AnalisisServidores.Datos.ParametrosClimaticos params_clima;

    // Enumeración para seleccionar la estrategia de control
    type TipoControl = enumeration(LineaBase, Optimizado);
    parameter TipoControl estrategia = TipoControl.LineaBase;

    // Parámetros para el control optimizado
    parameter Modelica.Units.SI.Temperature T_setpoint_inferior = 22 + 273.15;
    parameter Modelica.Units.SI.Temperature T_setpoint_superior = 26 + 273.15;

    // Instancias de los componentes
    Componentes.GeneradorClima generadorClima(params_clima=params_clima);
    Componentes.SalaServidores salaServidores(params_fisicos=params_fisicos);
    Componentes.HVAC hvac(params_fisicos=params_fisicos);

    Modelica.Units.SI.Temperature T_ambient_instantanea;
    Modelica.Units.SI.Power Q_cooling_calculada;

  equation
    // Conectar los componentes
    T_ambient_instantanea = Funciones.perfilTemperaturaDiaria(time, generadorClima.T_min_diaria, generadorClima.T_max_diaria);
    connect(T_ambient_instantanea, salaServidores.T_ambient);
    connect(Q_cooling_calculada, salaServidores.Q_cooling);
    connect(Q_cooling_calculada, hvac.Q_cooling_demand);
    connect(T_ambient_instantanea, hvac.T_ambient);

    // Lógica de control
    if estrategia == TipoControl.LineaBase then
      // Estrategia de termostato simple
      Q_cooling_calculada = if salaServidores.T_room > (24 + 273.15) then params_fisicos.Q_max_cooling else 0;
    else
      // Estrategia de pre-enfriamiento con banda muerta
      Q_cooling_calculada = if salaServidores.T_room > T_setpoint_superior then params_fisicos.Q_max_cooling
                         else if salaServidores.T_room > T_setpoint_inferior and hvac.COP > 3.0 then params_fisicos.Q_max_cooling // Enfriar solo si es eficiente
                         else 0;
    end if;

  end SimulacionCompleta;

end Modelos;