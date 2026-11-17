# faz a renderização da mina e dos personagens com o GLUT
from OpenGL.GL import *
from OpenGL.GLUT import *

from game_logic import BOARD_SIZE, PLAYER_COLORS
from player_model import draw_player_model
from items_model import draw_discovered_items
from textures import get_texture, load_textures


# Medidas do cenário (unidades arbitrárias do OpenGL).
CELL_SPACING = 1.55
TILE_SIZE = 1.42
TILE_HEIGHT = 0.28
TILE_CENTER_Y = -0.045
TILE_TOP_Y = TILE_CENTER_Y + TILE_HEIGHT / 2.0

BASE_HEIGHT = 0.32
BASE_CENTER_Y = -0.34


#largura das casas do tabuleiro
def board_width(board_size: int = BOARD_SIZE) -> float:
    return (board_size - 1) * CELL_SPACING + TILE_SIZE


#converte coordenada da matiz em posição 3d
def tile_position(
    row: int, col: int, board_size: int = BOARD_SIZE
) -> tuple[float, float, float]:
    x = (col - (board_size - 1) / 2.0) * CELL_SPACING
    z = (row - (board_size - 1) / 2.0) * CELL_SPACING
    return x, TILE_CENTER_Y, z

# desenha paralelepípedo usando um cubo GLUT escalonado
def draw_box(
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


#só Carrega as texturas depois que a janela do OpenGL existir. Antes as texturas n estavam sendo carregadas sem essa função
def init_renderer() -> None:
    load_textures()

def draw_background() -> None:
    texture_id = get_texture("background")
    if texture_id is None:
        return

    viewport = glGetIntegerv(GL_VIEWPORT)
    viewport_width = int(viewport[2])
    viewport_height = int(viewport[3])
    if viewport_width <= 0 or viewport_height <= 0:
        return

    previous_matrix_mode = glGetIntegerv(GL_MATRIX_MODE)

    # Guarda os estados que serão temporariamente modificados pelo fundo.
    glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT | GL_CURRENT_BIT | GL_DEPTH_BUFFER_BIT | GL_POLYGON_BIT)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(-1.0, 1.0, -1.0, 1.0, -1.0, 1.0)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST)
    glDepthMask(GL_FALSE)
    glDisable(GL_LIGHTING)
    glDisable(GL_CULL_FACE)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glColor3f(1.0, 1.0, 1.0)

    texture_width = int(glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH))
    texture_height = int(glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_HEIGHT))
    image_aspect = texture_width / texture_height
    viewport_aspect = viewport_width / viewport_height

    u_min = v_min = 0.0
    u_max = v_max = 1.0
    if image_aspect > viewport_aspect:
        visible_width = viewport_aspect / image_aspect
        u_min = (1.0 - visible_width) / 2.0
        u_max = 1.0 - u_min
    else:
        visible_height = image_aspect / viewport_aspect
        v_min = (1.0 - visible_height) / 2.0
        v_max = 1.0 - v_min

    glBegin(GL_QUADS)
    glTexCoord2f(u_min, v_min)
    glVertex2f(-1.0, -1.0)
    glTexCoord2f(u_max, v_min)
    glVertex2f(1.0, -1.0)
    glTexCoord2f(u_max, v_max)
    glVertex2f(1.0, 1.0)
    glTexCoord2f(u_min, v_max)
    glVertex2f(-1.0, 1.0)
    glEnd()

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glPopAttrib()
    glMatrixMode(previous_matrix_mode)

#paralelepípedo com textura nas 6 faces
def draw_textured_box(
    position: tuple[float, float, float],
    size: tuple[float, float, float],
    texture_id: int | None,
    tint: tuple[float, float, float] = (1.0, 1.0, 1.0),
    repeat_scale: float = 1.0,
) -> None:
    if texture_id is None:
        draw_box(position, size, tint)
        return

    sx, sy, sz = (component / 2.0 for component in size)
    # Cada face define normal, quatro vértices e repetição proporcional
    # ao tamanho físico da face. Isso evita esticar a textura nas paredes.
    faces = (
        # A ordem dos vértices segue o sentido anti-horário visto de fora,
        # para funcionar corretamente com GL_CULL_FACE / GL_BACK.
        ((0, 1, 0), [(-sx, sy, sz), (sx, sy, sz), (sx, sy, -sz), (-sx, sy, -sz)], size[0] / 1.5, size[2] / 1.5),
        ((0, -1, 0), [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, -sy, sz), (-sx, -sy, sz)], size[0] / 1.5, size[2] / 1.5),
        ((1, 0, 0), [(sx, -sy, sz), (sx, -sy, -sz), (sx, sy, -sz), (sx, sy, sz)], size[2] / 1.5, size[1] / 1.5),
        ((-1, 0, 0), [(-sx, -sy, -sz), (-sx, -sy, sz), (-sx, sy, sz), (-sx, sy, -sz)], size[2] / 1.5, size[1] / 1.5),
        ((0, 0, 1), [(-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)], size[0] / 1.5, size[1] / 1.5),
        ((0, 0, -1), [(sx, -sy, -sz), (-sx, -sy, -sz), (-sx, sy, -sz), (sx, sy, -sz)], size[0] / 1.5, size[1] / 1.5),
    )

    glPushMatrix()
    glTranslatef(*position)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glColor3f(*tint)
    glBegin(GL_QUADS)
    for normal, vertices, repeat_u, repeat_v in faces:
        glNormal3f(*normal)
        texcoords = (
            (0.0, 0.0),
            (repeat_u * repeat_scale, 0.0),
            (repeat_u * repeat_scale, repeat_v * repeat_scale),
            (0.0, repeat_v * repeat_scale),
        )
        for (u, v), vertex in zip(texcoords, vertices):
            glTexCoord2f(u, v)
            glVertex3f(*vertex)
    glEnd()
    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)
    glPopMatrix()


#textura rochosa em todas as casas da mina
def draw_mine_floor(game) -> None:
    width = board_width(game.board_size) + 0.75
    draw_textured_box(
        (0.0, BASE_CENTER_Y, 0.0),
        (width, BASE_HEIGHT, width),
        get_texture("floor"),
        (0.82, 0.82, 0.82),
        repeat_scale=1.35,
    )


#muito importante para desenhar a casa sem mostrar o conteúdo que está oculto
def draw_tile(tile, board_size: int) -> None:
    x, _, z = tile_position(tile.row, tile.col, board_size)

    if tile.revealed:
        color = (0.90, 0.84, 0.70)
    elif (tile.row + tile.col) % 2 == 0:
        color = (0.82, 0.77, 0.66)
    else:
        color = (0.74, 0.70, 0.60)

    draw_textured_box(
        (x, TILE_CENTER_Y, z),
        (TILE_SIZE, TILE_HEIGHT, TILE_SIZE),
        get_texture("floor"),
        color,
        repeat_scale=0.85,
    )

    # para posicionar o marcador colorido de cada jogador na casa
    corner_offsets = (
        (-0.48, -0.48),
        (0.48, -0.48),
        (-0.48, 0.48),
        (0.48, 0.48),
    )

    for player_id in sorted(tile.visited_by):
        if 0 <= player_id < len(PLAYER_COLORS):
            offset_x, offset_z = corner_offsets[player_id]
            draw_box(
                (x + offset_x, TILE_TOP_Y + 0.035, z + offset_z),
                (0.20, 0.07, 0.20),
                PLAYER_COLORS[player_id],
            )

# desenha casas na ordem da matriz
def draw_tiles(game) -> None:
    for row in game.board:
        for tile in row:
            draw_tile(tile, game.board_size)

# constroi as paredes de acordo com o tamanho da mina. importante para o chão da mina não passar das paredes quando atualizar
def draw_walls(game) -> None:
    width = board_width(game.board_size)
    half = width / 2.0
    thickness = 0.55
    height = 1.65
    center_y = 0.75
    wall_length = width + thickness
    side = half + thickness / 2.0 - 0.03

    rock = (0.30, 0.28, 0.25)
    rock_dark = (0.24, 0.23, 0.21)

    # Parede do fundo.
    draw_textured_box(
        (0.0, center_y, -side),
        (wall_length, height, thickness),
        get_texture("wall"),
        (0.82, 0.78, 0.70),
        repeat_scale=1.0,
    )

    # Paredes laterais.
    for x in (-side, side):
        draw_textured_box(
            (x, center_y, 0.0),
            (thickness, height, wall_length),
            get_texture("wall"),
            (0.90, 0.86, 0.78),
            repeat_scale=1.0,
        )

    # Parede frontal dividida em dois blocos para formar uma entrada.
    entrance_width = 2.2
    segment_length = (width - entrance_width) / 2.0
    front_z = side
    segment_center_x = entrance_width / 2.0 + segment_length / 2.0

    for x in (-segment_center_x, segment_center_x):
        draw_textured_box(
            (x, center_y, front_z),
            (segment_length, height, thickness),
            get_texture("wall"),
            (0.82, 0.78, 0.70),
            repeat_scale=1.0,
        )

    # Blocos maiores nos cantos dão volume às junções das paredes.
    for x in (-side, side):
        for z in (-side, side):
            draw_box(
                (x, center_y + 0.12, z),
                (0.78, height + 0.25, 0.78),
                (0.36, 0.32, 0.27),
            )

# desenha os jogadores em suas casas atuais
def draw_player_models(game, animator=None, now_ms: int = 0) -> None:
    player_offsets = (
        (-0.28, -0.28),
        (0.28, -0.28),
        (-0.28, 0.28),
        (0.28, 0.28),
    )

    for player in game.players:
        if animator is None:
            row, col = player.position
            facing_angle = 0.0
            walk_swing = 0.0
        else:
            row, col, facing_angle, walk_swing = animator.visual_state(
                player.player_id,
                player.position,
                now_ms,
            )

        x, _, z = tile_position(row, col, game.board_size)
        offset_x, offset_z = player_offsets[player.player_id]

        draw_player_model(
            player.color,
            (x + offset_x, TILE_TOP_Y + 0.025, z + offset_z),
            facing_angle,
            walk_swing,
        )

# larterna de madeira
def draw_lantern(position: tuple[float, float, float]) -> None:
    x, y, z = position
    draw_textured_box(
        (x, y - 0.24, z),
        (0.12, 0.48, 0.12),
        get_texture("wood"),
        (0.80, 0.78, 0.72),
    )
    draw_textured_box(
        (x, y + 0.04, z),
        (0.34, 0.08, 0.34),
        get_texture("wood"),
        (0.90, 0.85, 0.72),
    )

    glPushMatrix()
    glTranslatef(x, y - 0.06, z)
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (0.95, 0.48, 0.10, 1.0))
    glColor3f(1.0, 0.72, 0.28)
    glutSolidSphere(0.105, 12, 8)
    glMaterialfv(GL_FRONT_AND_BACK, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))
    glPopMatrix()

#detalhe nas paredes
def draw_cave_decorations(game) -> None:
    width = board_width(game.board_size)
    half = width / 2.0
    side = half + 0.55 / 2.0 - 0.03

    # Lanternas na parede do fundo e nas paredes laterais.
    lantern_x = min(2.9, side * 0.58)
    draw_lantern((-lantern_x, 1.18, -side + 0.34))
    draw_lantern((lantern_x, 1.18, -side + 0.34))
    draw_lantern((-side + 0.34, 1.18, 0.0))
    draw_lantern((side - 0.34, 1.18, 0.0))

    # Rochas decorativas próximas às paredes, fora das casas centrais.
    rocks = (
        (-side + 0.40, -0.02, -side + 0.45, (0.48, 0.34, 0.42)),
        (side - 0.42, -0.02, -side + 0.52, (0.38, 0.30, 0.44)),
        (-side + 0.42, -0.02, side - 0.48, (0.42, 0.31, 0.35)),
        (side - 0.42, -0.02, side - 0.46, (0.50, 0.36, 0.40)),
    )
    for x, y, z, scale in rocks:
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(*scale)
        glColor3f(0.31, 0.29, 0.26)
        glutSolidSphere(1.0, 10, 8)
        glPopMatrix()

#coloca luz
def configure_scene_lighting(game) -> None:
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # a iluminação ambiente fica baixa para manter a sensação de mina escura.
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.035, 0.035, 0.045, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.045, 0.045, 0.055, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.91, 0.76, 1.0))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.30, 0.28, 0.24, 1.0))

    # A luz acompanha o jogador da vez e ilumina sua casa e os tiles próximos.
    player = game.current_player
    row, col = player.position
    x, _, z = tile_position(row, col, game.board_size)

    player_offsets = (
        (-0.28, -0.28),
        (0.28, -0.28),
        (-0.28, 0.28),
        (0.28, 0.28),
    )
    offset_x, offset_z = player_offsets[player.player_id]

    # A posição é definida depois da câmera, portanto o OpenGL a transforma
    # para o espaço de câmera. O foco aponta verticalmente para o tabuleiro.
    glLightfv(GL_LIGHT0, GL_POSITION, (x + offset_x, 3.8, z + offset_z, 1.0))
    glLightf(GL_LIGHT0, GL_SPOT_CUTOFF, 55.0)
    glLightf(GL_LIGHT0, GL_SPOT_EXPONENT, 12.0)
    glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, (0.0, -1.0, 0.0))

    # Atenuação: a iluminação perde intensidade conforme se afasta do jogador.
    glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 1.0)
    glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.10)
    glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.035)

    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.18, 0.18, 0.18, 1.0))
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 20.0)
    glEnable(GL_NORMALIZE)
    glShadeModel(GL_SMOOTH)

#desenha mina tabuleiro e avatares
def draw_scene(game, animator=None, now_ms: int = 0) -> None:
    draw_background()
    configure_scene_lighting(game)
    draw_mine_floor(game)
    draw_tiles(game)
    draw_walls(game)
    draw_cave_decorations(game)
    draw_discovered_items(
        game,
        lambda row, col: tile_position(row, col, game.board_size),
        TILE_TOP_Y,
        now_ms,
    )
    draw_player_models(game, animator, now_ms)
