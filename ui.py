# menu e HUD do jogo. A gamUI serve para controlar a navegação entre as telas. A draw_ui desenha o 2d por cima do 3d
from __future__ import annotations

from dataclasses import dataclass
import unicodedata
from typing import Optional

from game_logic import WIN_SCORE


@dataclass(frozen=True)
class UIButton:
    action: str
    label: str
    x: float
    y: float
    width: float
    height: float

    def contains(self, x: float, y: float) -> bool:
        return (
            self.x <= x <= self.x + self.width
            and self.y <= y <= self.y + self.height
        )


class GameUI:
    #estados do jogo
    VALID_SCREENS = {"menu", "instructions", "config", "playing", "paused", "finished", "choose_tunnel_target", "choose_attack_target"}

    def __init__(self) -> None:
        self.screen = "menu"
        self.player_count = 2
        self.names = ["Jogador 1", "Jogador 2", "Jogador 3", "Jogador 4"]
        self.active_name = 0
        self.edited_names: set[int] = set()
        self.message = "Explore a mina e encontre os diamantes!"
        self.message_until_ms = 0
        self.target_options: list[dict] = []
        self.target_kind: Optional[str] = None

    def set_message(self, message: str, now_ms: int, duration_ms: int = 4500) -> None:
        self.message = message
        self.message_until_ms = now_ms + duration_ms

    # nomes dos jogadores
    def selected_names(self) -> list[str]:
        selected = []
        for index in range(self.player_count):
            name = self.names[index].strip()
            selected.append(name or f"Jogador {index + 1}")
        return selected

    def _buttons(self, width: int, height: int) -> list[UIButton]:
        cx = width / 2.0
        cy = height / 2.0
        buttons: list[UIButton] = []

        def add(action: str, label: str, x: float, y: float, w: float, h: float) -> None:
            buttons.append(UIButton(action, label, x, y, w, h))

        if self.screen == "menu":
            bw, bh = 270.0, 48.0
            add("menu_start", "Iniciar partida", cx - bw / 2, cy + 20, bw, bh)
            add("menu_instructions", "Como jogar", cx - bw / 2, cy - 43, bw, bh)
            add("menu_exit", "Sair", cx - bw / 2, cy - 106, bw, bh)

        elif self.screen == "instructions":
            add("instructions_back", "Voltar", cx - 110, cy - 260, 220, 46)

        elif self.screen == "config":
            for count in (2, 3, 4):
                x = cx - 145 + (count - 2) * 105
                add(f"count_{count}", str(count), x, cy + 158, 82, 42)

            for index in range(self.player_count):
                y = cy + 91 - index * 45
                add(f"name_{index}", self.names[index], cx - 180, y, 360, 36)

            add("config_start", "Comecar", cx - 160, cy - 166, 150, 46)
            add("config_back", "Voltar", cx + 10, cy - 166, 150, 46)

        elif self.screen == "playing":
            add("pause", "PAUSAR", width - 142, height - 58, 124, 40)
            add("mine", "MINERAR (M)", 18, 88, 132, 36)
            add("attack", "ATACAR (F)", 160, 88, 132, 36)

        elif self.screen in {"choose_tunnel_target", "choose_attack_target"}:
            panel_width = min(360.0, width - 36.0)
            button_width = panel_width - 56.0
            start_y = cy + 42.0
            for index, option in enumerate(self.target_options):
                y = start_y - index * 48.0
                player_id = option["player_id"]
                label = f"{player_id + 1} - {option['name']}"
                add(f"target_{player_id}", label, cx - button_width / 2.0, y, button_width, 38)
            cancel_y = start_y - len(self.target_options) * 48.0 - 6.0
            add("target_cancel", "Cancelar / nao usar", cx - button_width / 2.0, cancel_y, button_width, 38)

        elif self.screen == "paused":
            bw, bh = 260.0, 46.0
            add("resume", "Continuar", cx - bw / 2, cy + 45, bw, bh)
            add("paused_restart", "Reiniciar partida", cx - bw / 2, cy - 15, bw, bh)
            add("paused_menu", "Menu principal", cx - bw / 2, cy - 75, bw, bh)

        elif self.screen == "finished":
            bw, bh = 260.0, 46.0
            add("finished_restart", "Jogar novamente", cx - bw / 2, cy - 155, bw, bh)
            add("finished_menu", "Menu principal", cx - bw / 2, cy - 215, bw, bh)

        return buttons

    # tratar clique do mouse
    def handle_click(self, mouse_x: int, mouse_y: int, width: int, height: int) -> Optional[str]:
        x = float(mouse_x)
        y = float(height - mouse_y)

        for button in self._buttons(width, height):
            if not button.contains(x, y):
                continue

            action = button.action
            if action == "menu_start":
                self.screen = "config"
                self.active_name = 0
                return ""
            if action == "menu_instructions":
                self.screen = "instructions"
                return ""
            if action == "menu_exit":
                return "exit"
            if action == "instructions_back":
                self.screen = "menu"
                return ""
            if action.startswith("count_"):
                self.player_count = int(action.split("_")[1])
                self.active_name = min(self.active_name, self.player_count - 1)
                return ""
            if action.startswith("name_"):
                self.active_name = int(action.split("_")[1])
                return ""
            if action == "config_start":
                self.screen = "playing"
                return "start_game"
            if action == "config_back":
                self.screen = "menu"
                return ""
            if action == "pause":
                self.screen = "paused"
                return ""
            if action == "mine":
                return "mine"
            if action == "attack":
                return "attack"
            if action.startswith("target_") and action != "target_cancel":
                player_id = int(action.split("_")[1])
                self.screen = "playing"
                return f"target:{player_id}"
            if action == "target_cancel":
                self.cancel_target_selection()
                return "cancel_target_selection"
            if action == "resume":
                self.screen = "playing"
                return ""
            if action == "paused_restart" or action == "finished_restart":
                self.screen = "playing"
                return "restart_game"
            if action == "paused_menu" or action == "finished_menu":
                self.screen = "menu"
                return "main_menu"

        return None

    # abrir menu de escolha do alvo
    def begin_target_selection(self, kind: str, players) -> None:
        if kind not in {"tunnel", "attack"}:
            raise ValueError("Tipo de escolha de alvo inválido.")
        self.target_kind = kind
        self.target_options = [
            {"player_id": player.player_id, "name": player.name, "color": player.color}
            for player in players
        ]
        self.screen = "choose_tunnel_target" if kind == "tunnel" else "choose_attack_target"

    # sem essa função, quando fechava a tela de escolha a rodada era usada
    def cancel_target_selection(self) -> None:
        self.target_kind = None
        self.target_options = []
        self.screen = "playing"

    # atalhos de teclado com base da tela atual
    def handle_key(self, key: bytes) -> Optional[str]:
        if self.screen in {"choose_tunnel_target", "choose_attack_target"}:
            if key in (b"\x1b", b"n", b"N"):
                self.cancel_target_selection()
                return "cancel_target_selection"
            if len(key) == 1 and key in (b"1", b"2", b"3", b"4"):
                player_id = int(key.decode("ascii")) - 1
                if any(option["player_id"] == player_id for option in self.target_options):
                    self.screen = "playing"
                    return f"target:{player_id}"
            return None

        if self.screen == "menu":
            if key in (b"\x1b", b"q", b"Q"):
                return "exit"
            if key in (b"\r", b"\n", b" "):
                self.screen = "config"
                return None
            if key in (b"i", b"I"):
                self.screen = "instructions"
                return None
            return None

        if self.screen == "instructions":
            if key in (b"\x1b", b"q", b"Q", b"\r", b"\n"):
                self.screen = "menu"
            return None

        if self.screen == "config":
            if key == b"\x1b":
                self.screen = "menu"
                return None
            if key == b"\t":
                self.active_name = (self.active_name + 1) % self.player_count
                return None
            if key in (b"\r", b"\n"):
                if self.active_name < self.player_count - 1:
                    self.active_name += 1
                    return None
                self.screen = "playing"
                return "start_game"
            if key in (b"\x08", b"\x7f"):
                index = self.active_name
                if index not in self.edited_names:
                    self.names[index] = ""
                    self.edited_names.add(index)
                else:
                    self.names[index] = self.names[index][:-1]
                return None

            if len(key) == 1:
                char = key.decode("latin-1")
                if char.isprintable() and (char.isalnum() or char in " -_"):
                    index = self.active_name
                    if index not in self.edited_names:
                        self.names[index] = ""
                        self.edited_names.add(index)
                    if len(self.names[index]) < 16:
                        self.names[index] += char
            return None

        if self.screen == "playing":
            if key in (b"\x1b", b"p", b"P"):
                self.screen = "paused"
            return None

        if self.screen == "paused":
            if key in (b"\x1b", b"p", b"P", b" "):
                self.screen = "playing"
                return None
            if key in (b"r", b"R"):
                self.screen = "playing"
                return "restart_game"
            if key in (b"m", b"M"):
                self.screen = "menu"
                return "main_menu"
            return None

        if self.screen == "finished":
            if key in (b"\r", b"\n", b"r", b"R"):
                self.screen = "playing"
                return "restart_game"
            if key in (b"m", b"M", b"\x1b"):
                self.screen = "menu"
                return "main_menu"

        return None


# --- Funcoes de desenho 2D. Os imports OpenGL sao locais para manter a classe
# de estado testavel mesmo em ambientes sem contexto grafico. ---
# IA me ajudou com a parte dos testes
def _ascii(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text))
    return normalized.encode("ascii", "ignore").decode("ascii")


def _text_width(glut, text: str, font) -> int:
    return sum(glut.glutBitmapWidth(font, ord(char)) for char in _ascii(text))


def _draw_text(gl, glut, text: str, x: float, y: float, font, color=(1.0, 1.0, 1.0), centered=False) -> None:
    clean = _ascii(text)
    if centered:
        x -= _text_width(glut, clean, font) / 2.0
    gl.glColor4f(color[0], color[1], color[2], 1.0)
    gl.glRasterPos2f(x, y)
    for char in clean:
        glut.glutBitmapCharacter(font, ord(char))

def _rect(gl, x: float, y: float, width: float, height: float, color) -> None:
    gl.glColor4f(*color)
    gl.glBegin(gl.GL_QUADS)
    gl.glVertex2f(x, y)
    gl.glVertex2f(x + width, y)
    gl.glVertex2f(x + width, y + height)
    gl.glVertex2f(x, y + height)
    gl.glEnd()

def _outline(gl, x: float, y: float, width: float, height: float, color, line_width=1.5) -> None:
    gl.glLineWidth(line_width)
    gl.glColor4f(*color)
    gl.glBegin(gl.GL_LINE_LOOP)
    gl.glVertex2f(x, y)
    gl.glVertex2f(x + width, y)
    gl.glVertex2f(x + width, y + height)
    gl.glVertex2f(x, y + height)
    gl.glEnd()

def _draw_button(gl, glut, button: UIButton, font, selected=False) -> None:
    fill = (0.30, 0.22, 0.13, 0.96) if not selected else (0.48, 0.33, 0.14, 0.98)
    border = (0.82, 0.65, 0.34, 1.0) if selected else (0.60, 0.49, 0.32, 1.0)
    _rect(gl, button.x, button.y, button.width, button.height, fill)
    _outline(gl, button.x, button.y, button.width, button.height, border, 2.0)
    _draw_text(
        gl, glut, button.label,
        button.x + button.width / 2.0,
        button.y + button.height / 2.0 - 5.0,
        font,
        (0.98, 0.94, 0.84),
        centered=True,
    )

def _begin_overlay(gl, width: int, height: int) -> None:
    gl.glPushAttrib(gl.GL_ALL_ATTRIB_BITS)
    gl.glDisable(gl.GL_DEPTH_TEST)
    gl.glDisable(gl.GL_LIGHTING)
    gl.glDisable(gl.GL_TEXTURE_2D)
    gl.glDisable(gl.GL_CULL_FACE)
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glOrtho(0, max(width, 1), 0, max(height, 1), -1, 1)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glLoadIdentity()


def _end_overlay(gl) -> None:
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopAttrib()


def _panel(gl, width: float, height: float, center_x: float, center_y: float) -> None:
    x = center_x - width / 2.0
    y = center_y - height / 2.0
    _rect(gl, x, y, width, height, (0.035, 0.035, 0.04, 0.91))
    _outline(gl, x, y, width, height, (0.63, 0.49, 0.28, 0.95), 2.0)


def _draw_menu(gl, glut, ui: GameUI, width: int, height: int) -> None:
    cx, cy = width / 2.0, height / 2.0
    _rect(gl, 0, 0, width, height, (0.015, 0.018, 0.025, 0.67))
    _panel(gl, min(560, width - 40), 410, cx, cy)
    _draw_text(gl, glut, "DIAMONDS GAME", cx, cy + 125, glut.GLUT_BITMAP_TIMES_ROMAN_24, (0.95, 0.78, 0.38), True)
    _draw_text(gl, glut, "PROCURANDO O TESOURO", cx, cy + 91, glut.GLUT_BITMAP_HELVETICA_18, (0.86, 0.83, 0.76), True)
    for button in ui._buttons(width, height):
        _draw_button(gl, glut, button, glut.GLUT_BITMAP_HELVETICA_18)
    _draw_text(gl, glut, "Computacao Grafica - UNICENTRO", cx, cy - 165, glut.GLUT_BITMAP_HELVETICA_12, (0.68, 0.66, 0.61), True)


def _draw_instructions(gl, glut, ui: GameUI, width: int, height: int) -> None:
    cx, cy = width / 2.0, height / 2.0
    _rect(gl, 0, 0, width, height, (0.015, 0.018, 0.025, 0.72))
    _panel(gl, min(690, width - 40), 610, cx, cy)
    _draw_text(gl, glut, "COMO JOGAR", cx, cy + 255, glut.GLUT_BITMAP_TIMES_ROMAN_24, (0.95, 0.78, 0.38), True)
    lines = [
        "Explore a mina e acumule quilates para vencer.",
        "W / A / S / D: move o explorador uma casa por vez.",
        "M: minera diamantes ou recebe uma dica ao minerar pista.",
        "F: ataca um jogador que esteja na mesma casa.",
        "Diamante: recebe de 1 a 10 quilates e guarda no inventario.",
        "Pista: indica direcao e distancia de um diamante nao coletado.",
        "Tunel sem saida: perde 10 quilates automaticamente na chegada.",
        "Tunel secreto: pode trocar de posicao com outro jogador.",
        "Cada mina possui apenas uma passagem para o mapa seguinte.",
        "A cada mina, o tabuleiro cresce uma linha e uma coluna.",
        "A quantidade de acoes cresce com o tabuleiro (multiplo de 12).",
        "A pontuacao e o inventario sao preservados entre as minas.",
        "Atacar rouba um diamante do alvo, se ele tiver algum.",
        "O jogador atingido e empurrado para uma casa adjacente aleatoria.",
        "A chegada do empurrao revela a casa e ativa armadilhas automaticas.",
        f"Vence: o primeiro jogador que alcancar {WIN_SCORE} quilates.",
        "N ou ESC cancela a selecao de alvo sem consumir turno.",
    ]
    for index, line in enumerate(lines):
        _draw_text(gl, glut, line, cx - 300, cy + 200 - index * 27, glut.GLUT_BITMAP_HELVETICA_18, (0.89, 0.87, 0.81))
    for button in ui._buttons(width, height):
        _draw_button(gl, glut, button, glut.GLUT_BITMAP_HELVETICA_18)


def _draw_config(gl, glut, ui: GameUI, width: int, height: int) -> None:
    cx, cy = width / 2.0, height / 2.0
    _rect(gl, 0, 0, width, height, (0.015, 0.018, 0.025, 0.72))
    _panel(gl, min(620, width - 40), 560, cx, cy)
    _draw_text(gl, glut, "CONFIGURAR PARTIDA", cx, cy + 235, glut.GLUT_BITMAP_TIMES_ROMAN_24, (0.95, 0.78, 0.38), True)
    _draw_text(gl, glut, "Quantidade de jogadores", cx, cy + 195, glut.GLUT_BITMAP_HELVETICA_18, (0.89, 0.87, 0.81), True)

    for button in ui._buttons(width, height):
        if button.action.startswith("name_"):
            continue  # Os campos de texto sao desenhados abaixo, com foco visual.
        selected = button.action == f"count_{ui.player_count}"
        _draw_button(gl, glut, button, glut.GLUT_BITMAP_HELVETICA_18, selected)

    for index in range(ui.player_count):
        y = cy + 91 - index * 45
        _draw_text(gl, glut, f"Jogador {index + 1}", cx - 180, y + 44, glut.GLUT_BITMAP_HELVETICA_12, (0.79, 0.76, 0.68))
        _rect(gl, cx - 180, y, 360, 36, (0.10, 0.105, 0.11, 0.98))
        border = (0.92, 0.70, 0.30, 1.0) if index == ui.active_name else (0.42, 0.40, 0.36, 1.0)
        _outline(gl, cx - 180, y, 360, 36, border, 2.0 if index == ui.active_name else 1.0)
        name = ui.names[index] or "Digite o nome..."
        _draw_text(gl, glut, name, cx - 167, y + 11, glut.GLUT_BITMAP_HELVETICA_18, (0.98, 0.95, 0.87) if ui.names[index] else (0.55, 0.53, 0.49))

    _draw_text(gl, glut, "Clique em um campo ou use TAB/ENTER para trocar o nome.", cx, cy - 119, glut.GLUT_BITMAP_HELVETICA_12, (0.72, 0.69, 0.62), True)


def _draw_hud(gl, glut, ui: GameUI, game, width: int, height: int, now_ms: int) -> None:
    side_width = min(248.0, width * 0.30)
    side_x = width - side_width - 14.0
    _rect(gl, 12, height - 57, width - 24, 44, (0.025, 0.028, 0.035, 0.82))
    _draw_text(gl, glut, "DIAMONDS GAME", 27, height - 41, glut.GLUT_BITMAP_HELVETICA_18, (0.95, 0.78, 0.38))
    _draw_text(gl, glut, f"Mina {game.map_number} ({game.board_size}x{game.board_size})", 220, height - 40, glut.GLUT_BITMAP_HELVETICA_18, (0.98, 0.78, 0.38))
    _draw_text(gl, glut, f"Acoes: {game.moves_played}/{game.total_moves} | Meta: {WIN_SCORE}q", 405, height - 40, glut.GLUT_BITMAP_HELVETICA_18, (0.92, 0.90, 0.84))

    panel_y = 85
    panel_h = max(270, height - 165)
    _rect(gl, side_x, panel_y, side_width, panel_h, (0.025, 0.028, 0.035, 0.88))
    _outline(gl, side_x, panel_y, side_width, panel_h, (0.48, 0.39, 0.27, 0.9), 1.2)
    _draw_text(gl, glut, "RANKING", side_x + 16, height - 112, glut.GLUT_BITMAP_HELVETICA_18, (0.95, 0.78, 0.38))

    y = height - 151
    for rank, player in enumerate(game.ranking, start=1):
        gl.glColor4f(player.color[0], player.color[1], player.color[2], 1.0)
        gl.glPointSize(9.0)
        gl.glBegin(gl.GL_POINTS)
        gl.glVertex2f(side_x + 21, y + 5)
        gl.glEnd()
        name = player.name[:15]
        _draw_text(gl, glut, f"{rank}. {name}", side_x + 34, y, glut.GLUT_BITMAP_HELVETICA_12, (0.92, 0.90, 0.84))
        _draw_text(gl, glut, f"{player.score}q ({len(player.diamonds)}D)", side_x + side_width - 91, y, glut.GLUT_BITMAP_HELVETICA_12, (0.98, 0.82, 0.47))
        y -= 35

    if not game.finished:
        active = game.current_player
        _rect(gl, side_x + 10, panel_y + 18, side_width - 20, 73, (0.13, 0.11, 0.08, 0.95))
        _draw_text(gl, glut, "VEZ DE:", side_x + 20, panel_y + 67, glut.GLUT_BITMAP_HELVETICA_12, (0.76, 0.72, 0.63))
        _draw_text(gl, glut, active.name[:18], side_x + 20, panel_y + 42, glut.GLUT_BITMAP_HELVETICA_18, active.color)
        _draw_text(gl, glut, f"Acoes restantes: {game.remaining_moves}", side_x + 16, panel_y + 8, glut.GLUT_BITMAP_HELVETICA_12, (0.82, 0.80, 0.73))

    if game.latest_hint:
        _draw_text(gl, glut, "ULTIMA PISTA", side_x + 14, panel_y + 174, glut.GLUT_BITMAP_HELVETICA_12, (0.75, 0.63, 0.95))
        _draw_text(gl, glut, game.latest_hint[:34], side_x + 14, panel_y + 154, glut.GLUT_BITMAP_HELVETICA_12, (0.90, 0.85, 1.0))

    message_y = 20
    message_width = max(300.0, side_x - 35)
    _rect(gl, 14, message_y, message_width, 58, (0.025, 0.028, 0.035, 0.86))
    _outline(gl, 14, message_y, message_width, 58, (0.42, 0.35, 0.25, 0.85), 1.0)
    if ui.message and now_ms <= ui.message_until_ms:
        _draw_text(gl, glut, ui.message[:75], 27, message_y + 33, glut.GLUT_BITMAP_HELVETICA_12, (0.96, 0.91, 0.79))
    _draw_text(gl, glut, "WASD: mover | M: minerar | F: atacar | P: pausa", 27, message_y + 12, glut.GLUT_BITMAP_HELVETICA_12, (0.68, 0.67, 0.62))

    active_player = None if game.finished else game.current_player
    if active_player is not None:
        current_tile = game.tile_at(active_player.position)
        if current_tile.item.value != "Vazio" and current_tile.revealed and not current_tile.activated:
            hint = "M: minerar/usar " + current_tile.item.value
            _draw_text(gl, glut, hint[:38], side_x + 14, panel_y + 112, glut.GLUT_BITMAP_HELVETICA_12, (0.94, 0.78, 0.39))
        same_tile = game.attack_targets()
        if same_tile:
            _draw_text(gl, glut, "F: atacar jogador nesta casa", side_x + 14, panel_y + 136, glut.GLUT_BITMAP_HELVETICA_12, (0.95, 0.46, 0.36))

    for button in ui._buttons(width, height):
        _draw_button(gl, glut, button, glut.GLUT_BITMAP_HELVETICA_12)


def _draw_paused(gl, glut, ui: GameUI, width: int, height: int) -> None:
    cx, cy = width / 2.0, height / 2.0
    _rect(gl, 0, 0, width, height, (0.0, 0.0, 0.0, 0.68))
    _panel(gl, 430, 330, cx, cy)
    _draw_text(gl, glut, "JOGO PAUSADO", cx, cy + 112, glut.GLUT_BITMAP_TIMES_ROMAN_24, (0.95, 0.78, 0.38), True)
    for button in ui._buttons(width, height):
        _draw_button(gl, glut, button, glut.GLUT_BITMAP_HELVETICA_18)


def _draw_target_selection(gl, glut, ui: GameUI, width: int, height: int) -> None:
    cx, cy = width / 2.0, height / 2.0
    _rect(gl, 0, 0, width, height, (0.0, 0.0, 0.0, 0.52))
    panel_width = min(430.0, width - 36.0)
    panel_height = 245.0 + max(0, len(ui.target_options) - 2) * 42.0
    _panel(gl, panel_width, panel_height, cx, cy)
    if ui.target_kind == "tunnel":
        title = "TUNEL SECRETO"
        subtitle = "Escolha um jogador para trocar de posicao."
    else:
        title = "ESCOLHER ALVO"
        subtitle = "Voce so pode atacar quem esta na mesma casa."
    _draw_text(gl, glut, title, cx, cy + panel_height / 2.0 - 48, glut.GLUT_BITMAP_TIMES_ROMAN_24, (0.95, 0.78, 0.38), True)
    _draw_text(gl, glut, subtitle, cx, cy + panel_height / 2.0 - 80, glut.GLUT_BITMAP_HELVETICA_12, (0.88, 0.84, 0.75), True)
    for index, option in enumerate(ui.target_options):
        gl.glColor4f(*option["color"], 1.0)
        gl.glPointSize(10.0)
        gl.glBegin(gl.GL_POINTS)
        gl.glVertex2f(cx - 125, cy + 61 - index * 48)
        gl.glEnd()
    for button in ui._buttons(width, height):
        _draw_button(gl, glut, button, glut.GLUT_BITMAP_HELVETICA_18)
    _draw_text(gl, glut, "Pressione N ou ESC para cancelar sem consumir turno.", cx, cy - panel_height / 2.0 + 22, glut.GLUT_BITMAP_HELVETICA_12, (0.72, 0.69, 0.62), True)


def _draw_finished(gl, glut, ui: GameUI, game, width: int, height: int) -> None:
    cx, cy = width / 2.0, height / 2.0
    _rect(gl, 0, 0, width, height, (0.0, 0.0, 0.0, 0.78))
    _panel(gl, min(600, width - 40), 570, cx, cy)
    _draw_text(gl, glut, "FIM DE JOGO!", cx, cy + 238, glut.GLUT_BITMAP_TIMES_ROMAN_24, (0.95, 0.78, 0.38), True)

    winners = game.winners
    if len(winners) == 1:
        if game.winner_player_id is not None:
            winner_text = f"{winners[0].name} alcancou {WIN_SCORE} quilates primeiro!"
        else:
            winner_text = f"Vencedor: {winners[0].name}"
    else:
        winner_text = "Empate: " + ", ".join(player.name for player in winners)
    _draw_text(gl, glut, winner_text, cx, cy + 196, glut.GLUT_BITMAP_HELVETICA_18, (0.98, 0.93, 0.78), True)

    _draw_text(gl, glut, "RANKING FINAL", cx, cy + 145, glut.GLUT_BITMAP_HELVETICA_18, (0.95, 0.78, 0.38), True)
    y = cy + 105
    for rank, player in enumerate(game.ranking, start=1):
        _draw_text(gl, glut, f"{rank}. {player.name[:18]} - {player.score} quilates", cx, y, glut.GLUT_BITMAP_HELVETICA_18, player.color, True)
        y -= 34

    for button in ui._buttons(width, height):
        _draw_button(gl, glut, button, glut.GLUT_BITMAP_HELVETICA_18)


#func para desenhar a tela 2d em si
def draw_ui(ui: GameUI, game, width: int, height: int, now_ms: int = 0) -> None:
    from OpenGL import GL, GLUT

    _begin_overlay(GL, width, height)
    try:
        if ui.screen == "menu":
            _draw_menu(GL, GLUT, ui, width, height)
        elif ui.screen == "instructions":
            _draw_instructions(GL, GLUT, ui, width, height)
        elif ui.screen == "config":
            _draw_config(GL, GLUT, ui, width, height)
        elif ui.screen == "playing":
            _draw_hud(GL, GLUT, ui, game, width, height, now_ms)
        elif ui.screen in {"choose_tunnel_target", "choose_attack_target"}:
            _draw_hud(GL, GLUT, ui, game, width, height, now_ms)
            _draw_target_selection(GL, GLUT, ui, width, height)
        elif ui.screen == "paused":
            _draw_hud(GL, GLUT, ui, game, width, height, now_ms)
            _draw_paused(GL, GLUT, ui, width, height)
        elif ui.screen == "finished":
            _draw_finished(GL, GLUT, ui, game, width, height)
    finally:
        _end_overlay(GL)
