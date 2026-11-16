"""Testes para a regra de descoberta dos elementos visuais."""

import unittest

from game_logic import Game, ItemType
from item_visibility import is_item_visible, iter_visible_items


class ItemVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(2, ["Ana", "Beto"], seed=17)

    def find_tile(self, item_type):
        return next(
            tile
            for row in self.game.board
            for tile in row
            if tile.item == item_type
        )

    def test_elements_are_hidden_at_the_start(self):
        self.assertEqual(list(iter_visible_items(self.game)), [])

    def test_revealed_diamond_becomes_visible(self):
        tile = self.find_tile(ItemType.DIAMOND)
        self.assertFalse(is_item_visible(tile))

        tile.revealed = True

        self.assertTrue(is_item_visible(tile))
        self.assertIn(tile, list(iter_visible_items(self.game)))

    def test_collected_diamond_disappears(self):
        tile = self.find_tile(ItemType.DIAMOND)
        tile.revealed = True
        tile.collected_by = 0

        self.assertFalse(is_item_visible(tile))
        self.assertNotIn(tile, list(iter_visible_items(self.game)))

    def test_revealed_clues_and_traps_remain_visible(self):
        item_types = (
            ItemType.CLUE,
            ItemType.DEAD_END,
            ItemType.HIDEOUT,
        )

        for item_type in item_types:
            with self.subTest(item=item_type):
                tile = self.find_tile(item_type)
                tile.revealed = True
                tile.activated = True
                self.assertTrue(is_item_visible(tile))

    def test_revealed_map_change_portal_is_visible(self):
        tile = self.find_tile(ItemType.MAP_CHANGE)
        self.assertFalse(is_item_visible(tile))
        tile.revealed = True
        self.assertTrue(is_item_visible(tile))

    def test_revealed_empty_tile_does_not_create_an_item(self):
        tile = next(
            tile
            for row in self.game.board
            for tile in row
            if tile.item == ItemType.EMPTY
        )
        tile.revealed = True

        self.assertFalse(is_item_visible(tile))


if __name__ == "__main__":
    unittest.main()
