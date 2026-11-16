#para a lógica usei PyOpenGL
from dataclasses import dataclass, field
from enum import Enum
from random import Random
from typing import Optional


# O primeiro mapa começa em 6x6. Cada nova mina acrescenta uma linha e uma coluna. O limite de ações acompanha a área e é arredondado para um múltiplo de 12, garantindo divisão exata entre 2, 3 ou 4 jogadores.
BOARD_SIZE = 6
TOTAL_MOVES = 36
WIN_SCORE = 100
VALID_PLAYER_COUNTS = (2, 3, 4)

def board_size_for_map(map_number: int) -> int:
    if map_number < 1:
        raise ValueError("O número da mina deve ser positivo.")
    return BOARD_SIZE + map_number - 1

def action_limit_for_board(board_size: int) -> int:
    if board_size < BOARD_SIZE:
        raise ValueError("O tabuleiro não pode ser menor que o mapa inicial.")
    area = board_size * board_size
    return ((area + 11) // 12) * 12

DIRECTIONS = {
    "w": (-1, 0),
    "s": (1, 0),
    "a": (0, -1),
    "d": (0, 1),
}

PLAYER_COLORS = (
    (0.90, 0.20, 0.18),
    (0.15, 0.45, 0.95),
    (0.20, 0.75, 0.30),
    (0.95, 0.75, 0.12),
)

NUM_DIAMONDS = 7
NUM_CLUES = 2
NUM_DEAD_ENDS = 2
NUM_HIDEOUTS = 2
NUM_MAP_CHANGES = 1

class ItemType(Enum):
    EMPTY = "Vazio"
    DIAMOND = "Diamante"
    CLUE = "Pista"
    DEAD_END = "Túnel sem saída"
    HIDEOUT = "Túnel secreto"
    MAP_CHANGE = "Passagem para outra mina"

# casa da mina
@dataclass
class Tile:
    row: int
    col: int
    item: ItemType = ItemType.EMPTY
    diamond_value: Optional[int] = None
    revealed: bool = False
    activated: bool = False
    visited_by: set[int] = field(default_factory=set)
    collected_by: Optional[int] = None

#estados do player com o número de diamantes que tem
@dataclass
class Player:
    player_id: int
    name: str
    color: tuple[float, float, float]
    position: tuple[int, int]
    score: int = 0
    moves: int = 0
    diamonds: list[int] = field(default_factory=list)

# resultado da ação
@dataclass
class MoveResult:
    valid: bool
    consumed_turn: bool
    player_id: int
    player_name: str
    origin: tuple[int, int]
    destination: tuple[int, int]
    event: Optional[ItemType] = None
    points_delta: int = 0
    opponent_deltas: dict[int, int] = field(default_factory=dict)
    message: str = ""
    game_finished: bool = False
    action: str = "move"
    requires_target: bool = False
    target_player_id: Optional[int] = None
    stolen_diamond: Optional[int] = None
    swapped_player_id: Optional[int] = None
    swapped_origin: Optional[tuple[int, int]] = None
    swapped_destination: Optional[tuple[int, int]] = None
    knocked_back_player_id: Optional[int] = None
    knockback_origin: Optional[tuple[int, int]] = None
    knockback_destination: Optional[tuple[int, int]] = None
    knockback_event: Optional[ItemType] = None

#controla a partida, turnos, movimentação, mineração, tunel e ataques
class Game:
    def __init__(
        self,
        number_players: int,
        player_names: Optional[list[str]] = None,
        seed: Optional[int] = None,
    ) -> None:
        if number_players not in VALID_PLAYER_COUNTS:
            raise ValueError("O jogo aceita apenas 2, 3 ou 4 jogadores.")

        if player_names is None:
            player_names = [f"Jogador {i + 1}" for i in range(number_players)]
        if len(player_names) != number_players:
            raise ValueError("Informe exatamente um nome para cada jogador.")

        cleaned_names = [name.strip() for name in player_names]
        if any(not name for name in cleaned_names):
            raise ValueError("Os nomes dos jogadores não podem ficar vazios.")

        self.rng = Random(seed)
        self.number_players = number_players
        self.map_number = 1
        self.board_size = board_size_for_map(self.map_number)
        self.total_moves = action_limit_for_board(self.board_size)
        self.moves_per_player = self.total_moves // number_players
        self.players = self._create_players(cleaned_names)
        self.board = self._create_board()
        self.moves_played = 0
        self.current_player_index = 0
        self.finished = False
        self.winner_player_id: Optional[int] = None
        self.latest_hint: Optional[str] = None
        self.hinted_diamonds: set[tuple[int, int]] = set()

        for player in self.players:
            start_tile = self.tile_at(player.position)
            start_tile.revealed = True
            start_tile.visited_by.add(player.player_id)

    @staticmethod
    def _starting_positions(
        number_players: int, board_size: int = BOARD_SIZE
    ) -> list[tuple[int, int]]:
        last = board_size - 1
        positions = {
            2: [(0, 0), (last, last)],
            3: [(0, 0), (last, last), (0, last)],
            4: [(0, 0), (0, last), (last, 0), (last, last)],
        }
        return positions[number_players]

    def _create_players(self, names: list[str]) -> list[Player]:
        starts = self._starting_positions(self.number_players)
        return [
            Player(i, names[i], PLAYER_COLORS[i], starts[i])
            for i in range(self.number_players)
        ]
    
    #calcula a quantidade proporcional em relação ao tamanho da min
    def _item_counts_for_current_mine(self) -> tuple[int, int, int, int]:
        area = self.board_size * self.board_size
        diamonds = max(NUM_DIAMONDS, int(area * NUM_DIAMONDS / (BOARD_SIZE * BOARD_SIZE) + 0.5))
        clues = max(NUM_CLUES, int(area * 0.05 + 0.5))
        traps = max(NUM_DEAD_ENDS + NUM_HIDEOUTS, int(area * 0.10 + 0.5))
        dead_ends = (traps + 1) // 2
        hideouts = traps // 2
        return diamonds, clues, dead_ends, hideouts

    # gera a mina sem item sob os jogadores
    def _create_board(
        self, occupied_positions: Optional[set[tuple[int, int]]] = None
    ) -> list[list[Tile]]:
        board = [
            [Tile(row=r, col=c) for c in range(self.board_size)]
            for r in range(self.board_size)
        ]
        occupied_starts = (
            set(self._starting_positions(self.number_players, self.board_size))
            if occupied_positions is None
            else set(occupied_positions)
        )
        available = [
            (r, c)
            for r in range(self.board_size)
            for c in range(self.board_size)
            if (r, c) not in occupied_starts
        ]

        diamond_count, clue_count, dead_end_count, hideout_count = (
            self._item_counts_for_current_mine()
        )
        item_specs: list[tuple[ItemType, Optional[int]]] = []
        item_specs.extend(
            (ItemType.DIAMOND, self.rng.randint(1, 10))
            for _ in range(diamond_count)
        )
        item_specs.extend((ItemType.CLUE, None) for _ in range(clue_count))
        item_specs.extend((ItemType.DEAD_END, None) for _ in range(dead_end_count))
        item_specs.extend((ItemType.HIDEOUT, None) for _ in range(hideout_count))
        # Exatamente uma passagem é criada em cada mina.
        item_specs.extend((ItemType.MAP_CHANGE, None) for _ in range(NUM_MAP_CHANGES))

        if len(item_specs) > len(available):
            raise RuntimeError("Não há casas suficientes para distribuir os itens.")

        for (row, col), (item, value) in zip(
            self.rng.sample(available, len(item_specs)), item_specs
        ):
            board[row][col].item = item
            board[row][col].diamond_value = value
        return board

    # cria outra mina mantendo os jogadores nas posições em que já estavam
    def _generate_next_mine(self, next_player_index: int) -> None:
        occupied_positions = {player.position for player in self.players}
        self.map_number += 1
        self.board_size = board_size_for_map(self.map_number)
        self.total_moves = action_limit_for_board(self.board_size)
        self.moves_per_player = self.total_moves // self.number_players
        self.board = self._create_board(occupied_positions)
        self.moves_played = 0
        self.finished = False
        self.winner_player_id = None
        self.latest_hint = None
        self.hinted_diamonds.clear()
        self.current_player_index = next_player_index % self.number_players

        for player in self.players:
            player.moves = 0
            tile = self.tile_at(player.position)
            tile.revealed = True
            tile.visited_by.add(player.player_id)

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    @property
    def remaining_moves(self) -> int:
        return self.total_moves - self.moves_played

    @property
    def ranking(self) -> list[Player]:
        return sorted(self.players, key=lambda player: (-player.score, player.player_id))

    @property
    def winners(self) -> list[Player]:
        if not self.finished:
            return []
        if self.winner_player_id is not None:
            return [self.players[self.winner_player_id]]
        highest_score = max(player.score for player in self.players)
        return [player for player in self.players if player.score == highest_score]

    def tile_at(self, position: tuple[int, int]) -> Tile:
        row, col = position
        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            raise IndexError("Coordenada fora do tabuleiro.")
        return self.board[row][col]

    # retorna os jogadores que ocupam a casa do jogador atual
    def players_on_current_tile(self, exclude_current: bool = True) -> list[Player]:
        current = self.current_player
        return [
            player for player in self.players
            if player.position == current.position
            and (not exclude_current or player.player_id != current.player_id)
        ]
    
    # jogadores que podem ser atacados
    def attack_targets(self) -> list[Player]:
        return self.players_on_current_tile(exclude_current=True)

    # jogadores em casas diferentes para que a troca de posição tenha efeito
    def tunnel_targets(self) -> list[Player]:
        current = self.current_player
        return [
            player for player in self.players
            if player.player_id != current.player_id
            and player.position != current.position
        ]

    def _invalid_result(self, player: Player, message: str, action: str = "invalid") -> MoveResult:
        return MoveResult(
            valid=False,
            consumed_turn=False,
            player_id=player.player_id,
            player_name=player.name,
            origin=player.position,
            destination=player.position,
            message=message,
            game_finished=self.finished,
            action=action,
        )

    # registra uma ação
    def _consume_turn(self) -> bool:
        acting_player = self.current_player
        acting_player.moves += 1
        self.moves_played += 1

        # A meta de 100 quilates encerra a partida imediatamente
        if acting_player.score >= WIN_SCORE:
            self.finished = True
            self.winner_player_id = acting_player.player_id
            return True

        self.finished = self.moves_played >= self.total_moves
        if not self.finished:
            self.current_player_index = (self.current_player_index + 1) % self.number_players
        return self.finished

    # move uma casa, revela o destino e resolve armadilhas automáticas
    def play_move(self, direction: str) -> MoveResult:
        player = self.current_player
        if self.finished:
            return self._invalid_result(player, "A partida já terminou.", "move")

        normalized = direction.strip().lower()
        if normalized not in DIRECTIONS:
            return self._invalid_result(player, "Direção inválida. Use W, A, S ou D.", "move")

        dr, dc = DIRECTIONS[normalized]
        old_row, old_col = player.position
        destination = (old_row + dr, old_col + dc)
        new_row, new_col = destination
        if not (0 <= new_row < self.board_size and 0 <= new_col < self.board_size):
            return self._invalid_result(
                player,
                "Movimento fora da mina. Escolha uma casa adjacente válida.",
                "move",
            )

        origin = player.position
        player_index = self.current_player_index
        tile = self.board[new_row][new_col]
        player.position = destination
        tile.revealed = True
        tile.visited_by.add(player.player_id)

        # O túnel sem saída é uma armadilha automática: a penalidade acontece na chegada e a casa não pode ser minerada novamente.
        if tile.item == ItemType.DEAD_END and not tile.activated:
            tile.activated = True
            player.score -= 10
            finished = self._consume_turn()
            return MoveResult(
                valid=True,
                consumed_turn=True,
                player_id=player.player_id,
                player_name=player.name,
                origin=origin,
                destination=destination,
                event=ItemType.DEAD_END,
                points_delta=-10,
                message=f"Túnel sem saída! {player.name} perdeu 10 quilates imediatamente ao entrar.",
                game_finished=finished,
                action="dead_end",
            )

        # A passagem para outra mina também é automática.
        if tile.item == ItemType.MAP_CHANGE:
            next_player_index = (player_index + 1) % self.number_players
            self._generate_next_mine(next_player_index)
            return MoveResult(
                valid=True,
                consumed_turn=True,
                player_id=player.player_id,
                player_name=player.name,
                origin=origin,
                destination=destination,
                event=ItemType.MAP_CHANGE,
                message=(
                    f"{player.name} encontrou uma passagem! A Mina {self.map_number} foi descoberta. "
                    f"O tabuleiro agora tem {self.board_size}x{self.board_size} casas e "
                    f"{self.total_moves} acoes; pontos, inventarios e posicoes foram preservados."
                ),
                game_finished=False,
                action="map_change",
            )

        finished = self._consume_turn()
        if tile.item == ItemType.EMPTY:
            message = f"{player.name} chegou a uma casa vazia. A vez terminou."
            event = None
        elif tile.activated:
            message = f"{player.name} chegou a uma casa já explorada ({tile.item.value})."
            event = tile.item
        else:
            message = (
                f"{player.name} revelou: {tile.item.value}. "
                "No próximo turno, pode minerar/usar o item ou seguir para outra casa."
            )
            event = tile.item

        return MoveResult(
            valid=True,
            consumed_turn=True,
            player_id=player.player_id,
            player_name=player.name,
            origin=origin,
            destination=destination,
            event=event,
            message=message,
            game_finished=finished,
            action="move",
        )

    #gera uma dica para um diamante não coletado
    def _make_clue_hint(self, player: Player) -> str:
        candidates = [
            (tile.row, tile.col)
            for row in self.board
            for tile in row
            if tile.item == ItemType.DIAMOND
            and tile.collected_by is None
            and not tile.activated
        ]
        if not candidates:
            hint = "A mina nao tem mais diamantes disponiveis."
            self.latest_hint = "Sem diamantes restantes nesta mina."
            return hint

        not_yet_hinted = [
            position for position in candidates
            if position not in self.hinted_diamonds
        ]
        target = self.rng.choice(not_yet_hinted or candidates)
        self.hinted_diamonds.add(target)

        delta_row = target[0] - player.position[0]
        delta_col = target[1] - player.position[1]
        if delta_row < 0 and delta_col == 0:
            direction = "ao norte"
        elif delta_row > 0 and delta_col == 0:
            direction = "ao sul"
        elif delta_row == 0 and delta_col > 0:
            direction = "a leste"
        elif delta_row == 0 and delta_col < 0:
            direction = "a oeste"
        elif delta_row < 0 and delta_col > 0:
            direction = "a nordeste"
        elif delta_row < 0 and delta_col < 0:
            direction = "a noroeste"
        elif delta_row > 0 and delta_col > 0:
            direction = "a sudeste"
        else:
            direction = "a sudoeste"

        # Como o jogador só pode mover na horizontal/vertical, a distância Manhattan representa a quantidade mínima de movimentos até o alvo. -> serve para a dica
        distance = abs(delta_row) + abs(delta_col)
        hint = f"Ha um diamante {direction}, a {distance} movimentos daqui."
        self.latest_hint = f"Diamante {direction}, {distance} mov."
        return hint

    # minera a casa atual
    def mine_current_tile(self) -> MoveResult:
        player = self.current_player
        tile = self.tile_at(player.position)

        if self.finished:
            return self._invalid_result(player, "A partida já terminou.", "mine")
        if not tile.revealed:
            return self._invalid_result(player, "Esta casa ainda não foi revelada.", "mine")
        if tile.item == ItemType.EMPTY:
            return self._invalid_result(player, "Esta casa não contém nada para minerar.", "mine")
        if tile.item == ItemType.DEAD_END:
            return self._invalid_result(player, "O túnel sem saída já aplica sua penalidade automaticamente na chegada.", "mine")
        if tile.item == ItemType.MAP_CHANGE:
            return self._invalid_result(player, "A passagem para outra mina é ativada automaticamente na chegada.", "mine")
        if tile.activated:
            return self._invalid_result(player, "Este item já foi utilizado.", "mine")
        if tile.item == ItemType.HIDEOUT:
            return MoveResult(
                valid=True,
                consumed_turn=False,
                player_id=player.player_id,
                player_name=player.name,
                origin=player.position,
                destination=player.position,
                event=ItemType.HIDEOUT,
                message="Escolha um jogador para trocar de posição. Cancele para não usar o túnel.",
                game_finished=False,
                action="mine",
                requires_target=True,
            )

        points_delta = 0
        if tile.item == ItemType.DIAMOND:
            value = int(tile.diamond_value or 0)
            points_delta = value
            player.score += value
            player.diamonds.append(value)
            tile.collected_by = player.player_id
            message = f"{player.name} minerou um diamante de {value} quilate(s)! +{value}."
        elif tile.item == ItemType.CLUE:
            points_delta = 0
            hint = self._make_clue_hint(player)
            message = f"{player.name} encontrou uma pista! {hint}"
        else:
            return self._invalid_result(player, "Não há nada para minerar nesta casa.", "mine")

        tile.activated = True
        finished = self._consume_turn()
        return MoveResult(
            valid=True,
            consumed_turn=True,
            player_id=player.player_id,
            player_name=player.name,
            origin=player.position,
            destination=player.position,
            event=tile.item,
            points_delta=points_delta,
            message=message,
            game_finished=finished,
            action="mine",
        )

    # usa o tunel secreto e troca de posições
    def use_secret_tunnel(self, target_player_id: int) -> MoveResult:
        player = self.current_player
        tile = self.tile_at(player.position)
        if self.finished:
            return self._invalid_result(player, "A partida já terminou.", "tunnel")
        if tile.item != ItemType.HIDEOUT or not tile.revealed or tile.activated:
            return self._invalid_result(player, "Não há túnel secreto disponível nesta casa.", "tunnel")
        if target_player_id == player.player_id or not (0 <= target_player_id < self.number_players):
            return self._invalid_result(player, "Jogador escolhido inválido.", "tunnel")

        target = self.players[target_player_id]
        origin = player.position
        target_origin = target.position

        player.position, target.position = target_origin, origin
        tile.activated = True

        # player chega na casa trocada
        arrivals = (
            (player, self.tile_at(player.position)),
            (target, self.tile_at(target.position)),
        )
        points_delta = 0
        opponent_deltas: dict[int, int] = {}
        arrival_messages: list[str] = []
        map_change_found = False

        for arriving_player, destination_tile in arrivals:
            destination_tile.revealed = True
            destination_tile.visited_by.add(arriving_player.player_id)

            if destination_tile.item == ItemType.DEAD_END and not destination_tile.activated:
                destination_tile.activated = True
                arriving_player.score -= 10
                if arriving_player.player_id == player.player_id:
                    points_delta -= 10
                else:
                    opponent_deltas[arriving_player.player_id] = -10
                arrival_messages.append(
                    f"{arriving_player.name} caiu em um túnel sem saída e perdeu 10 quilates."
                )
            elif destination_tile.item == ItemType.MAP_CHANGE:
                map_change_found = True

        next_player_index = (player.player_id + 1) % self.number_players
        if map_change_found:
            self._generate_next_mine(next_player_index)
            return MoveResult(
                valid=True,
                consumed_turn=True,
                player_id=player.player_id,
                player_name=player.name,
                origin=origin,
                destination=player.position,
                event=ItemType.MAP_CHANGE,
                points_delta=points_delta,
                opponent_deltas=opponent_deltas,
                message=(
                    f"{player.name} usou o túnel secreto e a troca revelou a passagem para outra mina! "
                    f"A Mina {self.map_number} começou; posições, pontuações e inventários foram preservados."
                ),
                game_finished=False,
                action="map_change",
                target_player_id=target.player_id,
                swapped_player_id=target.player_id,
                swapped_origin=target_origin,
                swapped_destination=target.position,
            )

        finished = self._consume_turn()
        message = f"{player.name} usou o túnel secreto e trocou de posição com {target.name}!"
        if arrival_messages:
            message += " " + " ".join(arrival_messages)
        return MoveResult(
            valid=True,
            consumed_turn=True,
            player_id=player.player_id,
            player_name=player.name,
            origin=origin,
            destination=player.position,
            event=ItemType.HIDEOUT,
            points_delta=points_delta,
            opponent_deltas=opponent_deltas,
            message=message,
            game_finished=finished,
            action="tunnel",
            target_player_id=target.player_id,
            swapped_player_id=target.player_id,
            swapped_origin=target_origin,
            swapped_destination=target.position,
        )

    # para decidir para qual casa o jogador que apanhou vai ser lançado
    def _random_adjacent_destination(
        self,
        origin: tuple[int, int],
        moving_player_id: int,
    ) -> tuple[int, int]:
        row, col = origin
        adjacent = []
        for delta_row, delta_col in DIRECTIONS.values():
            candidate = (row + delta_row, col + delta_col)
            if 0 <= candidate[0] < self.board_size and 0 <= candidate[1] < self.board_size:
                adjacent.append(candidate)

        if not adjacent:
            raise RuntimeError("Não existe casa adjacente válida para deslocar o jogador.")

        occupied_by_others = {
            other.position
            for other in self.players
            if other.player_id != moving_player_id
        }
        free = [position for position in adjacent if position not in occupied_by_others]
        return self.rng.choice(free or adjacent)

    # ataca alguém na mesma casa
    def attack(self, target_player_id: int) -> MoveResult:
        player = self.current_player
        if self.finished:
            return self._invalid_result(player, "A partida já terminou.", "attack")
        if target_player_id == player.player_id or not (0 <= target_player_id < self.number_players):
            return self._invalid_result(player, "Jogador escolhido inválido.", "attack")

        target = self.players[target_player_id]
        if target.position != player.position:
            return self._invalid_result(
                player,
                f"{target.name} não está na mesma casa. Só é possível atacar jogadores junto de você.",
                "attack",
            )

        attack_position = player.position
        knockback_origin = target.position
        knockback_destination = self._random_adjacent_destination(
            knockback_origin,
            moving_player_id=target.player_id,
        )

        stolen_value = None
        points_delta = 0
        opponent_deltas: dict[int, int] = {}
        if target.diamonds:
            diamond_index = self.rng.randrange(len(target.diamonds))
            stolen_value = target.diamonds.pop(diamond_index)
            target.score -= stolen_value
            player.diamonds.append(stolen_value)
            player.score += stolen_value
            points_delta = stolen_value
            opponent_deltas[target.player_id] = -stolen_value
            message = (
                f"{player.name} atacou {target.name} e roubou um diamante "
                f"de {stolen_value} quilate(s)!"
            )
        else:
            message = f"{player.name} atacou {target.name}, mas não havia diamantes para roubar."

        # O alvo é empurrado uma casa. Essa movimentação não é uma ação extra.
        target.position = knockback_destination
        arrival_tile = self.tile_at(knockback_destination)
        arrival_tile.revealed = True
        arrival_tile.visited_by.add(target.player_id)
        knockback_event = arrival_tile.item

        arrival_message = (
            f"{target.name} foi empurrado para a casa "
            f"({knockback_destination[0] + 1}, {knockback_destination[1] + 1})."
        )

        if arrival_tile.item == ItemType.DEAD_END and not arrival_tile.activated:
            arrival_tile.activated = True
            target.score -= 10
            opponent_deltas[target.player_id] = opponent_deltas.get(target.player_id, 0) - 10
            arrival_message += f" Túnel sem saída: {target.name} perdeu mais 10 quilates."
        elif arrival_tile.item == ItemType.MAP_CHANGE:
            arrival_message += " O empurrão revelou a passagem para outra mina!"
        elif arrival_tile.item != ItemType.EMPTY:
            arrival_message += f" O item {arrival_tile.item.value} foi revelado."

        acting_player_index = self.current_player_index
        next_player_index = (acting_player_index + 1) % self.number_players
        finished = self._consume_turn()

        if finished and self.winner_player_id is not None:
            message += " " + arrival_message
            message += f" {player.name} alcançou {WIN_SCORE} quilates e venceu!"
            return MoveResult(
                valid=True,
                consumed_turn=True,
                player_id=player.player_id,
                player_name=player.name,
                origin=attack_position,
                destination=attack_position,
                event=knockback_event,
                points_delta=points_delta,
                opponent_deltas=opponent_deltas,
                message=message,
                game_finished=True,
                action="attack",
                target_player_id=target.player_id,
                stolen_diamond=stolen_value,
                knocked_back_player_id=target.player_id,
                knockback_origin=knockback_origin,
                knockback_destination=knockback_destination,
                knockback_event=knockback_event,
            )

        if knockback_event == ItemType.MAP_CHANGE:
            self._generate_next_mine(next_player_index)
            message += " " + arrival_message
            message += (
                f" A Mina {self.map_number} começou; posições, pontuações e inventários foram preservados."
            )
            action = "attack_map_change"
            finished = False
        else:
            message += " " + arrival_message
            action = "attack"

        return MoveResult(
            valid=True,
            consumed_turn=True,
            player_id=player.player_id,
            player_name=player.name,
            origin=attack_position,
            destination=attack_position,
            event=knockback_event,
            points_delta=points_delta,
            opponent_deltas=opponent_deltas,
            message=message,
            game_finished=finished,
            action=action,
            target_player_id=target.player_id,
            stolen_diamond=stolen_value,
            knocked_back_player_id=target.player_id,
            knockback_origin=knockback_origin,
            knockback_destination=knockback_destination,
            knockback_event=knockback_event,
        )

    def summary(self) -> dict:
        return {
            "map_number": self.map_number,
            "board_size": self.board_size,
            "total_moves": self.total_moves,
            "moves_played": self.moves_played,
            "remaining_moves": self.remaining_moves,
            "win_score": WIN_SCORE,
            "latest_hint": self.latest_hint,
            "current_player": None if self.finished else self.current_player.name,
            "finished": self.finished,
            "ranking": [
                {
                    "player_id": player.player_id,
                    "name": player.name,
                    "score": player.score,
                    "moves": player.moves,
                    "diamonds": list(player.diamonds),
                    "position": player.position,
                }
                for player in self.ranking
            ],
        }
