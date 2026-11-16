from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

from camera import OrbitCamera
from game_logic import Game, ItemType
from player_animation import PlayerAnimator
from renderer import draw_scene, init_renderer
from ui import GameUI, draw_ui

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 800

camera = OrbitCamera()
ui = GameUI()
game = Game(2, ["Jogador 1", "Jogador 2"])
animator = PlayerAnimator(duration_ms=360)

#cria a partida com as opções escolhidas no menu
def create_game() -> None:
    global game, animator
    game = Game(ui.player_count, ui.selected_names())
    animator = PlayerAnimator(duration_ms=360)
    camera.reset(game.board_size)
    ui.cancel_target_selection()
    ui.set_message("Mina pronta! Explore, encontre pistas e alcance 100 quilates.", glutGet(GLUT_ELAPSED_TIME))
    ui.screen = "playing"

#reinicia mantendo a quantidade e o nome dos participantes
def restart_game() -> None:
    global game, animator
    names = [player.name for player in game.players]
    game = Game(len(names), names)
    animator = PlayerAnimator(duration_ms=360)
    camera.reset(game.board_size)
    ui.cancel_target_selection()
    ui.set_message("Uma nova partida foi preparada! Alcance 100 quilates.", glutGet(GLUT_ELAPSED_TIME))
    ui.screen = "playing"


def finish_if_needed(result) -> None:
    if result.game_finished:
        ui.screen = "finished"
        print("Partida encerrada. Ranking final:")
        for position, player in enumerate(game.ranking, start=1):
            print(f"{position}. {player.name}: {player.score} quilates ({len(player.diamonds)} diamante(s))")

# apresenta o resultado
def show_result(result, now_ms: int, animate: bool = False) -> None:
    if not result.valid:
        ui.set_message(result.message, now_ms, 3500)
        return

    if animate and result.action in {"move", "dead_end", "map_change"}:
        animator.start_move(result.player_id, result.origin, result.destination, now_ms)
        if result.swapped_player_id is not None:
            animator.start_move(
                result.swapped_player_id,
                result.swapped_origin,
                result.swapped_destination,
                now_ms,
            )
    elif result.action == "map_change" and result.swapped_player_id is not None:
        # Uma troca de túnel pode revelar uma passagem para outra mina.
        animator.start_move(result.player_id, result.origin, result.destination, now_ms)
        animator.start_move(
            result.swapped_player_id,
            result.swapped_origin,
            result.swapped_destination,
            now_ms,
        )
    elif result.action == "tunnel":
        animator.start_move(result.player_id, result.origin, result.destination, now_ms)
        if result.swapped_player_id is not None:
            animator.start_move(
                result.swapped_player_id,
                result.swapped_origin,
                result.swapped_destination,
                now_ms,
            )

    # No ataque a pessoa que apanhou é deslocada
    if result.knocked_back_player_id is not None:
        animator.start_move(
            result.knocked_back_player_id,
            result.knockback_origin,
            result.knockback_destination,
            now_ms,
        )

    if result.action in {"map_change", "attack_map_change"}:
        camera.fit_board(game.board_size)
    ui.set_message(result.message, now_ms, 6500)
    finish_if_needed(result)

#minera a casa atual
def start_mining() -> None:
    now_ms = glutGet(GLUT_ELAPSED_TIME)
    if animator.is_active(now_ms):
        ui.set_message("Aguarde a movimentacao terminar.", now_ms, 1800)
        return

    result = game.mine_current_tile()
    if result.requires_target:
        targets = game.tunnel_targets()
        if not targets:
            ui.set_message(
                "Nao ha outro jogador em uma casa diferente para trocar de posicao. O tunel continua disponivel.",
                now_ms,
                4500,
            )
            return
        ui.begin_target_selection("tunnel", targets)
        ui.set_message(result.message, now_ms, 5000)
        return

    show_result(result, now_ms)

#seleção de jogadores para atacar
def start_attack() -> None:
    now_ms = glutGet(GLUT_ELAPSED_TIME)
    if animator.is_active(now_ms):
        ui.set_message("Aguarde a movimentacao terminar.", now_ms, 1800)
        return

    targets = game.attack_targets()
    if not targets:
        ui.set_message("Nao ha outro jogador na mesma casa para atacar.", now_ms, 2500)
        return

    ui.begin_target_selection("attack", targets)
    ui.set_message("Escolha quem deseja atacar.", now_ms, 3500)

#define o alvo
def resolve_target(player_id: int) -> None:
    now_ms = glutGet(GLUT_ELAPSED_TIME)
    kind = ui.target_kind
    ui.cancel_target_selection()

    if kind == "tunnel":
        result = game.use_secret_tunnel(player_id)
    elif kind == "attack":
        result = game.attack(player_id)
    else:
        ui.set_message("Acao cancelada.", now_ms, 1800)
        return

    show_result(result, now_ms)

def handle_ui_action(action: str | None) -> None:
    if action == "exit":
        glutLeaveMainLoop()
    elif action == "start_game":
        create_game()
    elif action == "restart_game":
        restart_game()
    elif action == "main_menu":
        ui.cancel_target_selection()
        ui.screen = "menu"
    elif action == "mine":
        start_mining()
    elif action == "attack":
        start_attack()
    elif action == "cancel_target_selection":
        ui.set_message("Voce decidiu nao usar essa acao. A casa continua revelada.", glutGet(GLUT_ELAPSED_TIME), 3500)
    elif action and action.startswith("target:"):
        resolve_target(int(action.split(":", 1)[1]))

def display() -> None:
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    camera.apply()
    now_ms = glutGet(GLUT_ELAPSED_TIME)
    draw_scene(game, animator, now_ms)

    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)
    draw_ui(ui, game, width, height, now_ms)
    glutSwapBuffers()

def reshape(width: int, height: int) -> None:
    global WINDOW_WIDTH, WINDOW_HEIGHT
    WINDOW_WIDTH = max(width, 1)
    WINDOW_HEIGHT = max(height, 1)
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    far_plane = max(100.0, game.board_size * 12.0)
    gluPerspective(48.0, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, far_plane)
    glMatrixMode(GL_MODELVIEW)

#recarregar a ui
def refresh_scene(value: int) -> None:
    glutPostRedisplay()
    glutTimerFunc(33, refresh_scene, 0)

def keyboard(key: bytes, x: int, y: int) -> None:
    if ui.screen != "playing":
        action = ui.handle_key(key)
        handle_ui_action(action)
        if ui.screen != "playing":
            camera.active_button = None
        glutPostRedisplay()
        return

    if key in (b"q", b"Q"):
        glutLeaveMainLoop()
        return

    if key == b" ":
        camera.reset()
        glutPostRedisplay()
        return

    if key in (b"w", b"W", b"a", b"A", b"s", b"S", b"d", b"D"):
        now_ms = glutGet(GLUT_ELAPSED_TIME)
        if animator.is_active(now_ms):
            ui.set_message("Aguarde o movimento terminar.", now_ms, 1800)
            glutPostRedisplay()
            return
        result = game.play_move(key.decode("ascii").lower())
        show_result(result, now_ms, animate=True)
        glutPostRedisplay()
        return

    if key in (b"m", b"M"):
        start_mining()
        glutPostRedisplay()
        return

    if key in (b"f", b"F"):
        start_attack()
        glutPostRedisplay()
        return

    action = ui.handle_key(key)
    handle_ui_action(action)
    glutPostRedisplay()


def mouse(button: int, state: int, x: int, y: int) -> None:
    if state == GLUT_DOWN:
        action = ui.handle_click(x, y, WINDOW_WIDTH, WINDOW_HEIGHT)
        if action is not None:
            handle_ui_action(action)
            if ui.screen != "playing":
                camera.active_button = None
            glutPostRedisplay()
            return

    if ui.screen == "playing":
        camera.mouse_button(button, state, x, y)
        glutPostRedisplay()

def motion(x: int, y: int) -> None:
    if ui.screen == "playing":
        camera.mouse_motion(x, y)
        glutPostRedisplay()

def init() -> None:
    glClearColor(0.055, 0.055, 0.065, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glCullFace(GL_BACK)
    init_renderer()

def main() -> None:
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(80, 60)
    glutCreateWindow(b"Diamonds Game CG - Procurando o Tesouro")
    try:
        glutSetOption(GLUT_ACTION_ON_WINDOW_CLOSE, GLUT_ACTION_GLUTMAINLOOP_RETURNS)
    except Exception:
        pass

    init()
    reshape(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutTimerFunc(33, refresh_scene, 0)

    print("\n=== DIAMONDS GAME CG ===")
    print("WASD: mover | M: minerar/usar item | F: atacar | P: pausar")
    print("Ao chegar a uma casa, o item e revelado; diamantes e pistas sao ativados ao minerar.")
    print("Pistas indicam direcao e distancia de diamantes. Vence quem atingir 100 quilates.")
    print("No tunel secreto ou ataque, escolha o alvo pelo numero ou clique.")
    glutMainLoop()

if __name__ == "__main__":
    main()
