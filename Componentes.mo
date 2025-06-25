package Componentes
  "Componentes físicos y de control"
  extends Modelica.Icons.ComponentsPackage;

  model GeneradorClima
    "Genera temperaturas diarias min/max basadas en estadísticas"

    parameter AnalisisServidores.Datos.ParametrosClimaticos params_clima;
    parameter Integer globalSeed = 12345;
    parameter Integer localSeed = 54321;

    output Modelica.Units.SI.Temperature T_min_diaria(start=293.15);
    output Modelica.Units.SI.Temperature T_max_diaria(start=305.15);

  protected
    discrete Integer state1024(each start=0, each fixed = true);
    discrete Real u1, u2;

  initial algorithm
    state1024 := Modelica.Math.Random.Generators.Xorshift1024star.initialState(localSeed, globalSeed);
    // Generar el primer día
    (u1, state1024) := Modelica.Math.Random.Generators.Xorshift1024star.random(state1024);
    (u2, state1024) := Modelica.Math.Random.Generators.Xorshift1024star.random(state1024);
    T_min_diaria := Modelica.Math.Distributions.Normal.quantile(u1, params_clima.Tmin_mu, params_clima.Tmin_sigma);
    T_max_diaria := T_min_diaria + Modelica.Math.Distributions.Normal.quantile(u2, params_clima.DeltaT_mu, params_clima.DeltaT_sigma);

  algorithm
    when sample(0, 86400) then
      (u1, state1024) := Modelica.Math.Random.Generators.Xorshift1024star.random(pre(state1024));
      (u2, state1024) := Modelica.Math.Random.Generators.Xorshift1024star.random(pre(state1024));
      T_min_diaria := Modelica.Math.Distributions.Normal.quantile(u1, params_clima.Tmin_mu, params_clima.Tmin_sigma);
      T_max_diaria := T_min_diaria + Modelica.Math.Distributions.Normal.quantile(u2, params_clima.DeltaT_mu, params_clima.DeltaT_sigma);
    end when;

  end GeneradorClima;

  model SalaServidores
    "Modelo térmico de la sala de servidores"

    parameter AnalisisServidores.Datos.ParametrosFisicos params_fisicos;

    input Modelica.Units.SI.Temperature T_ambient "Temperatura ambiente exterior";
    input Modelica.Units.SI.Power Q_cooling "Potencia de refrigeración aplicada";

    Modelica.Units.SI.Temperature T_room(start=297.15, fixed=true) "Temperatura interior de la sala";
    Modelica.Units.SI.Power Q_transmission "Calor transmitido desde el exterior";

  equation
    Q_transmission = params_fisicos.A * params_fisicos.U * (T_ambient - T_room);
    params_fisicos.C_th * der(T_room) = params_fisicos.Q_servers + Q_transmission - Q_cooling;

  end SalaServidores;

  model HVAC
    "Modelo de consumo de potencia del sistema de refrigeración"
    parameter AnalisisServidores.Datos.ParametrosFisicos params_fisicos;

    input Modelica.Units.SI.Power Q_cooling_demand "Demanda de refrigeración";
    input Modelica.Units.SI.Temperature T_ambient "Temperatura ambiente exterior";

    output Modelica.Units.SI.Power P_electric "Potencia eléctrica consumida";
    output Modelica.Units.SI.Energy EnergiaTotal;
    output Real CostoTotal "Costo total en USD";

    Real COP "Coeficiente de Rendimiento instantáneo";

  equation
    // Curva de COP dependiente de la temperatura ambiente
    COP = AnalisisServidores.Funciones.calcularCOP(T_ambient);

    // La potencia eléctrica es la demanda de refrigeración dividida por la eficiencia
    // Se asegura que P_electric no sea negativa y se maneja la división por cero
    P_electric = if Q_cooling_demand > 1e-6 then Q_cooling_demand / max(COP, 1e-6) else 0;

    // Integrar la potencia para obtener la energía
    der(EnergiaTotal) = P_electric;

    // Calcular el costo
    // 3.6e6 J = 1 kWh
    CostoTotal = (EnergiaTotal / 3.6e6) * params_fisicos.costo_kWh;

  end HVAC;

end Componentes;