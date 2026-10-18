from enum import Enum
from dataclasses import dataclass
from typing import Tuple, List


class Orientation(Enum):
    STANDING = "STANDING"
    LYING_HORIZONTAL = "LYING_HORIZONTAL"
    LYING_VERTICAL = "LYING_VERTICAL"
    SPLIT = "SPLIT"


@dataclass(frozen=True)
class State:
    # Tọa độ của khối hộp.
    # - Nếu STANDING: ((r, c),)
    # - Nếu LYING_HORIZONTAL: ((r, c), (r, c + 1)) (sắp xếp tăng dần)
    # - Nếu LYING_VERTICAL: ((r, c), (r + 1, c)) (sắp xếp tăng dần)
    # - Nếu SPLIT: ((rA, cA), (rB, cB)) (giữ đúng thứ tự khối 0 và khối 1)
    block_positions: Tuple[Tuple[int, int], ...]

    # Hướng định vị của khối
    orientation: Orientation

    # Trạng thái các cầu: tuple chứa các giá trị boolean (True = Mở, False = Đóng)
    bridges_status: Tuple[bool, ...] = ()

    # Chỉ số khối nhỏ đang được điều khiển khi ở trạng thái SPLIT (0 hoặc 1)
    active_split_index: int = 0


@dataclass
class SearchResult:
    path: List[str]          # Danh sách các bước đi, VD: ['UP', 'RIGHT', 'DOWN', 'SPACE']
    search_time: float       # Thời gian tìm kiếm (giây)
    peak_memory: float       # Đỉnh bộ nhớ sử dụng (MB)
    expanded_nodes: int      # Số nút đã duyệt
    solution_length: int     # Độ dài lời giải (số bước)