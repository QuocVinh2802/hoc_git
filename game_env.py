from typing import List, Tuple, Dict, Any, Optional
from state import State, Orientation


# Quy ước mã ô trên bàn cờ (Grid Tile Codes):
# 0: Ô trống / Vực thẳm (Void)
# 1: Ô sàn bình thường (Normal Floor)
# 2: Ô dễ vỡ / Màu cam (Fragile Tile - cấm đứng thẳng)
# 3: Lỗ đích (Goal Hole)
# 4: Công tắc nhẹ (Soft Switch - hình tròn O, đè bất kỳ phần nào cũng kích hoạt)
# 5: Công tắc nặng (Heavy Switch - hình chữ X, phải đứng thẳng mới kích hoạt)
# 6: Công tắc phân tách (Split Switch - hình (), đứng thẳng sẽ tách khối 1x1x2 thành hai khối 1x1x1)
# 7: Ô cầu (Bridge Tile - trạng thái đóng/mở phụ thuộc vào bridges_status trong State)


class GameEnv:
    def __init__(self, level_data: Dict[str, Any]) -> None:
        """
        Khởi tạo bàn cờ từ dữ liệu màn chơi (level_data).
        Lưu trữ các dữ liệu tĩnh như: lưới ô, vị trí xuất phát, ô đích, cầu, công tắc...
        """
        self.level_id: int = level_data.get("id", 1)
        self.name: str = level_data.get("name", f"Level {self.level_id}")
        self.difficulty: str = level_data.get("difficulty", "Easy")
        self.description: str = level_data.get("description", "")

        self.grid: List[List[int]] = level_data.get("grid", [])
        self.rows: int = len(self.grid)
        self.cols: int = len(self.grid[0]) if self.rows > 0 else 0

        self.start_pos: Tuple[int, int] = tuple(level_data.get("start_pos", (0, 0)))
        self.goal_pos: Tuple[int, int] = tuple(level_data.get("goal_pos", (0, 0)))

        # Danh sách cầu: mỗi cầu có {"id": int, "positions": [(r, c), ...], "initial_open": bool}
        self.bridges_cfg: List[Dict[str, Any]] = level_data.get("bridges", [])
        self.pos_to_bridge_idx: Dict[Tuple[int, int], int] = {}
        initial_bridges: List[bool] = []

        for idx, b in enumerate(self.bridges_cfg):
            initial_bridges.append(bool(b.get("initial_open", False)))
            for pos in b.get("positions", []):
                self.pos_to_bridge_idx[(pos[0], pos[1])] = idx

        self.initial_bridges_status: Tuple[bool, ...] = tuple(initial_bridges)

        # Danh sách công tắc:
        # - Soft/Heavy switch: {"pos": (r, c), "type": "soft"|"heavy", "targets": [bridge_idx, ...], "behavior": "toggle"|"open"|"close"}
        # - Split switch: {"pos": (r, c), "type": "split", "spawn_positions": [(r1, c1), (r2, c2)]}
        self.switches_cfg: List[Dict[str, Any]] = level_data.get("switches", [])
        self.pos_to_switch: Dict[Tuple[int, int], Dict[str, Any]] = {}
        for sw in self.switches_cfg:
            pos = (sw["pos"][0], sw["pos"][1])
            self.pos_to_switch[pos] = sw

    def get_initial_state(self) -> State:
        """Trả về trạng thái bắt đầu của màn chơi."""
        return State(
            block_positions=(self.start_pos,),
            orientation=Orientation.STANDING,
            bridges_status=self.initial_bridges_status,
            active_split_index=0
        )

    def is_goal(self, state: State) -> bool:
        """Kiểm tra xem trạng thái hiện tại đã chiến thắng chưa (khối đứng thẳng trên ô đích)."""
        return (
            state.orientation == Orientation.STANDING
            and len(state.block_positions) == 1
            and state.block_positions[0] == self.goal_pos
        )

    def get_tile(self, r: int, c: int) -> int:
        """Lấy mã loại ô tại tọa độ (r, c). Nếu ngoài biên trả về 0 (Void)."""
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return self.grid[r][c]
        return 0

    def is_tile_walkable(self, r: int, c: int, bridges_status: Tuple[bool, ...]) -> bool:
        """Kiểm tra một ô đơn lẻ (r, c) có sàn đỡ hay không."""
        tile = self.get_tile(r, c)
        if tile == 0:
            return False
        if (r, c) in self.pos_to_bridge_idx:
            b_idx = self.pos_to_bridge_idx[(r, c)]
            return bridges_status[b_idx]
        if tile == 7:
            # Nếu được đánh dấu là ô cầu nhưng không tìm thấy trong cấu hình cầu -> coi như đóng
            return False
        return True

    def is_valid_state(self, state: State) -> bool:
        """
        Kiểm tra xem trạng thái lý thuyết có hợp lệ trên bàn cờ hay không:
        1. Không rơi ra ngoài biên hoặc rơi vào ô trống (Void) / cầu đang đóng.
        2. Không đứng thẳng (STANDING) trên ô dễ vỡ (Fragile tile = 2).
        """
        for r, c in state.block_positions:
            if not self.is_tile_walkable(r, c, state.bridges_status):
                return False

        # Kiểm tra luật ô dễ vỡ (Fragile tile - mã 2): chỉ sập khi khối 1x1x2 đứng thẳng
        if state.orientation == Orientation.STANDING:
            r, c = state.block_positions[0]
            if self.get_tile(r, c) == 2:
                return False

        return True

    def get_theoretical_move(self, state: State, move: str) -> Optional[State]:
        """
        Tính toán vị trí và hướng mới của khối hộp thuần túy về mặt hình học
        (chưa kiểm tra ô sàn đỡ hay công tắc).
        """
        move = move.upper()
        if move in ("SPACE", "SWITCH_BLOCK"):
            if state.orientation != Orientation.SPLIT:
                return None
            new_idx = 1 - state.active_split_index
            return State(
                block_positions=state.block_positions,
                orientation=Orientation.SPLIT,
                bridges_status=state.bridges_status,
                active_split_index=new_idx,
            )

        if move not in ("UP", "DOWN", "LEFT", "RIGHT"):
            return None

        dr, dc = {
            "UP": (-1, 0),
            "DOWN": (1, 0),
            "LEFT": (0, -1),
            "RIGHT": (0, 1),
        }[move]

        ori = state.orientation

        if ori == Orientation.STANDING:
            r, c = state.block_positions[0]
            if move == "UP":
                new_pos = ((r - 2, c), (r - 1, c))
                new_ori = Orientation.LYING_VERTICAL
            elif move == "DOWN":
                new_pos = ((r + 1, c), (r + 2, c))
                new_ori = Orientation.LYING_VERTICAL
            elif move == "LEFT":
                new_pos = ((r, c - 2), (r, c - 1))
                new_ori = Orientation.LYING_HORIZONTAL
            else:  # RIGHT
                new_pos = ((r, c + 1), (r, c + 2))
                new_ori = Orientation.LYING_HORIZONTAL
            return State(new_pos, new_ori, state.bridges_status, 0)

        elif ori == Orientation.LYING_HORIZONTAL:
            (r, c1), (_, c2) = state.block_positions
            if move == "LEFT":
                new_pos = ((r, c1 - 1),)
                new_ori = Orientation.STANDING
            elif move == "RIGHT":
                new_pos = ((r, c2 + 1),)
                new_ori = Orientation.STANDING
            elif move == "UP":
                new_pos = ((r - 1, c1), (r - 1, c2))
                new_ori = Orientation.LYING_HORIZONTAL
            else:  # DOWN
                new_pos = ((r + 1, c1), (r + 1, c2))
                new_ori = Orientation.LYING_HORIZONTAL
            return State(new_pos, new_ori, state.bridges_status, 0)

        elif ori == Orientation.LYING_VERTICAL:
            (r1, c), (r2, _) = state.block_positions
            if move == "UP":
                new_pos = ((r1 - 1, c),)
                new_ori = Orientation.STANDING
            elif move == "DOWN":
                new_pos = ((r2 + 1, c),)
                new_ori = Orientation.STANDING
            elif move == "LEFT":
                new_pos = ((r1, c - 1), (r2, c - 1))
                new_ori = Orientation.LYING_VERTICAL
            else:  # RIGHT
                new_pos = ((r1, c + 1), (r2, c + 1))
                new_ori = Orientation.LYING_VERTICAL
            return State(new_pos, new_ori, state.bridges_status, 0)

        elif ori == Orientation.SPLIT:
            idx = state.active_split_index
            pos_list = list(state.block_positions)
            r, c = pos_list[idx]
            nr, nc = r + dr, c + dc
            pos_list[idx] = (nr, nc)

            # Kiểm tra hai khối nhỏ có nằm cạnh nhau để hợp nhất lại không
            (rA, cA), (rB, cB) = pos_list[0], pos_list[1]
            if rA == rB and abs(cA - cB) == 1:
                merged_pos = tuple(sorted([pos_list[0], pos_list[1]]))
                return State(merged_pos, Orientation.LYING_HORIZONTAL, state.bridges_status, 0)
            elif cA == cB and abs(rA - rB) == 1:
                merged_pos = tuple(sorted([pos_list[0], pos_list[1]]))
                return State(merged_pos, Orientation.LYING_VERTICAL, state.bridges_status, 0)
            else:
                return State(
                    (pos_list[0], pos_list[1]),
                    Orientation.SPLIT,
                    state.bridges_status,
                    idx,
                )

        return None

    def apply_move(self, state: State, move: str) -> Optional[State]:
        """
        Áp dụng một hành động ('UP', 'DOWN', 'LEFT', 'RIGHT', hoặc 'SPACE') lên trạng thái hiện tại.
        Trả về State mới nếu hợp lệ, hoặc None nếu nước đi bất hợp lệ (rơi xuống vực, sập ô cam...).
        """
        move = move.upper()
        if move in ("SPACE", "SWITCH_BLOCK"):
            return self.get_theoretical_move(state, move)

        old_positions = set(state.block_positions)
        theoretical_state = self.get_theoretical_move(state, move)
        if theoretical_state is None:
            return None

        # 2. Kiểm tra tính hợp lệ trên mặt sàn hiện tại
        if not self.is_valid_state(theoretical_state):
            return None

        # 3. Kích hoạt công tắc (Switches) nếu có
        final_state = self._trigger_switches(old_positions, theoretical_state)

        # Kiểm tra lại lần nữa phòng trường hợp cầu vừa đóng ngay dưới chân khối
        if not self.is_valid_state(final_state):
            return None

        return final_state

    def _trigger_switches(self, old_positions: set, state: State) -> State:
        """Kiểm tra và xử lý các công tắc mà khối hộp vừa chạm vào."""
        bridges = list(state.bridges_status)
        block_positions = state.block_positions
        orientation = state.orientation
        active_idx = state.active_split_index

        # Những ô mới mà khối hộp vừa đặt chân tới trong lượt lăn này
        newly_entered = [pos for pos in block_positions if pos not in old_positions]

        for pos in newly_entered:
            if pos not in self.pos_to_switch:
                continue
            sw = self.pos_to_switch[pos]
            sw_type = sw.get("type", "soft")

            if sw_type == "soft":
                # Công tắc nhẹ (O): bất kỳ phần nào đè lên cũng kích hoạt
                self._apply_bridge_switch(bridges, sw)

            elif sw_type == "heavy":
                # Công tắc nặng (X): chỉ kích hoạt khi khối 1x1x2 đứng thẳng trên đó
                if orientation == Orientation.STANDING:
                    self._apply_bridge_switch(bridges, sw)

            elif sw_type == "split":
                # Công tắc phân tách (): chỉ kích hoạt khi khối 1x1x2 đứng thẳng trên đó
                if orientation == Orientation.STANDING:
                    spawns = sw.get("spawn_positions", [])
                    if len(spawns) == 2:
                        p1 = (spawns[0][0], spawns[0][1])
                        p2 = (spawns[1][0], spawns[1][1])
                        block_positions = (p1, p2)
                        orientation = Orientation.SPLIT
                        active_idx = 0
                        # Kiểm tra nếu 2 vị trí dịch chuyển đè lên công tắc nhẹ (soft switch)
                        for sp in (p1, p2):
                            if sp in self.pos_to_switch and self.pos_to_switch[sp].get("type") == "soft":
                                self._apply_bridge_switch(bridges, self.pos_to_switch[sp])

        return State(
            block_positions=block_positions,
            orientation=orientation,
            bridges_status=tuple(bridges),
            active_split_index=active_idx
        )

    @staticmethod
    def _apply_bridge_switch(bridges: List[bool], sw: Dict[str, Any]) -> None:
        """Cập nhật danh sách trạng thái cầu theo hành vi của công tắc (toggle / open / close)."""
        behavior = sw.get("behavior", "toggle")
        for b_idx in sw.get("targets", []):
            if 0 <= b_idx < len(bridges):
                if behavior == "toggle":
                    bridges[b_idx] = not bridges[b_idx]
                elif behavior == "open":
                    bridges[b_idx] = True
                elif behavior == "close":
                    bridges[b_idx] = False

    def get_step_cost(self, current_state: State, action: str, next_state: State) -> float:
        """
        Hàm chi phí bước đi gợi ý cho thuật toán UCS và A*:
        - Đổi khối điều khiển (SPACE): 0.5
        - Lăn qua ô dễ vỡ (Fragile tile): 2.0 (rủi ro cao hơn)
        - Lăn bình thường: 1.0
        """
        if action in ("SPACE", "SWITCH_BLOCK"):
            return 0.5
        for r, c in next_state.block_positions:
            if self.get_tile(r, c) == 2:
                return 2.0
        return 1.0

    def get_successors(self, state: State) -> List[Tuple[str, State]]:
        """
        Hàm quan trọng nhất dành cho 4 người làm thuật toán (BFS, DFS, UCS, A*).
        Sinh ra danh sách [(action, next_state), ...] hợp lệ từ trạng thái hiện tại.
        """
        successors: List[Tuple[str, State]] = []
        moves = ["UP", "DOWN", "LEFT", "RIGHT"]
        if state.orientation == Orientation.SPLIT:
            moves.append("SPACE")

        for move in moves:
            next_state = self.apply_move(state, move)
            if next_state is not None:
                successors.append((move, next_state))

        return successors