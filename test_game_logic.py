"""Testes de regras: mover, minerar, túnel secreto e ataque."""

import unittest

from game_logic import (
    BOARD_SIZE,
    TOTAL_MOVES,
    WIN_SCORE,
    Game,
    ItemType,
    action_limit_for_board,
)


class GameLogicTests(unittest.TestCase):
    def test_accepts_only_two_three_or_four_players(self):
        for count in (2, 3, 4):
            self.assertEqual(Game(count, seed=10).number_players, count)
        for count in (1, 5, 0):
            with self.assertRaises(ValueError):
                Game(count, seed=10)

    def test_board_has_expected_items_and_hidden_item_tiles(self):
        game = Game(4, seed=10)
        counts = {item: 0 for item in ItemType}
        for row in game.board:
            for tile in row:
                counts[tile.item] += 1
                if tile.item != ItemType.EMPTY:
                    self.assertFalse(tile.revealed)
        self.assertEqual(BOARD_SIZE * BOARD_SIZE, 36)
        self.assertEqual(counts[ItemType.DIAMOND], 7)
        self.assertEqual(counts[ItemType.CLUE], 2)
        self.assertEqual(counts[ItemType.DEAD_END], 2)
        self.assertEqual(counts[ItemType.HIDEOUT], 2)
        self.assertEqual(counts[ItemType.MAP_CHANGE], 1)

    def test_diamond_values_are_between_one_and_ten(self):
        game = Game(2, seed=11)
        values = [t.diamond_value for row in game.board for t in row if t.item == ItemType.DIAMOND]
        self.assertEqual(len(values), 7)
        self.assertTrue(all(1 <= value <= 10 for value in values))

    def test_invalid_direction_does_not_consume_turn(self):
        game = Game(2, seed=12)
        result = game.play_move("x")
        self.assertFalse(result.valid)
        self.assertFalse(result.consumed_turn)
        self.assertEqual(game.moves_played, 0)
        self.assertEqual(game.current_player.player_id, 0)

    def test_move_outside_board_does_not_consume_turn(self):
        game = Game(2, seed=13)
        result = game.play_move("w")
        self.assertFalse(result.valid)
        self.assertEqual(game.moves_played, 0)
        self.assertEqual(game.players[0].position, (0, 0))

    def test_arrival_reveals_item_but_does_not_mine_it(self):
        game = Game(2, seed=14)
        tile = game.board[0][1]
        tile.item = ItemType.DIAMOND
        tile.diamond_value = 7
        result = game.play_move("d")
        self.assertTrue(result.valid)
        self.assertEqual(result.event, ItemType.DIAMOND)
        self.assertTrue(tile.revealed)
        self.assertFalse(tile.activated)
        self.assertEqual(game.players[0].score, 0)
        self.assertEqual(game.players[0].diamonds, [])
        self.assertEqual(game.current_player.player_id, 1)

    def test_player_can_leave_revealed_tile_without_mining(self):
        game = Game(2, seed=15)
        tile = game.board[0][1]
        tile.item = ItemType.CLUE
        game.play_move("d")
        game.play_move("a")
        # Jogador 0 decide seguir para outra casa em vez de minerar a pista.
        result = game.play_move("d")
        self.assertTrue(result.valid)
        self.assertTrue(tile.revealed)
        self.assertFalse(tile.activated)
        self.assertEqual(game.players[0].score, 0)

    def test_mining_diamond_adds_score_and_inventory(self):
        game = Game(2, seed=16)
        tile = game.board[0][1]
        tile.item = ItemType.DIAMOND
        tile.diamond_value = 8
        game.play_move("d")
        game.play_move("a")
        result = game.mine_current_tile()
        self.assertTrue(result.valid)
        self.assertTrue(result.consumed_turn)
        self.assertEqual(result.action, "mine")
        self.assertEqual(game.players[0].score, 8)
        self.assertEqual(game.players[0].diamonds, [8])
        self.assertEqual(game.players[0].moves, 2)  # movimento + mineracao
        self.assertTrue(tile.activated)
        self.assertEqual(tile.collected_by, 0)
        self.assertEqual(game.current_player.player_id, 1)

    def test_clue_is_mined_but_dead_end_penalty_applies_on_arrival(self):
        game = Game(2, seed=18)
        clue = game.board[0][1]
        clue.item = ItemType.CLUE
        dead_end = game.board[5][4]
        dead_end.item = ItemType.DEAD_END

        game.play_move("d")  # Jogador 0 revela a pista.
        self.assertEqual(game.players[0].score, 0)
        game.play_move("a")  # Jogador 1 chega ao túnel sem saída.
        self.assertEqual(game.players[1].score, -10)
        self.assertTrue(dead_end.revealed)
        self.assertTrue(dead_end.activated)

        result = game.mine_current_tile()  # Jogador 0 minera a pista.
        self.assertTrue(result.valid)
        self.assertEqual(result.points_delta, 0)
        self.assertEqual(game.players[0].score, 0)
        self.assertIn("diamante", result.message.lower())
        self.assertIn("movimentos", result.message.lower())
        self.assertIsNotNone(game.latest_hint)

    def test_dead_end_is_applied_once_and_cannot_be_mined(self):
        game = Game(2, seed=180)
        trap = game.board[0][1]
        trap.item = ItemType.DEAD_END
        game.players[0].score = 12

        result = game.play_move("d")
        self.assertTrue(result.valid)
        self.assertEqual(result.action, "dead_end")
        self.assertEqual(result.points_delta, -10)
        self.assertEqual(game.players[0].score, 2)
        self.assertTrue(trap.revealed)
        self.assertTrue(trap.activated)
        self.assertEqual(game.moves_played, 1)

        game.play_move("a")  # Passa a vez e volta ao jogador 0.
        result = game.mine_current_tile()
        self.assertFalse(result.valid)
        self.assertEqual(game.players[0].score, 2)
        self.assertEqual(game.moves_played, 2)

    def test_new_mine_item_is_distributed_once(self):
        game = Game(4, seed=181)
        occurrences = [
            tile for row in game.board for tile in row
            if tile.item == ItemType.MAP_CHANGE
        ]
        self.assertEqual(len(occurrences), 1)
        self.assertFalse(occurrences[0].revealed)

    def test_new_mine_preserves_positions_scores_and_diamonds_and_resets_turns(self):
        game = Game(3, ["Ana", "Beto", "Caio"], seed=182)
        game.players[0].position = (2, 2)
        game.players[1].position = (3, 3)
        game.players[2].position = (4, 4)
        game.players[0].score = 11
        game.players[0].diamonds = [4, 7]
        game.players[1].score = 3  # Pontos de pista não fazem parte do inventário.
        game.players[1].diamonds = []
        game.players[2].score = 5
        game.players[2].diamonds = [5]
        game.players[0].moves = 2
        game.players[1].moves = 1
        game.players[2].moves = 1
        game.moves_played = 4

        passage = game.board[2][3]
        passage.item = ItemType.MAP_CHANGE
        old_board = game.board
        saved_positions = [player.position for player in game.players]
        saved_scores = [player.score for player in game.players]
        saved_diamonds = [list(player.diamonds) for player in game.players]

        result = game.play_move("d")

        self.assertTrue(result.valid)
        self.assertTrue(result.consumed_turn)
        self.assertEqual(result.action, "map_change")
        self.assertFalse(result.game_finished)
        self.assertEqual(game.map_number, 2)
        self.assertIsNot(game.board, old_board)
        self.assertEqual(game.players[0].position, (2, 3))
        self.assertEqual(game.players[1].position, saved_positions[1])
        self.assertEqual(game.players[2].position, saved_positions[2])
        self.assertEqual([player.score for player in game.players], saved_scores)
        self.assertEqual([player.diamonds for player in game.players], saved_diamonds)
        self.assertEqual(game.moves_played, 0)
        self.assertEqual(game.board_size, 7)
        self.assertEqual(game.total_moves, 60)
        self.assertEqual(game.remaining_moves, game.total_moves)
        self.assertEqual(game.moves_per_player, 20)
        self.assertEqual([player.moves for player in game.players], [0, 0, 0])
        self.assertEqual(game.current_player.player_id, 1)

        for player in game.players:
            current_tile = game.tile_at(player.position)
            self.assertTrue(current_tile.revealed)
            self.assertIn(player.player_id, current_tile.visited_by)
            self.assertEqual(current_tile.item, ItemType.EMPTY)

    def test_map_change_resets_even_if_it_is_the_36th_action(self):
        game = Game(2, seed=183)
        game.players[0].position = (2, 2)
        game.players[1].position = (5, 5)
        game.current_player_index = 0
        game.moves_played = 35
        game.players[0].moves = 17
        game.players[1].moves = 18
        game.board[2][3].item = ItemType.MAP_CHANGE

        result = game.play_move("d")

        self.assertTrue(result.valid)
        self.assertEqual(game.map_number, 2)
        self.assertFalse(game.finished)
        self.assertEqual(game.moves_played, 0)
        self.assertEqual(game.current_player.player_id, 1)

    def test_new_mine_does_not_place_items_under_any_player(self):
        game = Game(4, seed=184)
        positions = [(1, 1), (2, 2), (3, 3), (4, 4)]
        for player, position in zip(game.players, positions):
            player.position = position
        game._generate_next_mine(next_player_index=2)

        for position in positions:
            self.assertEqual(game.tile_at(position).item, ItemType.EMPTY)
            self.assertTrue(game.tile_at(position).revealed)

        item_count = sum(
            tile.item != ItemType.EMPTY
            for row in game.board for tile in row
        )
        self.assertEqual(game.board_size, 7)
        self.assertEqual(item_count, 18)

    def test_mining_empty_or_already_activated_tile_is_invalid(self):
        game = Game(2, seed=20)
        result = game.mine_current_tile()
        self.assertFalse(result.valid)
        self.assertEqual(game.moves_played, 0)

        tile = game.board[0][1]
        tile.item = ItemType.CLUE
        game.play_move("d")
        game.play_move("a")
        game.mine_current_tile()
        game.play_move("a")
        result = game.mine_current_tile()
        self.assertFalse(result.valid)
        self.assertEqual(game.moves_played, 4)

    def test_secret_tunnel_requests_target_without_consuming_turn(self):
        game = Game(2, seed=21)
        game.board[0][1].item = ItemType.HIDEOUT
        game.play_move("d")
        game.play_move("a")
        result = game.mine_current_tile()
        self.assertTrue(result.valid)
        self.assertTrue(result.requires_target)
        self.assertFalse(result.consumed_turn)
        self.assertEqual(game.moves_played, 2)
        self.assertFalse(game.tile_at((0, 1)).activated)

    def test_secret_tunnel_swaps_positions_with_selected_player(self):
        game = Game(2, seed=22)
        game.board[0][1].item = ItemType.HIDEOUT
        game.play_move("d")
        game.play_move("a")
        origin_current = game.players[0].position
        origin_target = game.players[1].position
        result = game.use_secret_tunnel(1)
        self.assertTrue(result.valid)
        self.assertEqual(result.action, "tunnel")
        self.assertEqual(game.players[0].position, origin_target)
        self.assertEqual(game.players[1].position, origin_current)
        self.assertEqual(game.players[0].moves, 2)  # movimento + uso do tunel
        self.assertTrue(game.tile_at(origin_current).activated)
        self.assertTrue(game.tile_at(origin_target).revealed)
        self.assertEqual(game.current_player.player_id, 1)

    def test_unused_secret_tunnel_remains_revealed_and_unactivated(self):
        game = Game(2, seed=30)
        tunnel = game.board[0][1]
        tunnel.item = ItemType.HIDEOUT
        game.play_move("d")
        self.assertTrue(tunnel.revealed)
        game.play_move("a")
        # O jogador 0 escolhe mover em vez de minerar/usar o túnel.
        game.play_move("d")
        self.assertTrue(tunnel.revealed)
        self.assertFalse(tunnel.activated)

    def test_invalid_secret_tunnel_target_does_not_consume_turn(self):
        game = Game(2, seed=23)
        game.board[0][1].item = ItemType.HIDEOUT
        game.play_move("d")
        game.play_move("a")
        before = game.moves_played
        result = game.use_secret_tunnel(0)
        self.assertFalse(result.valid)
        self.assertEqual(game.moves_played, before)

    def test_secret_tunnel_arrival_applies_dead_end_immediately(self):
        game = Game(2, seed=185)
        game.players[0].position = (1, 1)
        game.players[1].position = (4, 4)
        hideout = game.tile_at((1, 1))
        hideout.item = ItemType.HIDEOUT
        hideout.revealed = True
        dead_end = game.tile_at((4, 4))
        dead_end.item = ItemType.DEAD_END

        result = game.use_secret_tunnel(1)

        self.assertTrue(result.valid)
        self.assertEqual(result.action, "tunnel")
        self.assertEqual(game.players[0].score, -10)
        self.assertTrue(dead_end.revealed)
        self.assertTrue(dead_end.activated)
        self.assertEqual(result.points_delta, -10)

    def test_secret_tunnel_can_trigger_new_mine_on_arrival(self):
        game = Game(2, seed=186)
        game.players[0].position = (1, 1)
        game.players[1].position = (4, 4)
        game.players[0].score = 9
        game.players[0].diamonds = [9]
        hideout = game.tile_at((1, 1))
        hideout.item = ItemType.HIDEOUT
        hideout.revealed = True
        game.tile_at((4, 4)).item = ItemType.MAP_CHANGE

        result = game.use_secret_tunnel(1)

        self.assertTrue(result.valid)
        self.assertEqual(result.action, "map_change")
        self.assertEqual(game.map_number, 2)
        self.assertEqual(game.moves_played, 0)
        self.assertEqual(game.current_player.player_id, 1)
        self.assertEqual(game.players[0].position, (4, 4))
        self.assertEqual(game.players[1].position, (1, 1))
        self.assertEqual(game.players[0].score, 9)
        self.assertEqual(game.players[0].diamonds, [9])

    def test_attack_only_works_on_same_tile_and_steals_one_diamond(self):
        game = Game(2, seed=24)
        game.players[0].position = (2, 2)
        game.players[1].position = (2, 2)
        game.players[0].score = 2
        game.players[0].diamonds = [2]
        game.players[1].score = 13
        game.players[1].diamonds = [4, 9]

        result = game.attack(1)
        self.assertTrue(result.valid)
        self.assertEqual(result.action, "attack")
        self.assertIn(result.stolen_diamond, (4, 9))
        self.assertEqual(sum(game.players[0].diamonds), game.players[0].score)
        self.assertEqual(sum(game.players[1].diamonds), game.players[1].score)
        self.assertEqual(len(game.players[0].diamonds), 2)
        self.assertEqual(len(game.players[1].diamonds), 1)
        self.assertEqual(game.moves_played, 1)

    def test_attack_without_target_diamonds_has_no_score_effect_but_uses_turn(self):
        game = Game(2, seed=25)
        game.players[0].position = (2, 2)
        game.players[1].position = (2, 2)
        game.players[1].score = 3  # Pontos de uma pista, mas nenhum diamante.
        result = game.attack(1)
        self.assertTrue(result.valid)
        self.assertIsNone(result.stolen_diamond)
        self.assertEqual(game.players[0].score, 0)
        self.assertEqual(game.players[1].score, 3)
        self.assertEqual(game.players[0].moves, 1)
        self.assertEqual(game.players[1].diamonds, [])
        self.assertEqual(game.moves_played, 1)

    def test_attack_is_invalid_when_players_are_not_together(self):
        game = Game(2, seed=26)
        result = game.attack(1)
        self.assertFalse(result.valid)
        self.assertEqual(game.moves_played, 0)

    def test_all_valid_actions_are_counted_toward_36_turns(self):
        expected_per_player = {2: 18, 3: 12, 4: 9}
        for count in (2, 3, 4):
            game = Game(count, seed=27)
            for row in game.board:
                for tile in row:
                    if tile.item == ItemType.MAP_CHANGE:
                        tile.item = ItemType.EMPTY
            while not game.finished:
                for direction in ("w", "a", "s", "d"):
                    result = game.play_move(direction)
                    if result.valid:
                        break
                self.assertTrue(result.valid)
            self.assertEqual(game.moves_played, TOTAL_MOVES)
            self.assertEqual([p.moves for p in game.players], [expected_per_player[count]] * count)

    def test_game_finishes_after_36_valid_actions_and_exposes_winners(self):
        game = Game(2, seed=28)
        for row in game.board:
            for tile in row:
                if tile.item == ItemType.MAP_CHANGE:
                    tile.item = ItemType.EMPTY
        directions = ("d", "s", "a", "w")
        while not game.finished:
            for direction in directions:
                result = game.play_move(direction)
                if result.valid:
                    break
        self.assertEqual(game.moves_played, 36)
        self.assertTrue(game.finished)
        self.assertGreaterEqual(len(game.winners), 1)
        self.assertEqual(sum(p.moves for p in game.players), 36)

    def test_each_new_mine_grows_board_and_action_limit(self):
        game = Game(3, seed=201)
        self.assertEqual(game.board_size, 6)
        self.assertEqual(game.total_moves, 36)

        game._generate_next_mine(next_player_index=1)
        self.assertEqual(game.map_number, 2)
        self.assertEqual(game.board_size, 7)
        self.assertEqual(len(game.board), 7)
        self.assertTrue(all(len(row) == 7 for row in game.board))
        self.assertEqual(game.total_moves, 60)
        self.assertEqual(game.moves_per_player, 20)

        game._generate_next_mine(next_player_index=2)
        self.assertEqual(game.map_number, 3)
        self.assertEqual(game.board_size, 8)
        self.assertEqual(game.total_moves, 72)
        self.assertEqual(game.moves_per_player, 24)

    def test_action_limit_is_multiple_of_twelve_and_divisible_by_player_count(self):
        for size in range(6, 16):
            limit = action_limit_for_board(size)
            self.assertEqual(limit % 12, 0)
            for player_count in (2, 3, 4):
                self.assertEqual(limit % player_count, 0)
        self.assertEqual(action_limit_for_board(6), 36)
        self.assertEqual(action_limit_for_board(7), 60)
        self.assertEqual(action_limit_for_board(8), 72)

    def test_player_can_move_into_new_rows_and_columns_on_larger_mines(self):
        game = Game(2, seed=210)
        game._generate_next_mine(next_player_index=0)
        game.players[0].position = (5, 5)
        game.players[1].position = (0, 0)
        game.current_player_index = 0
        tile = game.tile_at((5, 6))
        tile.item = ItemType.EMPTY

        result = game.play_move("d")

        self.assertTrue(result.valid)
        self.assertEqual(game.players[0].position, (5, 6))
        self.assertTrue(tile.revealed)

    def test_each_mine_contains_exactly_one_passage(self):
        game = Game(2, seed=202)
        for expected_map in range(1, 5):
            if expected_map > 1:
                game._generate_next_mine(next_player_index=0)
            passages = [
                tile for row in game.board for tile in row
                if tile.item == ItemType.MAP_CHANGE
            ]
            self.assertEqual(len(passages), 1)

    def test_later_mines_scale_item_counts_with_area(self):
        game = Game(2, seed=203)
        game._generate_next_mine(next_player_index=0)
        counts = {item: 0 for item in ItemType}
        for row in game.board:
            for tile in row:
                counts[tile.item] += 1
        self.assertEqual(counts[ItemType.DIAMOND], 10)
        self.assertEqual(counts[ItemType.CLUE], 2)
        self.assertEqual(counts[ItemType.DEAD_END], 3)
        self.assertEqual(counts[ItemType.HIDEOUT], 2)
        self.assertEqual(counts[ItemType.MAP_CHANGE], 1)

    def test_clue_gives_directional_hint_without_points(self):
        game = Game(2, seed=204)
        for row in game.board:
            for tile in row:
                if tile.item == ItemType.DIAMOND:
                    tile.item = ItemType.EMPTY
                    tile.diamond_value = None
        clue = game.tile_at((0, 1))
        clue.item = ItemType.CLUE
        diamond = game.tile_at((3, 4))
        diamond.item = ItemType.DIAMOND
        diamond.diamond_value = 6

        game.play_move("d")  # jogador 0 chega na pista
        game.play_move("a")  # jogador 1 consome seu movimento
        result = game.mine_current_tile()

        self.assertTrue(result.valid)
        self.assertEqual(result.points_delta, 0)
        self.assertEqual(game.players[0].score, 0)
        self.assertEqual(game.players[0].diamonds, [])
        self.assertIn("sudeste", result.message)
        self.assertIn("6 movimentos", result.message)
        self.assertTrue(clue.activated)
        self.assertIn("sudeste", game.latest_hint)

    def test_clue_reports_when_no_uncollected_diamonds_remain(self):
        game = Game(2, seed=205)
        for row in game.board:
            for tile in row:
                if tile.item == ItemType.DIAMOND:
                    tile.activated = True
                    tile.collected_by = 0
        clue = game.tile_at((0, 1))
        clue.item = ItemType.CLUE
        game.play_move("d")
        game.play_move("a")
        result = game.mine_current_tile()
        self.assertTrue(result.valid)
        self.assertIn("nao tem mais diamantes", result.message)
        self.assertEqual(game.players[0].score, 0)

    def test_latest_clue_is_cleared_when_entering_new_mine(self):
        game = Game(2, seed=208)
        game.latest_hint = "Diamante a leste, 3 mov."
        game._generate_next_mine(next_player_index=1)
        self.assertIsNone(game.latest_hint)
        self.assertEqual(game.hinted_diamonds, set())

    def test_score_goal_takes_priority_over_mine_action_limit(self):
        game = Game(2, seed=209)
        game.players[0].score = 90
        game.players[0].diamonds = [90]
        game.players[0].position = (0, 0)
        game.players[1].position = (5, 5)
        game.current_player_index = 0
        game.moves_played = game.total_moves - 1
        game.players[0].position = (0, 1)
        game.board[0][1].item = ItemType.DIAMOND
        game.board[0][1].diamond_value = 10
        game.board[0][1].revealed = True

        result = game.mine_current_tile()
        self.assertTrue(result.game_finished)
        self.assertEqual(game.winner_player_id, 0)
        self.assertEqual(game.players[0].score, WIN_SCORE)

    def test_first_player_to_reach_100_wins_immediately(self):
        game = Game(2, seed=206)
        game.players[0].score = 95
        game.players[0].diamonds = [95]
        tile = game.tile_at((0, 1))
        tile.item = ItemType.DIAMOND
        tile.diamond_value = 10
        game.play_move("d")
        game.play_move("a")

        result = game.mine_current_tile()
        self.assertTrue(result.valid)
        self.assertTrue(result.game_finished)
        self.assertTrue(game.finished)
        self.assertEqual(game.players[0].score, 105)
        self.assertEqual(game.winners, [game.players[0]])
        self.assertEqual(game.winner_player_id, 0)
        blocked = game.play_move("d")
        self.assertFalse(blocked.valid)

    def test_attack_can_trigger_100_quilates_victory(self):
        game = Game(2, seed=207)
        game.players[0].position = (2, 2)
        game.players[1].position = (2, 2)
        game.players[0].score = 95
        game.players[0].diamonds = [95]
        game.players[1].score = 10
        game.players[1].diamonds = [10]

        result = game.attack(1)
        self.assertTrue(result.valid)
        self.assertTrue(result.game_finished)
        self.assertEqual(game.players[0].score, 105)
        self.assertEqual(game.players[1].score, 0)
        self.assertEqual(game.winners, [game.players[0]])

    def test_player_can_move_onto_a_tile_occupied_by_another_player(self):
        game = Game(2, seed=31)
        game.players[1].position = (0, 1)
        result = game.play_move("d")
        self.assertTrue(result.valid)
        self.assertEqual(game.players[0].position, game.players[1].position)
        # A vez passa ao jogador 1, que pode atacar o jogador 0 na mesma casa.
        self.assertEqual([p.player_id for p in game.attack_targets()], [0])

    def test_tunnel_targets_excludes_players_already_on_same_tile(self):
        game = Game(3, seed=32)
        game.players[1].position = game.players[0].position
        self.assertEqual([p.player_id for p in game.tunnel_targets()], [2])

    def test_attack_targets_returns_only_players_on_current_tile(self):
        game = Game(4, seed=29)
        game.players[1].position = game.players[0].position
        game.players[2].position = game.players[0].position
        self.assertEqual([p.player_id for p in game.attack_targets()], [1, 2])


    def test_attack_pushes_target_to_random_orthogonal_adjacent_tile(self):
        game = Game(2, seed=301)
        game.players[0].position = (2, 2)
        game.players[1].position = (2, 2)
        game.rng.choice = lambda options: options[-1]

        result = game.attack(1)

        self.assertTrue(result.valid)
        self.assertEqual(result.action, "attack")
        self.assertEqual(game.players[0].position, (2, 2))
        self.assertEqual(game.players[1].position, result.knockback_destination)
        self.assertEqual(result.knocked_back_player_id, 1)
        self.assertEqual(result.knockback_origin, (2, 2))
        self.assertEqual(
            abs(result.knockback_destination[0] - 2)
            + abs(result.knockback_destination[1] - 2),
            1,
        )
        destination_tile = game.tile_at(result.knockback_destination)
        self.assertTrue(destination_tile.revealed)
        self.assertIn(1, destination_tile.visited_by)
        self.assertEqual(game.moves_played, 1)

    def test_attack_push_from_corner_stays_inside_board(self):
        game = Game(2, seed=302)
        game.players[0].position = (0, 0)
        game.players[1].position = (0, 0)
        game.rng.choice = lambda options: options[0]

        result = game.attack(1)

        self.assertTrue(result.valid)
        self.assertEqual(result.knockback_destination, (1, 0))
        self.assertEqual(
            abs(result.knockback_destination[0])
            + abs(result.knockback_destination[1]),
            1,
        )

    def test_attack_prefers_unoccupied_adjacent_tiles_when_available(self):
        game = Game(3, seed=303)
        game.players[0].position = (2, 2)
        game.players[1].position = (2, 2)
        game.players[2].position = (1, 2)
        game.rng.choice = lambda options: options[0]

        result = game.attack(1)

        self.assertTrue(result.valid)
        self.assertNotEqual(result.knockback_destination, game.players[2].position)
        self.assertEqual(
            abs(result.knockback_destination[0] - 2)
            + abs(result.knockback_destination[1] - 2),
            1,
        )

    def test_attack_knockback_reveals_and_automatically_applies_dead_end(self):
        game = Game(2, seed=304)
        game.players[0].position = (2, 2)
        game.players[1].position = (2, 2)
        game.players[1].score = 11
        game.players[1].diamonds = [5]
        game.players[0].diamonds = []
        game.rng.choice = lambda options: next(
            position for position in options if position == (1, 2)
        )
        trap = game.tile_at((1, 2))
        trap.item = ItemType.DEAD_END

        result = game.attack(1)

        self.assertTrue(result.valid)
        self.assertEqual(result.knockback_destination, (1, 2))
        self.assertEqual(result.knockback_event, ItemType.DEAD_END)
        self.assertTrue(trap.revealed)
        self.assertTrue(trap.activated)
        self.assertEqual(game.players[1].score, -4)  # -5 pelo roubo e -10 pela armadilha
        self.assertEqual(game.players[0].score, 5)
        self.assertEqual(result.opponent_deltas[1], -15)
        self.assertIn("perdeu mais 10", result.message)

    def test_attack_knockback_into_passage_generates_next_mine(self):
        game = Game(2, seed=305)
        game.players[0].position = (2, 2)
        game.players[1].position = (2, 2)
        game.players[1].score = 7
        game.players[1].diamonds = [7]
        passage = game.tile_at((1, 2))
        passage.item = ItemType.MAP_CHANGE
        game.rng.choice = lambda options: next(
            position for position in options if position == (1, 2)
        )

        result = game.attack(1)

        self.assertTrue(result.valid)
        self.assertEqual(result.action, "attack_map_change")
        self.assertEqual(result.knockback_event, ItemType.MAP_CHANGE)
        self.assertEqual(game.map_number, 2)
        self.assertEqual(game.board_size, 7)
        self.assertEqual(game.players[0].position, (2, 2))
        self.assertEqual(game.players[1].position, (1, 2))
        self.assertEqual(game.players[1].score, 0)
        self.assertEqual(game.players[1].diamonds, [])
        self.assertEqual(game.moves_played, 0)
        self.assertEqual(game.current_player.player_id, 1)
        self.assertFalse(game.finished)

    def test_attack_victory_has_priority_when_knockback_reaches_passage(self):
        game = Game(2, seed=306)
        game.players[0].position = (2, 2)
        game.players[1].position = (2, 2)
        game.players[0].score = 95
        game.players[0].diamonds = [95]
        game.players[1].score = 5
        game.players[1].diamonds = [5]
        game.tile_at((1, 2)).item = ItemType.MAP_CHANGE
        game.rng.choice = lambda options: next(
            position for position in options if position == (1, 2)
        )

        result = game.attack(1)

        self.assertTrue(result.valid)
        self.assertTrue(result.game_finished)
        self.assertEqual(game.winner_player_id, 0)
        self.assertEqual(game.players[0].score, WIN_SCORE)
        self.assertEqual(game.map_number, 1)
        self.assertEqual(game.players[1].position, (1, 2))

    def test_attack_without_diamond_still_pushes_target(self):
        game = Game(2, seed=307)
        game.players[0].position = (3, 3)
        game.players[1].position = (3, 3)
        game.players[1].diamonds = []
        game.rng.choice = lambda options: options[0]

        result = game.attack(1)

        self.assertTrue(result.valid)
        self.assertIsNone(result.stolen_diamond)
        self.assertNotEqual(game.players[1].position, (3, 3))
        self.assertEqual(
            abs(game.players[1].position[0] - 3)
            + abs(game.players[1].position[1] - 3),
            1,
        )



if __name__ == "__main__":
    unittest.main(verbosity=2)
