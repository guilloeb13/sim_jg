"""
Funciones de utilidad
"""

import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia entre dos puntos usando la fórmula de Haversine

    Args:
        lat1, lon1: Coordenadas del primer punto
        lat2, lon2: Coordenadas del segundo punto

    Returns:
        Distancia en kilómetros
    """
    R = 6371  # Radio de la Tierra en km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula el azimut desde un punto hacia otro

    Args:
        lat1, lon1: Coordenadas del punto de origen
        lat2, lon2: Coordenadas del punto de destino

    Returns:
        Azimut en grados (0-360)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon = math.radians(lon2 - lon1)

    x = math.sin(dlon) * math.cos(lat2_rad)
    y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360


def knots_to_ms(knots: float) -> float:
    """Convierte nudos a metros por segundo"""
    return knots * 0.514444


def ms_to_knots(ms: float) -> float:
    """Convierte metros por segundo a nudos"""
    return ms / 0.514444


def feet_to_meters(feet: float) -> float:
    """Convierte pies a metros"""
    return feet * 0.3048


def meters_to_feet(meters: float) -> float:
    """Convierte metros a pies"""
    return meters / 0.3048


def nm_to_km(nm: float) -> float:
    """Convierte millas náuticas a kilómetros"""
    return nm * 1.852


def km_to_nm(km: float) -> float:
    """Convierte kilómetros a millas náuticas"""
    return km / 1.852
