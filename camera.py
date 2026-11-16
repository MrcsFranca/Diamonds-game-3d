from OpenGL.GL import glTranslatef, glRotatef
from OpenGL.GLUT import GLUT_LEFT_BUTTON, GLUT_RIGHT_BUTTON, GLUT_DOWN


class OrbitCamera:
    # camera controlada no mouse, usei basicamente a mesma coisa da aula
    def __init__(self) -> None:
        self.active_button = None
        self.last_x = 0
        self.last_y = 0
        self.reset()

    def reset(self, board_size: int = 6) -> None:
        #restaura a cam e ajusta a dist ao tam da mina
        self.board_size = max(6, int(board_size))
        self.min_distance = max(8.0, self.board_size * 1.25)
        self.max_distance = max(35.0, self.board_size * 5.0)
        self.distance = min(max(self.board_size * 3.0, self.min_distance), self.max_distance)
        self.azimuth = 35.0
        self.incidence = -55.0
        self.twist = 0.0

    def fit_board(self, board_size: int) -> None:
        # serve para afastar a cam quando uma nova mina surge
        self.reset(board_size)

    def apply(self) -> None:
        #vista orbital
        glTranslatef(0.0, 0.0, -self.distance)
        glRotatef(-self.twist, 0.0, 0.0, 1.0)
        glRotatef(-self.incidence, 1.0, 0.0, 0.0)
        glRotatef(-self.azimuth, 0.0, 1.0, 0.0)

    #para alterar a dist da cam
    def zoom(self, amount: float) -> None:
        self.distance = min(
            max(self.distance + amount, self.min_distance),
            self.max_distance,
        )

    #para o scroll do mouse ou botão pressionado
    def mouse_button(self, button: int, state: int, x: int, y: int) -> None:
        if state == GLUT_DOWN and button == 3:  # roda para cima
            self.zoom(-1.0)
            return
        if state == GLUT_DOWN and button == 4:  # roda para baixo
            self.zoom(1.0)
            return

        if state == GLUT_DOWN and button in (GLUT_LEFT_BUTTON, GLUT_RIGHT_BUTTON):
            self.active_button = button
            self.last_x = x
            self.last_y = y
        else:
            self.active_button = None

    #rotaciona com esq e aproxima com direito
    def mouse_motion(self, x: int, y: int) -> None:
        dx = x - self.last_x
        dy = y - self.last_y
        self.last_x = x
        self.last_y = y

        if self.active_button == GLUT_LEFT_BUTTON:
            self.azimuth = (self.azimuth - dx * 0.5) % 360.0
            self.incidence = min(max(self.incidence - dy * 0.4, -85.0), -15.0)
        elif self.active_button == GLUT_RIGHT_BUTTON:
            self.zoom(dy * 0.06)
