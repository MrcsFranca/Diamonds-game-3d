# modelo do personagem. Fiz separado pq basicamente é um monte de formas juntas
from OpenGL.GL import *
from OpenGL.GLUT import *

def _shade(color: tuple[float, float, float], factor: float) -> tuple[float, float, float]:
    return tuple(max(0.0, min(1.0, component * factor)) for component in color)

def _cube(
    position: tuple[float, float, float],
    size: tuple[float, float, float],
    color: tuple[float, float, float],
) -> None:
    glPushMatrix()
    glTranslatef(*position)
    glScalef(*size)
    glColor3f(*color)
    glutSolidCube(1.0)
    glPopMatrix()

def _sphere(
    position: tuple[float, float, float],
    scale: tuple[float, float, float],
    color: tuple[float, float, float],
) -> None:
    glPushMatrix()
    glTranslatef(*position)
    glScalef(*scale)
    glColor3f(*color)
    glutSolidSphere(1.0, 14, 10)
    glPopMatrix()

def _limb(
    shoulder: tuple[float, float, float],
    length: float,
    width: float,
    depth: float,
    angle: float,
    color: tuple[float, float, float],
    axis: tuple[float, float, float],
) -> None:
    glPushMatrix()
    glTranslatef(*shoulder)
    glRotatef(angle, *axis)
    _cube(
        (0.0, -length / 2.0, 0.0),
        (width, length, depth),
        color,
    )
    glPopMatrix()


def draw_player_model(
    color: tuple[float, float, float],
    position: tuple[float, float, float],
    facing_angle: float = 0.0,
    walk_swing: float = 0.0,
) -> None:
    dark = _shade(color, 0.58)
    light = _shade(color, 1.18)
    skin = (0.78, 0.57, 0.40)
    helmet = (0.95, 0.68, 0.12)
    boot = (0.12, 0.11, 0.10)

    glPushMatrix()
    glTranslatef(*position)
    glRotatef(facing_angle, 0.0, 1.0, 0.0)

    #mochila atrás do tronco
    _cube((0.0, 0.57, -0.20), (0.27, 0.34, 0.18), dark)
    _cube((0.0, 0.67, -0.30), (0.18, 0.10, 0.05), light)

    #pernas e botas com movimento oposto para parecer que está caminhando
    _limb((-0.11, 0.37, 0.0), 0.31, 0.13, 0.14, walk_swing, dark, (1, 0, 0))
    _limb((0.11, 0.37, 0.0), 0.31, 0.13, 0.14, -walk_swing, dark, (1, 0, 0))
    _cube((-0.11, 0.055, 0.055), (0.17, 0.11, 0.27), boot)
    _cube((0.11, 0.055, 0.055), (0.17, 0.11, 0.27), boot)

    # Tronco e gola.
    _cube((0.0, 0.60, 0.0), (0.38, 0.43, 0.25), color)
    _cube((0.0, 0.81, 0.0), (0.17, 0.10, 0.17), dark)

    # Braços articulados.
    _limb((-0.235, 0.76, 0.0), 0.34, 0.13, 0.14, -walk_swing, light, (1, 0, 0))
    _limb((0.235, 0.76, 0.0), 0.34, 0.13, 0.14, walk_swing, light, (1, 0, 0))
    _sphere((-0.235, 0.57, 0.0), (0.075, 0.075, 0.075), skin)
    _sphere((0.235, 0.57, 0.0), (0.075, 0.075, 0.075), skin)

    # Cabeça, rosto e capacete.
    _sphere((0.0, 0.96, 0.015), (0.17, 0.19, 0.16), skin)
    _sphere((-0.065, 0.98, 0.153), (0.025, 0.025, 0.018), (0.08, 0.07, 0.06))
    _sphere((0.065, 0.98, 0.153), (0.025, 0.025, 0.018), (0.08, 0.07, 0.06))
    _sphere((0.0, 1.115, 0.0), (0.205, 0.105, 0.19), helmet)
    _cube((0.0, 1.075, 0.035), (0.47, 0.045, 0.35), helmet)

    # Picareta presa à mochila, cabo e cabeça feitos com dois cubos.
    glPushMatrix()
    glTranslatef(0.30, 0.61, -0.12)
    glRotatef(-18.0, 0.0, 0.0, 1.0)
    _cube((0.0, 0.0, 0.0), (0.055, 0.62, 0.055), (0.40, 0.24, 0.12))
    _cube((0.0, 0.30, 0.0), (0.38, 0.07, 0.08), (0.55, 0.57, 0.60))
    glPopMatrix()

    glPopMatrix()
