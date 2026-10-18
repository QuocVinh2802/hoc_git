import time
import tracemalloc
from typing import Set

from state import State, SearchResult
from game_env import GameEnv
from base_solver import BaseSolver


class DFSSolver(BaseSolver):
    """
    Khung mẫu (Template) cho thuật toán Tìm kiếm theo chiều sâu (DFS / IDS).
    Thành viên phụ trách DFS chỉ cần viết code bên trong hàm solve() bên dưới.
    """

    def solve(self, initial_state: State, env: GameEnv) -> SearchResult:
        tracemalloc.start()
        start_time = time.perf_counter()

        # TODO: Thành viên phụ trách DFS/IDS cài đặt thuật toán tại đây.
        # Gợi ý cấu trúc Stack: stack = [(initial_state, [])]
        # Sử dụng env.is_goal(state) và env.get_successors(state)
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
