"""Map audio energy level to a viseme ID for lip-sync."""


def energy_to_viseme(energy: float) -> int:
    """Map energy level to a viseme ID (0-5).

    Args:
        energy: Normalized audio energy value (0.0-1.0).

    Returns:
        Viseme ID: 0=neutral, 1=slight open, 2=open, 3=wide open,
                    4=very wide, 5=maximum.
    """
    if energy < 0.1:
        return 0  # neutral
    elif energy < 0.3:
        return 1  # slight open
    elif energy < 0.5:
        return 2  # open
    elif energy < 0.7:
        return 3  # wide open
    elif energy < 0.85:
        return 4  # very wide
    else:
        return 5  # maximum
