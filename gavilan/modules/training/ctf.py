"""
Motor de CTF
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Flag:
    """Bandera de CTF"""
    flag_id: str
    value: str
    points: int
    captured: bool = False
    captured_by: str = ""


class CTFEngine:
    """Motor de Capture The Flag"""

    def __init__(self):
        self._flags: dict[str, Flag] = {}

    def create_flag(self, flag_id: str, value: str, points: int) -> Flag:
        """Crea una nueva flag"""
        flag = Flag(
            flag_id=flag_id,
            value=value,
            points=points
        )
        self._flags[flag_id] = flag
        return flag

    def capture_flag(self, flag_id: str, team_id: str) -> bool:
        """Captura una flag"""
        if flag_id not in self._flags:
            return False

        flag = self._flags[flag_id]
        if flag.captured:
            return False

        flag.captured = True
        flag.captured_by = team_id
        return True

    def validate_flag(self, flag_value: str) -> Optional[Flag]:
        """Valida un valor de flag"""
        for flag in self._flags.values():
            if flag.value == flag_value and not flag.captured:
                return flag
        return None
