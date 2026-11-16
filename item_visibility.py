#serve para decidir quais itens devem aparecer

from collections.abc import Iterator

from game_logic import Game, ItemType, Tile


#basicamente diz se o item da casa deve aparecer no cenário
def is_item_visible(tile: Tile) -> bool:
    if not tile.revealed or tile.item == ItemType.EMPTY:
        return False

    if tile.item == ItemType.DIAMOND and tile.collected_by is not None:
        return False

    return True


# Percorre as casas que o item já foi descoberto e continua visível
def iter_visible_items(game: Game) -> Iterator[Tile]:
    for row in game.board:
        for tile in row:
            if is_item_visible(tile):
                yield tile
