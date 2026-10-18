import time
import tracemalloc
from collections import deque
from typing import Set

from state import State, SearchResult
from game_env import GameEnv
from base_solver import BaseSolver


class BFSSolver(BaseSolver):
    """
    Khung cài đặt thuật toán Tìm kiếm theo chiều rộng (BFS).
    Dành cho thành viên phụ trách BFS hoàn thiện/tinh chỉnh thêm nếu cần.
    """

    def solve(self, initial_state: State, env: GameEnv) -> SearchResult:
        tracemalloc.start()
        start_time = time.perf_counter()

        queue = deque([(initial_state, [])])
        visited: Set[State] = {initial_state}
        expanded_nodes = 0
        final_path = []

        while queue:
            current_state, path = queue.popleft()
            expanded_nodes += 1

            if env.is_goal(current_state):
                final_path = path
                break

            for action, next_state in env.get_successors(current_state):
                if next_state not in visited:
                    visited.add(next_state)
                    queue.append((next_state, path + [action]))

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
