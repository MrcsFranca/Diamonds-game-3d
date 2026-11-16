#animação de deslocamento dos jogadores
from dataclasses import dataclass
from math import sin, pi

@dataclass
class MovementAnimation:
    player_id: int
    origin: tuple[int, int]
    destination: tuple[int, int]
    start_time_ms: int
    duration_ms: int
    facing_angle: float


class PlayerAnimator:
    DIRECTION_ANGLES = {
        (-1, 0): 180.0,  # norte: -Z
        (1, 0): 0.0,     # sul: +Z
        (0, -1): -90.0,  # oeste: -X
        (0, 1): 90.0,    # leste: +X
    }

    def __init__(self, duration_ms: int = 360) -> None:
        if duration_ms <= 0:
            raise ValueError("A duração da animação deve ser positiva.")
        self.duration_ms = duration_ms
        self.animations: dict[int, MovementAnimation] = {}
        self.facing_angles: dict[int, float] = {}

    #inicia a animação
    def start_move(
        self,
        player_id: int,
        origin: tuple[int, int],
        destination: tuple[int, int],
        start_time_ms: int,
    ) -> None:
        delta = (
            destination[0] - origin[0],
            destination[1] - origin[1],
        )
        angle = self.DIRECTION_ANGLES.get(delta, self.facing_angles.get(player_id, 0.0))
        self.facing_angles[player_id] = angle
        self.animations[player_id] = MovementAnimation(
            player_id=player_id,
            origin=origin,
            destination=destination,
            start_time_ms=start_time_ms,
            duration_ms=self.duration_ms,
            facing_angle=angle,
        )

    def visual_state(
        self,
        player_id: int,
        logical_position: tuple[int, int],
        now_ms: int,
    ) -> tuple[float, float, float, float]:
        animation = self.animations.get(player_id)
        if animation is None:
            return (
                float(logical_position[0]),
                float(logical_position[1]),
                self.facing_angles.get(player_id, 0.0),
                0.0,
            )

        elapsed = max(0, now_ms - animation.start_time_ms)
        progress = min(elapsed / animation.duration_ms, 1.0)

        if progress >= 1.0:
            del self.animations[player_id]
            return (
                float(logical_position[0]),
                float(logical_position[1]),
                animation.facing_angle,
                0.0,
            )

        # Smoothstep: começa e termina suavemente, sem trancos.
        eased = progress * progress * (3.0 - 2.0 * progress)
        row = animation.origin[0] + (
            animation.destination[0] - animation.origin[0]
        ) * eased
        col = animation.origin[1] + (
            animation.destination[1] - animation.origin[1]
        ) * eased
        swing = sin(progress * 4.0 * pi) * 24.0

        return row, col, animation.facing_angle, swing

    #informa se ainda existe movimento
    def is_active(self, now_ms: int) -> bool:
        expired = [
            player_id
            for player_id, animation in self.animations.items()
            if now_ms - animation.start_time_ms >= animation.duration_ms
        ]
        for player_id in expired:
            del self.animations[player_id]
        return bool(self.animations)
