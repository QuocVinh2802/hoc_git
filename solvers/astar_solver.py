import time
import tracemalloc

from state import State, SearchResult
from game_env import GameEnv
from base_solver import BaseSolver


class AStarSolver(BaseSolver):
    """
    Khung mẫu (Template) cho thuật toán Tìm kiếm A* (A-Star).
    Thành viên phụ trách A* chỉ cần viết code bên trong hàm solve() bên dưới.
    """

    def heuristic(self, state: State, env: GameEnv) -> float:
        """Hàm heuristic ước lượng chi phí từ state hiện tại đến env.goal_pos."""
        # TODO: Thiết kế hàm heuristic admissible (VD: khoảng cách Manhattan chia 2)
        return 0.0

    def solve(self, initial_state: State, env: GameEnv) -> SearchResult:
        tracemalloc.start()
        start_time = time.perf_counter()

        # TODO: Thành viên phụ trách A* cài đặt thuật toán tại đây (dùng heapq với f = g + h).
        expanded_nodes = 0
        final_path = []

        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        search_time = time.perf_counter() - start_time

        return SearchResult(
            path=final_path,
            search_time=search_time,
            peak_memory=peak_mem / (1024 * 1024),
            expanded_nodes=expanded_nodes,
            solution_length=len(final_path),
        )
