# aqui é feito os modelos 3d dos objetos do jogo -> com ajuda de IA desenhei os objetos com o GLUT
from math import sin, pi

from OpenGL.GL import *
from OpenGL.GLUT import *

from game_logic import ItemType
from item_visibility import iter_visible_items


# desenha um cubo
def _draw_box(position, size, color) -> None:
    glPushMatrix()
    glTranslatef(*position)
    glScalef(*size)
    glColor3f(*color)
    glutSolidCube(1.0)
    glPopMatrix()


# desenha diamante
def _draw_diamond(tile, position, now_ms: int) -> None:
    value = tile.diamond_value or 1
    # Os valores de 1 a 10 resultam em tamanhos discretamente diferentes.
    scale = 0.55 + value * 0.035
    angle = (now_ms * 0.075) % 360.0
    bob = 0.035 * sin((now_ms / 1000.0) * 2.5)

    glPushMatrix()
    glTranslatef(position[0], position[1] + 0.36 + bob, position[2])
    glRotatef(angle, 0.0, 1.0, 0.0)
    glRotatef(18.0, 1.0, 0.0, 0.0)
    glScalef(scale, scale, scale)
    glColor3f(0.12, 0.78, 0.96)
    glutSolidOctahedron()
    glPopMatrix()


# item de pista: cristal violeta sobre uma base
def _draw_clue(position, now_ms: int) -> None:
    pulse = 1.0 + 0.06 * sin((now_ms / 1000.0) * 3.0)
    _draw_box(
        (position[0], position[1] + 0.055, position[2]),
        (0.36, 0.11, 0.36),
        (0.34, 0.27, 0.19),
    )

    glPushMatrix()
    glTranslatef(position[0], position[1] + 0.30, position[2])
    glRotatef((now_ms * 0.045) % 360.0, 0.0, 1.0, 0.0)
    glScalef(0.30 * pulse, 0.38 * pulse, 0.30 * pulse)
    glColor3f(0.66, 0.35, 0.95)
    glutSolidTetrahedron()
    glPopMatrix()


# o tunel sem saída é só um buraco escuro cercado de pedras
def _draw_dead_end(position, now_ms: int) -> None:
    # A esfera achatada forma a abertura escura no piso.
    glPushMatrix()
    glTranslatef(position[0], position[1] + 0.025, position[2])
    glScalef(0.48, 0.045, 0.48)
    glColor3f(0.035, 0.025, 0.02)
    glutSolidSphere(1.0, 16, 10)
    glPopMatrix()

    rock_color = (0.36, 0.30, 0.24)
    rock_positions = (
        (-0.43, 0.08, 0.0, 18.0),
        (0.43, 0.08, 0.0, -14.0),
        (0.0, 0.08, -0.43, 12.0),
        (0.0, 0.08, 0.43, -20.0),
    )

    for dx, dy, dz, angle in rock_positions:
        glPushMatrix()
        glTranslatef(position[0] + dx, position[1] + dy, position[2] + dz)
        glRotatef(angle, 0.0, 1.0, 0.0)
        glScalef(0.25, 0.18, 0.22)
        glColor3f(*rock_color)
        glutSolidCube(1.0)
        glPopMatrix()

    glPushMatrix()
    glTranslatef(position[0], position[1] + 0.12, position[2])
    glScalef(0.10, 0.10, 0.10)
    glColor3f(0.75, 0.16, 0.10)
    glutSolidOctahedron()
    glPopMatrix()


# o Esconderijo é uma pequena entrada de pedra
def _draw_hideout(position, now_ms: int) -> None:
    stone = (0.40, 0.38, 0.33)
    dark = (0.025, 0.035, 0.05)

    _draw_box(
        (position[0], position[1] + 0.27, position[2]),
        (0.48, 0.48, 0.075),
        dark,
    )

    # Duas colunas e uma viga superior formam o portal.
    _draw_box(
        (position[0] - 0.31, position[1] + 0.25, position[2]),
        (0.16, 0.55, 0.24),
        stone,
    )
    _draw_box(
        (position[0] + 0.31, position[1] + 0.25, position[2]),
        (0.16, 0.55, 0.24),
        stone,
    )
    _draw_box(
        (position[0], position[1] + 0.56, position[2]),
        (0.78, 0.16, 0.24),
        (0.31, 0.29, 0.25),
    )

    # Cristal azul marca a entrada secreta.
    pulse = 1.0 + 0.08 * sin((now_ms / 1000.0) * 2.8)
    glPushMatrix()
    glTranslatef(position[0], position[1] + 0.69, position[2] + 0.02)
    glRotatef((now_ms * 0.06) % 360.0, 0.0, 1.0, 0.0)
    glScalef(0.18 * pulse, 0.18 * pulse, 0.18 * pulse)
    glColor3f(0.15, 0.72, 0.92)
    glutSolidOctahedron()
    glPopMatrix()



# passagem para próxima mina
def _draw_map_change(position, now_ms: int) -> None:
    dark = (0.025, 0.035, 0.055)
    stone = (0.38, 0.35, 0.30)
    _draw_box(
        (position[0], position[1] + 0.23, position[2]),
        (0.62, 0.48, 0.10),
        dark,
    )
    _draw_box(
        (position[0] - 0.37, position[1] + 0.28, position[2]),
        (0.13, 0.58, 0.25),
        stone,
    )
    _draw_box(
        (position[0] + 0.37, position[1] + 0.28, position[2]),
        (0.13, 0.58, 0.25),
        stone,
    )
    _draw_box(
        (position[0], position[1] + 0.59, position[2]),
        (0.86, 0.14, 0.25),
        (0.29, 0.27, 0.24),
    )
    pulse = 1.0 + 0.08 * sin((now_ms / 1000.0) * 3.2)
    glPushMatrix()
    glTranslatef(position[0], position[1] + 0.37, position[2] + 0.08)
    glRotatef((now_ms * 0.07) % 360.0, 0.0, 1.0, 0.0)
    glScalef(0.22 * pulse, 0.32 * pulse, 0.22 * pulse)
    glColor3f(0.95, 0.48, 0.12)
    glutSolidOctahedron()
    glPopMatrix()


# função para desenhar só os itens descobertos
def draw_discovered_items(game, tile_position_fn, tile_top_y: float, now_ms: int = 0) -> None:
    for tile in iter_visible_items(game):
        x, _, z = tile_position_fn(tile.row, tile.col)
        position = (x, tile_top_y, z)

        if tile.item == ItemType.DIAMOND:
            _draw_diamond(tile, position, now_ms)
        elif tile.item == ItemType.CLUE:
            _draw_clue(position, now_ms)
        elif tile.item == ItemType.DEAD_END:
            _draw_dead_end(position, now_ms)
        elif tile.item == ItemType.HIDEOUT:
            _draw_hideout(position, now_ms)
        elif tile.item == ItemType.MAP_CHANGE:
            _draw_map_change(position, now_ms)
