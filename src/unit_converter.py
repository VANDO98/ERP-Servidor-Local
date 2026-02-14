"""
Módulo de Conversión de Unidades de Medida

Permite convertir cantidades entre unidades compatibles de la misma familia.
Ejemplo: 500 ML → 0.5 LITRO
"""

# Definición de familias de unidades y sus factores de conversión
# Factor representa cuántas unidades base equivale 1 unidad
UNIT_FAMILIES = {
    'VOLUMEN': {
        'LITRO': 1.0,
        'ML': 0.001,
        'GLN': 3.785411784,  # Galón US
        'M3': 1000.0,
    },
    'MASA': {
        'KG': 1.0,
        'GR': 0.001,
        'TON': 1000.0,
        'LB': 0.45359237,  # Libra
    },
    'LONGITUD': {
        'METRO': 1.0,
        'CM': 0.01,
        'MM': 0.001,
    },
    'UNIDAD': {
        'UND': 1.0,
        'CAJA': 1.0,
        'BOLSA': 1.0,
        'LATE': 1.0,
    }
}

def get_unit_family(unit: str) -> str:
    """
    Retorna la familia a la que pertenece una unidad.
    
    Args:
        unit: Unidad de medida (ej: 'LITRO', 'KG')
    
    Returns:
        Nombre de la familia ('VOLUMEN', 'MASA', etc.) o 'UNIDAD' si no se encuentra
    """
    unit = unit.upper().strip()
    
    for family, units in UNIT_FAMILIES.items():
        if unit in units:
            return family
    
    # Si no se encuentra, asumir que es una unidad sin conversión
    return 'UNIDAD'

def get_compatible_units(base_unit: str) -> list:
    """
    Retorna lista de unidades compatibles (misma familia) con la unidad base.
    
    Args:
        base_unit: Unidad base del producto (ej: 'LITRO')
    
    Returns:
        Lista de unidades compatibles incluyendo la base
    """
    family = get_unit_family(base_unit)
    
    if family in UNIT_FAMILIES:
        return sorted(list(UNIT_FAMILIES[family].keys()))
    
    # Si no tiene familia conocida, solo retornar la misma unidad
    return [base_unit.upper().strip()]

def get_conversion_factor(from_unit: str, to_unit: str) -> float:
    """
    Obtiene el factor de conversión entre dos unidades.
    
    Args:
        from_unit: Unidad origen
        to_unit: Unidad destino
    
    Returns:
        Factor de conversión (cantidad_destino = cantidad_origen * factor)
        Retorna 1.0 si las unidades no son compatibles
    """
    from_unit = from_unit.upper().strip()
    to_unit = to_unit.upper().strip()
    
    # Si son la misma unidad, factor es 1
    if from_unit == to_unit:
        return 1.0
    
    # Verificar que ambas unidades pertenezcan a la misma familia
    from_family = get_unit_family(from_unit)
    to_family = get_unit_family(to_unit)
    
    if from_family != to_family:
        # Unidades incompatibles, no se puede convertir
        return 1.0
    
    # Obtener factores de conversión a la unidad base
    family_units = UNIT_FAMILIES.get(from_family, {})
    from_factor = family_units.get(from_unit, 1.0)
    to_factor = family_units.get(to_unit, 1.0)
    
    # Calcular factor de conversión
    # Ejemplo: ML a LITRO
    # from_factor = 0.001 (1 ML = 0.001 LITRO)
    # to_factor = 1.0 (1 LITRO = 1.0 LITRO)
    # conversion = 0.001 / 1.0 = 0.001
    # Entonces: 500 ML * 0.001 = 0.5 LITRO
    
    return from_factor / to_factor

def convert_quantity(quantity: float, from_unit: str, to_unit: str) -> float:
    """
    Convierte una cantidad de una unidad a otra.
    
    Args:
        quantity: Cantidad a convertir
        from_unit: Unidad origen
        to_unit: Unidad destino
    
    Returns:
        Cantidad convertida a la unidad destino
    
    Examples:
        >>> convert_quantity(500, 'ML', 'LITRO')
        0.5
        >>> convert_quantity(2.5, 'KG', 'GR')
        2500.0
        >>> convert_quantity(1, 'LITRO', 'ML')
        1000.0
    """
    factor = get_conversion_factor(from_unit, to_unit)
    return quantity * factor

def are_units_compatible(unit1: str, unit2: str) -> bool:
    """
    Verifica si dos unidades son compatibles (misma familia).
    
    Args:
        unit1: Primera unidad
        unit2: Segunda unidad
    
    Returns:
        True si pertenecen a la misma familia, False en caso contrario
    """
    return get_unit_family(unit1) == get_unit_family(unit2)

def format_conversion_info(quantity: float, from_unit: str, to_unit: str) -> str:
    """
    Genera un mensaje informativo sobre la conversión.
    
    Args:
        quantity: Cantidad original
        from_unit: Unidad origen
        to_unit: Unidad destino
    
    Returns:
        Mensaje descriptivo de la conversión
    """
    converted = convert_quantity(quantity, from_unit, to_unit)
    
    if from_unit.upper() == to_unit.upper():
        return f"{quantity} {from_unit}"
    
    return f"{quantity} {from_unit} = {converted:.4f} {to_unit}"


# Función de prueba
if __name__ == "__main__":
    # Tests básicos
    print("=== Tests de Conversión ===")
    print(format_conversion_info(500, 'ML', 'LITRO'))
    print(format_conversion_info(2.5, 'KG', 'GR'))
    print(format_conversion_info(1, 'LITRO', 'ML'))
    print(format_conversion_info(3.785, 'GLN', 'LITRO'))
    
    print("\n=== Unidades Compatibles ===")
    print(f"LITRO: {get_compatible_units('LITRO')}")
    print(f"KG: {get_compatible_units('KG')}")
    print(f"UND: {get_compatible_units('UND')}")
