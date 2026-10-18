from abc import ABC, abstractmethod
from state import State, SearchResult
from game_env import GameEnv

class BaseSolver(ABC):
    @abstractmethod
    def solve(self, initial_state: State, env: GameEnv) -> SearchResult:
        """
        Hàm thực thi thuật toán tìm kiếm.
        Yêu cầu trả về đối tượng SearchResult.
        """
        pass