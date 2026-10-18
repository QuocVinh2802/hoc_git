import time
import tracemalloc

from state import State, SearchResult
from game_env import GameEnv
from base_solver import BaseSolver


class UCSSolver(BaseSolver):
    """
    Khung mẫu (Template) cho thuật toán Tìm kiếm chi phí đồng nhất (UCS).
    Thành viên phụ trách UCS chỉ cần viết code bên trong hàm solve() bên dưới.
    """

    def solve(self, initial_state: State, env: GameEnv) -> SearchResult:
        tracemalloc.start()
        start_time = time.perf_counter()

        # TODO: Thành viên phụ trách UCS cài đặt thuật toán tại đây (dùng heapq).
        # Có thể dùng env.get_step_cost(current_state, action, next_state) hoặc tự định nghĩa hàm chi phí.
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
