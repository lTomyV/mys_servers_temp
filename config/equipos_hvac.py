"""
Configuración de equipos de refrigeración basados en datos reales de fabricantes HVAC.
"""

# Datos técnicos de fabricantes de equipos HVAC comerciales
MODELOS_REFRIGERACION = {
    'economico': {
        'nombre': 'Economico (Estándar)',
        'cop_nominal': 2.8,  # COP a 35°C exterior
        'potencia_nominal': 55000,  # W - 55kW para manejar 25kW de carga + margen
        'precio': 3500,  # USD
        'vida_util': 8,  # años
        'mantenimiento_anual': 280,  # USD/año
        # COP ≈ 2.8 @35°C; cae 0.05 por °C hacia arriba
        'cop_curve': lambda t: max(1.0, 2.8 - 0.05 * (t - 35))
    },
    'eficiente': {
        'nombre': 'Eficiente (Inverter)',
        'cop_nominal': 3.2,  # COP a 35°C exterior
        'potencia_nominal': 55000,  # W - 55kW para manejar 25kW de carga + margen
        'precio': 5800,  # USD
        'vida_util': 12,  # años
        'mantenimiento_anual': 220,  # USD/año
        # COP variable más realista
        'cop_curve': lambda t: max(1.2, 3.2 - 0.06 * (t - 35))
    },
    'premium': {
        'nombre': 'Premium (VRF)',
        'cop_nominal': 3.8,  # COP a 35°C exterior
        'potencia_nominal': 55000,  # W - 55kW para manejar 25kW de carga + margen
        'precio': 9200,  # USD
        'vida_util': 15,  # años
        'mantenimiento_anual': 180,  # USD/año
        # COP variable premium
        'cop_curve': lambda t: max(1.5, 3.8 - 0.07 * (t - 35))
    }
}

# Modelo por defecto para usar en las simulaciones
MODELO_DEFAULT = 'eficiente'
