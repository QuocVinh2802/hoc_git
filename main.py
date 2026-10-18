from typing import List, Dict, Tuple, Optional
import math
from ursina import (
    Ursina,
    Entity,
    Text,
    Button,
    camera,
    color,
    window,
    Vec3,
    invoke,
    destroy,
    application,
    time as utime,
)

from state import State, Orientation
from game_env import GameEnv
from levels import LEVELS, get_level, export_levels_to_json
from solvers import BFSSolver, DFSSolver, UCSSolver, AStarSolver


# =============================================================================
# HIGH-CONTRAST 3D COLOR PALETTE
# =============================================================================
COLOR_BG = color.rgb32(15, 23, 42)              # Deep Space Navy

# Safe tiles (Checkerboard)
COLOR_FLOOR_A = color.rgb32(226, 232, 240)      # Platinum White
COLOR_FLOOR_B = color.rgb32(186, 198, 216)      # Slate Silver
COLOR_BORDER = color.rgb32(51, 65, 85)          # Dark Slate Bevel

# Fragile tiles (Orange warning)
COLOR_FRAGILE = color.rgb32(249, 115, 22)        # Vivid Orange
COLOR_FRAGILE_INNER = color.rgb32(194, 65, 12)  # Warning Amber

# Goal Hole
COLOR_GOAL_RIM = color.rgb32(234, 179, 8)       # Golden Glow Rim
COLOR_GOAL_HOLE = color.rgb32(5, 5, 10)         # Abyss Core

# Bridge tiles
COLOR_BRIDGE_OPEN = color.rgb32(16, 185, 129)   # Emerald Green
COLOR_BRIDGE_BORDER = color.rgb32(5, 150, 105)
COLOR_BRIDGE_CLOSED = color.rgba32(239, 68, 68, 80)

# Player Block
COLOR_BLOCK_MAIN = color.rgb32(225, 29, 72)     # Crimson Red
COLOR_BLOCK_ACTIVE = color.rgb32(244, 63, 94)   # Rose Red (Active split piece)
COLOR_BLOCK_INACTIVE = color.rgb32(136, 19, 55) # Dark Rose (Inactive split piece)

# Switches
COLOR_SW_SOFT = color.rgb32(14, 165, 233)       # Sky Blue (Circle)
COLOR_SW_HEAVY = color.rgb32(250, 204, 21)      # Lemon Yellow (X)
COLOR_SW_SPLIT = color.rgb32(168, 85, 247)      # Bright Purple (())


class BloxorzUrsinaApp:
    def __init__(self) -> None:
        self.current_level_idx: int = 0
        self.env: Optional[GameEnv] = None
        self.state: Optional[State] = None

        self.move_count: int = 0
        self.is_animating: bool = False
        self.game_over: bool = False
        self.auto_play_queue: List[str] = []

        # Physics & Rolling Animation State
        self.is_rolling: bool = False
        self.roll_elapsed: float = 0.0
        self.roll_duration: float = 0.22        # 220ms natural flip time
        self.roll_pivot: Optional[Entity] = None
        self.roll_axis: str = "z"
        self.roll_target_deg: float = 0.0
        self.is_invalid_roll: bool = False
        self.pending_fall_mode: Optional[str] = None
        self.pending_fall_move: str = "UP"

        # Gravity Fall Simulation State
        self.is_falling: bool = False
        self.fall_time: float = 0.0
        self.fall_duration: float = 1.2
        self.fall_positions: List[Vec3] = []
        self.fall_velocities: List[Vec3] = []
        self.fall_rotations: List[Vec3] = []
        self.fall_rot_speeds: List[Vec3] = []

        # 3D Board Entities
        self.board_root = Entity()
        self.tile_entities: List[Entity] = []
        self.bridge_entities: Dict[Tuple[int, int], Tuple[Entity, Entity]] = {}
        self.block_entities: List[Entity] = []
        self.active_marker: Optional[Entity] = None

        self._setup_ui()
        self.load_level(0)

    def _setup_ui(self) -> None:
        """Create compact, modern English UI with cleanly organized screen space."""
        # Top-Left: Game Title, Stage Info & Step Counter
        self.title_text = Text(
            text="BLOXORZ 3D",
            position=(-0.8, 0.47),
            scale=1.2,
            color=color.rgb32(250, 204, 21),
        )
        self.diff_text = Text(
            text="",
            position=(-0.8, 0.43),
            scale=0.85,
            color=color.rgb32(56, 189, 248),
        )
        self.status_text = Text(
            text="Steps: 0 | STANDING",
            position=(-0.8, 0.39),
            scale=0.85,
            color=color.white,
        )

        # Center-Top: Notification Banner
        self.banner_text = Text(
            text="",
            origin=(0, 0),
            position=(-0.05, 0.44),
            scale=1.05,
            color=color.rgb32(74, 222, 128),
        )

        # Bottom-Left: Compact Controls & Tile Legend
        legend_content = (
            "CONTROLS: WASD / Arrow Keys: Roll | SPACE: Switch piece | R: Restart\n"
            "TILES: Gray: Floor | Orange: Fragile (No standing!) | Hole: Goal\n"
            "Green: Bridge | Blue (O): Soft Switch | Yellow (X): Heavy Switch | Purple: Split"
        )
        self.legend_text = Text(
            text=legend_content,
            position=(-0.8, -0.42),
            scale=0.68,
            color=color.rgb32(203, 213, 225),
        )

        # Top-Right: Level Navigation & Restart Buttons
        Button(
            text="< Prev",
            position=(0.63, 0.45),
            scale=(0.11, 0.04),
            color=color.rgb32(51, 65, 85),
            highlight_color=color.rgb32(71, 85, 105),
            on_click=self.prev_level,
        )
        Button(
            text="Next >",
            position=(0.76, 0.45),
            scale=(0.11, 0.04),
            color=color.rgb32(51, 65, 85),
            highlight_color=color.rgb32(71, 85, 105),
            on_click=self.next_level,
        )
        Button(
            text="Restart (R)",
            position=(0.695, 0.395),
            scale=(0.24, 0.04),
            color=color.rgb32(185, 28, 28),
            highlight_color=color.rgb32(220, 38, 38),
            on_click=self.restart_level,
        )

        # Middle-Right: Level Selector Grid (1 - 15)
        Text(
            text="SELECT LEVEL (1 - 15):",
            position=(0.57, 0.34),
            scale=0.75,
            color=color.rgb32(250, 204, 21),
        )
        self.level_buttons: List[Button] = []
        for i in range(15):
            r_idx = i // 5
            c_idx = i % 5
            bx = 0.585 + c_idx * 0.055
            by = 0.30 - r_idx * 0.045
            btn = Button(
                text=str(i + 1),
                position=(bx, by),
                scale=(0.048, 0.038),
                color=color.rgb32(30, 41, 59),
                highlight_color=color.rgb32(71, 85, 105),
                on_click=lambda idx=i: self.load_level(idx),
            )
            self.level_buttons.append(btn)

        # Bottom-Right: AI Solvers Controls
        Text(
            text="AI SOLVERS:",
            position=(0.57, 0.14),
            scale=0.75,
            color=color.rgb32(56, 189, 248),
        )
        solvers_ui = [
            ("Solve with BFS", "BFS", color.rgb32(5, 150, 105)),
            ("Solve with DFS", "DFS", color.rgb32(2, 132, 199)),
            ("Solve with UCS", "UCS", color.rgb32(217, 119, 6)),
            ("Solve with A*", "ASTAR", color.rgb32(147, 51, 234)),
        ]
        for idx, (label, s_type, btn_col) in enumerate(solvers_ui):
            Button(
                text=label,
                position=(0.695, 0.09 - idx * 0.045),
                scale=(0.24, 0.038),
                color=btn_col,
                on_click=lambda st=s_type: self.run_solver(st),
            )

        self.solver_metrics_text = Text(
            text="Solver Metrics:\n(Idle)",
            position=(0.57, -0.13),
            scale=0.70,
            color=color.rgb32(203, 213, 225),
        )

    def GridToWorld(self, r: float, c: float, y: float = 0.0) -> Vec3:
        """Convert 2D grid coordinates (row, col) to Ursina 3D Vector (x, y, z)."""
        return Vec3(c, y, -r)

    def load_level(self, idx: int) -> None:
        """Load stage index (0-14) and rebuild the 3D board scene."""
        self.current_level_idx = max(0, min(idx, len(LEVELS) - 1))
        lvl_data = get_level(self.current_level_idx)

        self.env = GameEnv(lvl_data)
        self.state = self.env.get_initial_state()
        self.move_count = 0
        self.is_animating = False
        self.is_rolling = False
        self.is_falling = False
        self.game_over = False
        self.auto_play_queue.clear()

        # Update level button highlights
        for i, btn in enumerate(self.level_buttons):
            if i == self.current_level_idx:
                btn.color = color.rgb32(234, 179, 8)
                btn.text_entity.color = color.black
            else:
                btn.color = color.rgb32(30, 41, 59)
                btn.text_entity.color = color.white

        # Update HUD Texts (English)
        self.title_text.text = f"LEVEL {lvl_data['id']}/15: {lvl_data.get('name', '')}"
        diff_name = lvl_data.get("difficulty", "Normal")
        self.diff_text.text = f"Difficulty: {diff_name}"
        self.banner_text.text = ""
        self._update_hud()

        self._build_board_3d()
        self._sync_block_3d()
        self._position_camera()

    def _position_camera(self) -> None:
        """Smoothly fit camera according to board dimensions."""
        assert self.env is not None
        center_x = (self.env.cols - 1) / 2.0
        center_z = -(self.env.rows - 1) / 2.0
        span = max(self.env.cols, self.env.rows)
        dist = max(11.0, span * 1.15)

        camera.position = Vec3(center_x - 1.2, dist * 0.98, center_z - dist * 0.80)
        camera.look_at(Vec3(center_x + 0.5, 0, center_z))

    def _clear_board_3d(self) -> None:
        for e in self.tile_entities:
            destroy(e)
        self.tile_entities.clear()
        self.bridge_entities.clear()

        for b in self.block_entities:
            destroy(b)
        self.block_entities.clear()
        if self.active_marker:
            destroy(self.active_marker)
            self.active_marker = None
        if self.roll_pivot:
            destroy(self.roll_pivot)
            self.roll_pivot = None

    def _build_board_3d(self) -> None:
        """Build board tiles, goal holes, bridges, and switches."""
        self._clear_board_3d()
        assert self.env is not None and self.state is not None

        for r in range(self.env.rows):
            for c in range(self.env.cols):
                tile = self.env.get_tile(r, c)
                if tile == 0:
                    continue

                checker_col = COLOR_FLOOR_A if (r + c) % 2 == 0 else COLOR_FLOOR_B

                # 1. Goal Hole (Tile 3)
                if tile == 3:
                    rim_outer = Entity(
                        parent=self.board_root,
                        model="cube",
                        position=self.GridToWorld(r, c, -0.11),
                        scale=(0.98, 0.20, 0.98),
                        color=COLOR_GOAL_RIM,
                        texture="white_cube",
                    )
                    hole_inner = Entity(
                        parent=self.board_root,
                        model="cube",
                        position=self.GridToWorld(r, c, -0.07),
                        scale=(0.72, 0.22, 0.72),
                        color=COLOR_GOAL_HOLE,
                    )
                    hole_core = Entity(
                        parent=self.board_root,
                        model="cube",
                        position=self.GridToWorld(r, c, -0.02),
                        scale=(0.56, 0.22, 0.56),
                        color=color.black,
                    )
                    self.tile_entities.extend([rim_outer, hole_inner, hole_core])
                    continue

                # 2. Bridge (Tile 7)
                if tile == 7 or (r, c) in self.env.pos_to_bridge_idx:
                    b_border = Entity(
                        parent=self.board_root,
                        model="cube",
                        position=self.GridToWorld(r, c, -0.12),
                        scale=(0.96, 0.16, 0.96),
                        color=COLOR_BRIDGE_BORDER,
                    )
                    b_top = Entity(
                        parent=self.board_root,
                        model="cube",
                        position=self.GridToWorld(r, c, -0.08),
                        scale=(0.88, 0.16, 0.88),
                        color=COLOR_BRIDGE_OPEN,
                        texture="white_cube",
                    )
                    self.tile_entities.extend([b_border, b_top])
                    self.bridge_entities[(r, c)] = (b_border, b_top)
                    continue

                # 3. Fragile Tile (Tile 2)
                if tile == 2:
                    border_ent = Entity(
                        parent=self.board_root,
                        model="cube",
                        position=self.GridToWorld(r, c, -0.12),
                        scale=(0.98, 0.18, 0.98),
                        color=COLOR_FRAGILE_INNER,
                    )
                    top_ent = Entity(
                        parent=self.board_root,
                        model="cube",
                        position=self.GridToWorld(r, c, -0.08),
                        scale=(0.90, 0.16, 0.90),
                        color=COLOR_FRAGILE,
                        texture="white_cube",
                    )
                    inner_patch = Entity(
                        parent=self.board_root,
                        model="cube",
                        position=self.GridToWorld(r, c, -0.01),
                        scale=(0.45, 0.04, 0.45),
                        color=COLOR_FRAGILE_INNER,
                    )
                    self.tile_entities.extend([border_ent, top_ent, inner_patch])
                    continue

                # 4. Standard Floor Tile (Tile 1, 4, 5, 6)
                border_ent = Entity(
                    parent=self.board_root,
                    model="cube",
                    position=self.GridToWorld(r, c, -0.12),
                    scale=(0.98, 0.18, 0.98),
                    color=COLOR_BORDER,
                )
                top_ent = Entity(
                    parent=self.board_root,
                    model="cube",
                    position=self.GridToWorld(r, c, -0.08),
                    scale=(0.91, 0.16, 0.91),
                    color=checker_col,
                    texture="white_cube",
                )
                self.tile_entities.extend([border_ent, top_ent])

                # 5. Switch icons
                if tile == 4:
                    # Soft Switch (O)
                    sw_base = Entity(
                        parent=self.board_root,
                        model="sphere",
                        position=self.GridToWorld(r, c, 0.01),
                        scale=(0.68, 0.08, 0.68),
                        color=COLOR_BORDER,
                    )
                    sw_o = Entity(
                        parent=self.board_root,
                        model="sphere",
                        position=self.GridToWorld(r, c, 0.04),
                        scale=(0.56, 0.10, 0.56),
                        color=COLOR_SW_SOFT,
                    )
                    self.tile_entities.extend([sw_base, sw_o])

                elif tile == 5:
                    # Heavy Switch (X)
                    bar1 = Entity(
                        parent=self.board_root,
                        model="cube",
                        position=self.GridToWorld(r, c, 0.03),
                        scale=(0.76, 0.08, 0.20),
                        rotation_y=45,
                        color=COLOR_SW_HEAVY,
                        texture="white_cube",
                    )
                    bar2 = Entity(
                        parent=self.board_root,
                        model="cube",
                        position=self.GridToWorld(r, c, 0.03),
                        scale=(0.76, 0.08, 0.20),
                        rotation_y=-45,
                        color=COLOR_SW_HEAVY,
                        texture="white_cube",
                    )
                    self.tile_entities.extend([bar1, bar2])

                elif tile == 6:
                    # Split Switch ()
                    ring_outer = Entity(
                        parent=self.board_root,
                        model="sphere",
                        position=self.GridToWorld(r, c, 0.02),
                        scale=(0.72, 0.09, 0.72),
                        color=COLOR_SW_SPLIT,
                    )
                    ring_inner = Entity(
                        parent=self.board_root,
                        model="sphere",
                        position=self.GridToWorld(r, c, 0.05),
                        scale=(0.36, 0.09, 0.36),
                        color=COLOR_BORDER,
                    )
                    self.tile_entities.extend([ring_outer, ring_inner])

        self._update_bridges_3d()

    def _update_bridges_3d(self) -> None:
        """Update 3D bridge visuals based on current state."""
        assert self.env is not None and self.state is not None
        for pos, (b_border, b_top) in self.bridge_entities.items():
            b_idx = self.env.pos_to_bridge_idx.get(pos, -1)
            is_open = (
                self.state.bridges_status[b_idx]
                if 0 <= b_idx < len(self.state.bridges_status)
                else False
            )
            if is_open:
                b_border.enabled = True
                b_border.color = COLOR_BRIDGE_BORDER
                b_top.color = COLOR_BRIDGE_OPEN
                b_top.scale = (0.88, 0.16, 0.88)
            else:
                b_border.enabled = False
                b_top.color = COLOR_BRIDGE_CLOSED
                b_top.scale = (0.45, 0.04, 0.45)

    def _sync_block_3d(self) -> None:
        """Render block entities directly from self.state."""
        assert self.state is not None
        for b in self.block_entities:
            destroy(b)
        self.block_entities.clear()
        if self.active_marker:
            destroy(self.active_marker)
            self.active_marker = None
        if self.roll_pivot:
            destroy(self.roll_pivot)
            self.roll_pivot = None

        ori = self.state.orientation
        pos = self.state.block_positions

        if ori == Orientation.STANDING:
            r, c = pos[0]
            ent = Entity(
                parent=self.board_root,
                model="cube",
                position=self.GridToWorld(r, c, 1.0),
                scale=(0.92, 1.96, 0.92),
                color=COLOR_BLOCK_MAIN,
                texture="white_cube",
            )
            self.block_entities.append(ent)

        elif ori == Orientation.LYING_HORIZONTAL:
            (r, c1), (_, c2) = pos
            mid_c = (c1 + c2) / 2.0
            ent = Entity(
                parent=self.board_root,
                model="cube",
                position=self.GridToWorld(r, mid_c, 0.5),
                scale=(1.94, 0.92, 0.92),
                color=COLOR_BLOCK_MAIN,
                texture="white_cube",
            )
            self.block_entities.append(ent)

        elif ori == Orientation.LYING_VERTICAL:
            (r1, c), (r2, _) = pos
            mid_r = (r1 + r2) / 2.0
            ent = Entity(
                parent=self.board_root,
                model="cube",
                position=self.GridToWorld(mid_r, c, 0.5),
                scale=(0.92, 0.92, 1.94),
                color=COLOR_BLOCK_MAIN,
                texture="white_cube",
            )
            self.block_entities.append(ent)

        elif ori == Orientation.SPLIT:
            for idx, (r, c) in enumerate(pos):
                is_active = idx == self.state.active_split_index
                b_col = COLOR_BLOCK_ACTIVE if is_active else COLOR_BLOCK_INACTIVE
                ent = Entity(
                    parent=self.board_root,
                    model="cube",
                    position=self.GridToWorld(r, c, 0.5),
                    scale=(0.90, 0.92, 0.90),
                    color=b_col,
                    texture="white_cube",
                )
                self.block_entities.append(ent)
                if is_active:
                    self.active_marker = Entity(
                        parent=self.board_root,
                        model="sphere",
                        position=self.GridToWorld(r, c, 1.22),
                        scale=(0.32, 0.32, 0.32),
                        color=color.rgb32(250, 204, 21),
                    )

        self._update_bridges_3d()

    def _update_hud(self) -> None:
        assert self.state is not None
        ori_name = self.state.orientation.value
        split_info = (
            f" (Piece #{self.state.active_split_index + 1})"
            if self.state.orientation == Orientation.SPLIT
            else ""
        )
        self.status_text.text = f"Steps: {self.move_count} | {ori_name}{split_info}"

    def handle_move(self, move: str, from_solver: bool = False) -> None:
        """Handle player or AI solver move with accurate edge-rolling physics."""
        if self.is_animating or self.game_over:
            return
        if not from_solver and self.auto_play_queue:
            return

        assert self.env is not None and self.state is not None
        old_state = self.state

        # Switching split pieces does not rotate
        if move in ("SPACE", "SWITCH_BLOCK"):
            next_state = self.env.apply_move(self.state, move)
            if next_state is not None:
                self.state = next_state
                self.move_count += 1
                self._sync_block_3d()
                self._update_hud()
            return

        # Check legal move vs illegal move
        next_state = self.env.apply_move(self.state, move)

        if next_state is None:
            # Illegal move: execute authentic edge roll into abyss without penetrating ground!
            self._start_invalid_sequence(old_state, move)
            return

        # Valid move: execute natural edge-rolling animation
        self.state = next_state
        self.move_count += 1
        self._start_rolling_animation(old_state, move, is_invalid=False)

    # =========================================================================
    # NATURAL ROLLING ANIMATION (AROUND BOTTOM CONTACT EDGE)
    # =========================================================================
    def _start_rolling_animation(
        self, prev_state: State, move: str, is_invalid: bool = False
    ) -> None:
        """Initialize pivot on the exact contact edge and preserve world positions."""
        pivot_pos, axis, target_deg = self._compute_roll_pivot(prev_state, move)
        if pivot_pos is None or prev_state.orientation == Orientation.SPLIT:
            if is_invalid:
                self._start_gravity_fall(move)
            else:
                self._sync_block_3d()
                self._update_hud()
                self._check_goal_condition()
            return

        self.is_animating = True
        self.is_rolling = True
        self.is_invalid_roll = is_invalid
        self.roll_elapsed = 0.0
        self.roll_duration = 0.22
        self.roll_axis = axis
        self.roll_target_deg = target_deg

        if self.roll_pivot:
            destroy(self.roll_pivot)
        self.roll_pivot = Entity(parent=self.board_root, position=pivot_pos)

        # Reparent using world_parent so initial geometry never glitches or shifts!
        for b in self.block_entities:
            b.world_parent = self.roll_pivot

    def _compute_roll_pivot(
        self, state: State, move: str
    ) -> Tuple[Optional[Vec3], str, float]:
        """
        Compute edge pivot location and rotation angle in Ursina coordinates.
        +X is RIGHT, -X is LEFT.
        +Z is UP (facing North), -Z is DOWN (facing South).
        """
        ori = state.orientation
        pos = state.block_positions

        if ori == Orientation.STANDING:
            r, c = pos[0]
            if move == "RIGHT":
                return Vec3(c + 0.5, 0.0, -r), "z", 90.0
            if move == "LEFT":
                return Vec3(c - 0.5, 0.0, -r), "z", -90.0
            if move == "UP":
                return Vec3(c, 0.0, -r + 0.5), "x", 90.0
            if move == "DOWN":
                return Vec3(c, 0.0, -r - 0.5), "x", -90.0

        elif ori == Orientation.LYING_HORIZONTAL:
            (r, c1), (_, c2) = pos
            if move == "RIGHT":
                return Vec3(c2 + 0.5, 0.0, -r), "z", 90.0
            if move == "LEFT":
                return Vec3(c1 - 0.5, 0.0, -r), "z", -90.0
            if move == "UP":
                return Vec3((c1 + c2) / 2.0, 0.0, -r + 0.5), "x", 90.0
            if move == "DOWN":
                return Vec3((c1 + c2) / 2.0, 0.0, -r - 0.5), "x", -90.0

        elif ori == Orientation.LYING_VERTICAL:
            (r1, c), (r2, _) = pos
            if move == "UP":
                return Vec3(c, 0.0, -r1 + 0.5), "x", 90.0
            if move == "DOWN":
                return Vec3(c, 0.0, -r2 - 0.5), "x", -90.0
            if move == "RIGHT":
                return Vec3(c + 0.5, 0.0, -(r1 + r2) / 2.0), "z", 90.0
            if move == "LEFT":
                return Vec3(c - 0.5, 0.0, -(r1 + r2) / 2.0), "z", -90.0

        return None, "z", 0.0

    def _finish_rolling(self) -> None:
        """Conclude rolling step, cleanup pivot, and verify state."""
        self.is_rolling = False
        if self.roll_pivot:
            destroy(self.roll_pivot)
            self.roll_pivot = None

        if self.is_invalid_roll:
            # Transition directly from the edge roll into free-fall gravity!
            self.is_invalid_roll = False
            self._start_gravity_fall(self.pending_fall_move, mode=self.pending_fall_mode)
            return

        self.is_animating = False
        self._sync_block_3d()
        self._update_hud()
        self._check_goal_condition()

    def _check_goal_condition(self) -> None:
        assert self.env is not None and self.state is not None
        if self.env.is_goal(self.state):
            self.game_over = True
            self.auto_play_queue.clear()
            self._animate_victory()
        elif self.auto_play_queue:
            invoke(self._step_auto_play, delay=0.04)

    # =========================================================================
    # TWO-STAGE AUTHENTIC EDGE-FALL & GRAVITY SIMULATION
    # =========================================================================
    def _start_invalid_sequence(self, old_state: State, move: str) -> None:
        """
        Bloxorz accurate physics:
        Instead of immediately falling through the boundary, the block first rotates
        around the board's outer boundary edge (outward away from the floor).
        Once its center of gravity hangs completely over the abyss, gravity takes over!
        """
        assert self.env is not None
        theo_state = self.env.get_theoretical_move(old_state, move)
        if theo_state is None:
            self._start_gravity_fall(move)
            return

        # Check if failure was fragile tile collapse
        if theo_state.orientation == Orientation.STANDING:
            r, c = theo_state.block_positions[0]
            if self.env.get_tile(r, c) == 2:
                # Fragile collapse: roll onto fragile tile first, then collapse into abyss!
                self.pending_fall_mode = "fragile_collapse"
                self.pending_fall_move = move
                self._start_rolling_animation(old_state, move, is_invalid=True)
                return

        # Edge overstep: block rolls around current contact edge outward into the void
        self.pending_fall_mode = "edge_fall"
        self.pending_fall_move = move
        self._start_rolling_animation(old_state, move, is_invalid=True)

    def _start_gravity_fall(self, move: str, mode: Optional[str] = "edge_fall") -> None:
        """Trigger authentic gravity acceleration into the abyss."""
        self.is_animating = True
        self.is_falling = True
        self.game_over = True
        self.fall_time = 0.0
        self.fall_duration = 1.15

        self.banner_text.color = color.rgb32(248, 113, 113)
        self.banner_text.text = "FALLEN INTO THE ABYSS! Restarting..."

        # Re-attach block pieces to board_root preserving world transform
        for b in self.block_entities:
            b.world_parent = self.board_root

        dir_map = {
            "RIGHT": Vec3(2.2, 0.4, 0),
            "LEFT": Vec3(-2.2, 0.4, 0),
            "UP": Vec3(0, 0.4, 2.2),
            "DOWN": Vec3(0, 0.4, -2.2),
        }
        rot_map = {
            "RIGHT": Vec3(0, 0, 240),
            "LEFT": Vec3(0, 0, -240),
            "UP": Vec3(240, 0, 0),
            "DOWN": Vec3(-240, 0, 0),
        }

        if mode == "fragile_collapse":
            base_v = Vec3(0, -1.8, 0)
            base_rot = Vec3(25, 10, -25)
        else:
            base_v = dir_map.get(move, Vec3(0, 0.2, 0))
            base_rot = rot_map.get(move, Vec3(180, 0, 0))

        self.fall_positions = [Vec3(b.world_position) for b in self.block_entities]
        self.fall_velocities = [Vec3(base_v) for _ in self.block_entities]
        self.fall_rotations = [Vec3(b.world_rotation) for b in self.block_entities]
        self.fall_rot_speeds = [Vec3(base_rot) for _ in self.block_entities]

        invoke(self.restart_level, delay=1.2)

    def _update_physics(self, dt: float) -> None:
        """Real-time Euler integration for continuous smooth rotation & gravity."""
        # 1. Update rolling animation
        if self.is_rolling and self.roll_pivot:
            self.roll_elapsed += dt
            t = min(1.0, self.roll_elapsed / self.roll_duration)
            # Smooth sine-eased curve for natural mechanical weight
            eased_t = 0.5 - 0.5 * math.cos(math.pi * t)
            current_deg = eased_t * self.roll_target_deg
            if self.roll_axis == "z":
                self.roll_pivot.rotation_z = current_deg
            else:
                self.roll_pivot.rotation_x = current_deg

            if t >= 1.0:
                self._finish_rolling()

        # 2. Update gravity falling physics
        if self.is_falling:
            self.fall_time += dt
            gravity = Vec3(0, -24.0, 0)  # Gravity g = 24 m/s^2

            for i, b in enumerate(self.block_entities):
                if i < len(self.fall_velocities):
                    self.fall_velocities[i] += gravity * dt
                    self.fall_positions[i] += self.fall_velocities[i] * dt
                    self.fall_rotations[i] += self.fall_rot_speeds[i] * dt
                    b.world_position = self.fall_positions[i]
                    b.world_rotation = self.fall_rotations[i]

    def _animate_victory(self) -> None:
        """Victory animation: block shines green and drops cleanly into the goal hole."""
        self.is_animating = True
        for b in self.block_entities:
            b.color = color.rgb32(34, 197, 94)
            b.animate_position(
                b.position + Vec3(0, -1.8, 0),
                duration=0.55,
            )

        if self.current_level_idx < len(LEVELS) - 1:
            self.banner_text.color = color.rgb32(74, 222, 128)
            self.banner_text.text = (
                f"STAGE {self.current_level_idx + 1} CLEARED ({self.move_count} moves)! Next stage..."
            )
            invoke(self.next_level, delay=1.3)
        else:
            self.banner_text.color = color.rgb32(250, 204, 21)
            self.banner_text.text = "CONGRATULATIONS! ALL 15 STAGES COMPLETED!"
            self.is_animating = False

    def restart_level(self) -> None:
        self.load_level(self.current_level_idx)

    def next_level(self) -> None:
        if self.current_level_idx < len(LEVELS) - 1:
            self.load_level(self.current_level_idx + 1)
        else:
            self.load_level(0)

    def prev_level(self) -> None:
        if self.current_level_idx > 0:
            self.load_level(self.current_level_idx - 1)
        else:
            self.load_level(len(LEVELS) - 1)

    def run_solver(self, solver_type: str) -> None:
        """Run requested AI algorithm (BFS, DFS, UCS, A*) and animate solution."""
        if self.is_animating:
            return
        if self.game_over:
            self.restart_level()

        assert self.env is not None and self.state is not None
        solver_map = {
            "BFS": BFSSolver,
            "DFS": DFSSolver,
            "UCS": UCSSolver,
            "ASTAR": AStarSolver,
        }
        solver_cls = solver_map.get(solver_type)
        if not solver_cls:
            return

        solver = solver_cls()
        result = solver.solve(self.state, self.env)

        self.solver_metrics_text.text = (
            f"{solver_type} Result:\n"
            f" - Solution: {result.solution_length} steps\n"
            f" - Expanded: {result.expanded_nodes} nodes\n"
            f" - Time: {result.search_time * 1000:.2f} ms\n"
            f" - Memory: {result.peak_memory:.4f} MB"
        )

        if not result.path:
            self.banner_text.color = color.rgb32(251, 146, 60)
            self.banner_text.text = (
                f"{solver_type}: No path found (or algorithm pending implementation)!"
            )
            return

        self.banner_text.color = color.rgb32(56, 189, 248)
        self.banner_text.text = f"Playing {solver_type} solution ({len(result.path)} moves)..."
        self.auto_play_queue = list(result.path)
        self._step_auto_play()

    def _step_auto_play(self) -> None:
        if not self.auto_play_queue or self.game_over or self.is_animating:
            return
        next_act = self.auto_play_queue.pop(0)
        self.handle_move(next_act, from_solver=True)


def main() -> None:
    export_levels_to_json("levels_json")

    app = Ursina(
        title="Bloxorz 3D - Ursina Engine (15 Levels)",
        borderless=False,
        fullscreen=False,
        size=(1360, 820),
    )
    window.color = COLOR_BG
    window.fps_counter.enabled = False
    window.exit_button.visible = False

    game = BloxorzUrsinaApp()

    # Register global update loop for continuous physics simulation
    def update() -> None:
        game._update_physics(utime.dt)

    def input(key: str) -> None:
        if key in ("w", "up arrow"):
            game.handle_move("UP")
        elif key in ("s", "down arrow"):
            game.handle_move("DOWN")
        elif key in ("a", "left arrow"):
            game.handle_move("LEFT")
        elif key in ("d", "right arrow"):
            game.handle_move("RIGHT")
        elif key == "space":
            game.handle_move("SPACE")
        elif key == "r":
            game.restart_level()
        elif key == "n":
            game.next_level()
        elif key == "p":
            game.prev_level()
        elif key == "escape":
            application.quit()

    import __main__
    setattr(__main__, "update", update)
    setattr(__main__, "input", input)

    app.run()


if __name__ == "__main__":
    main()
