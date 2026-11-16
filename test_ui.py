"""Testes de estado e interacao da interface, sem precisar de OpenGL."""

import unittest

from ui import GameUI
from game_logic import Game


class TestGameUI(unittest.TestCase):
    def setUp(self):
        self.ui = GameUI()
        self.width = 1100
        self.height = 800

    def click_button(self, action):
        button = next(button for button in self.ui._buttons(self.width, self.height) if button.action == action)
        mouse_x = int(button.x + button.width / 2)
        mouse_y = int(self.height - (button.y + button.height / 2))
        return self.ui.handle_click(mouse_x, mouse_y, self.width, self.height)

    def test_menu_start_opens_config(self):
        self.assertEqual(self.ui.screen, "menu")
        self.assertEqual(self.click_button("menu_start"), "")
        self.assertEqual(self.ui.screen, "config")

    def test_player_count_selection(self):
        self.ui.screen = "config"
        self.click_button("count_4")
        self.assertEqual(self.ui.player_count, 4)
        self.assertEqual(len(self.ui.selected_names()), 4)

    def test_name_editing(self):
        self.ui.screen = "config"
        self.ui.active_name = 0
        self.ui.handle_key(b"M")
        self.ui.handle_key(b"a")
        self.ui.handle_key(b"r")
        self.assertEqual(self.ui.names[0], "Mar")

    def test_enter_advances_name_field(self):
        self.ui.screen = "config"
        self.ui.handle_key(b"\r")
        self.assertEqual(self.ui.active_name, 1)

    def test_tab_cycles_between_name_fields(self):
        self.ui.screen = "config"
        self.ui.handle_key(b"\t")
        self.assertEqual(self.ui.active_name, 1)
        self.ui.handle_key(b"\t")
        self.assertEqual(self.ui.active_name, 0)

    def test_start_returns_action_and_changes_screen(self):
        self.ui.screen = "config"
        self.assertEqual(self.click_button("config_start"), "start_game")
        self.assertEqual(self.ui.screen, "playing")

    def test_pause_and_resume(self):
        self.ui.screen = "playing"
        self.click_button("pause")
        self.assertEqual(self.ui.screen, "paused")
        self.click_button("resume")
        self.assertEqual(self.ui.screen, "playing")

    def test_escape_from_menu_requests_exit(self):
        self.assertEqual(self.ui.handle_key(b"\x1b"), "exit")


    def test_mine_and_attack_buttons_return_game_actions(self):
        self.ui.screen = "playing"
        self.assertEqual(self.click_button("mine"), "mine")
        self.assertEqual(self.click_button("attack"), "attack")

    def test_target_selection_click_returns_selected_player_id(self):
        game = Game(3, ["Ana", "Beto", "Caio"], seed=8)
        self.ui.begin_target_selection("tunnel", [game.players[1], game.players[2]])
        self.assertEqual(self.ui.screen, "choose_tunnel_target")
        self.assertEqual(self.click_button("target_2"), "target:2")
        self.assertEqual(self.ui.screen, "playing")

    def test_target_selection_number_uses_player_id_not_list_position(self):
        game = Game(4, ["Ana", "Beto", "Caio", "Dora"], seed=9)
        self.ui.begin_target_selection("attack", [game.players[1], game.players[3]])
        # A tecla 4 deve atingir o jogador de ID 3, mesmo sendo a segunda opção.
        self.assertEqual(self.ui.handle_key(b"4"), "target:3")

    def test_target_selection_cancel_button_closes_overlay(self):
        game = Game(2, ["Ana", "Beto"], seed=11)
        self.ui.begin_target_selection("tunnel", [game.players[1]])
        self.assertEqual(self.click_button("target_cancel"), "cancel_target_selection")
        self.assertEqual(self.ui.screen, "playing")
        self.assertIsNone(self.ui.target_kind)

    def test_target_selection_can_be_cancelled_without_consuming_game_turn(self):
        game = Game(2, seed=10)
        self.ui.begin_target_selection("tunnel", [game.players[1]])
        self.assertEqual(self.ui.handle_key(b"n"), "cancel_target_selection")
        self.assertEqual(self.ui.screen, "playing")
        self.assertEqual(self.ui.target_options, [])

    def test_click_outside_buttons_is_not_consumed(self):
        self.assertIsNone(self.ui.handle_click(5, 5, self.width, self.height))


if __name__ == "__main__":
    unittest.main()
