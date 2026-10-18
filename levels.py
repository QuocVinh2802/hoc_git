import json
import os
from typing import List, Dict, Any

# Danh sách 15 màn chơi với độ khó tăng dần:
# Quy ước mã ô:
# 0: Vực thẳm (Void)
# 1: Sàn thường (Floor)
# 2: Ô dễ vỡ - màu cam (Fragile - cấm đứng thẳng)
# 3: Lỗ đích (Goal)
# 4: Công tắc nhẹ - hình tròn O (Soft Switch)
# 5: Công tắc nặng - hình chữ X (Heavy Switch)
# 6: Công tắc phân tách - hình () (Split Switch)
# 7: Ô cầu (Bridge)

LEVELS: List[Dict[str, Any]] = [
    # =========================================================================
    # LEVEL 1: Khởi động (Classic Stage 1) - Dễ
    # =========================================================================
    {
        "id": 1,
        "name": "Màn 1: Khởi Động",
        "difficulty": "Dễ (1/15)",
        "description": "Làm quen với cách lăn khối hộp 1x1x2 và đưa khối đứng thẳng vào lỗ đích.",
        "grid": [
            [1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 1, 1, 3, 1, 1],
            [0, 0, 0, 0, 0, 0, 1, 1, 1, 0],
        ],
        "start_pos": [1, 1],
        "goal_pos": [4, 7],
        "bridges": [],
        "switches": [],
    },

    # =========================================================================
    # LEVEL 2: Đường Hẹp Quanh Co - Dễ
    # =========================================================================
    {
        "id": 2,
        "name": "Màn 2: Hành Lang Chữ Z",
        "difficulty": "Dễ (2/15)",
        "description": "Điều chỉnh tư thế nằm ngang / nằm dọc khéo léo để ôm cua qua hành lang hẹp.",
        "grid": [
            [1, 1, 1, 1, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 0, 0, 0],
            [1, 1, 1, 0, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 1, 1, 3, 1],
            [0, 0, 0, 0, 0, 1, 1, 1, 1],
        ],
        "start_pos": [1, 1],
        "goal_pos": [4, 7],
        "bridges": [],
        "switches": [],
    },

    # =========================================================================
    # LEVEL 3: Đảo Đá Giữa Vực (Classic Stage 3) - Dễ
    # =========================================================================
    {
        "id": 3,
        "name": "Màn 3: Eo Biển Hẹp",
        "difficulty": "Dễ (3/15)",
        "description": "Băng qua dải đất hẹp nối hai đảo lớn mà không để khối hộp lăn xuống vực.",
        "grid": [
            [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
            [1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1],
            [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 3, 1],
            [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
        ],
        "start_pos": [2, 1],
        "goal_pos": [3, 13],
        "bridges": [],
        "switches": [],
    },

    # =========================================================================
    # LEVEL 4: Gạch Cam Dễ Vỡ Đầu Tiên - Trung bình-Dễ
    # =========================================================================
    {
        "id": 4,
        "name": "Màn 4: Bước Chân Nhẹ Nhàng",
        "difficulty": "Trung bình - Dễ (4/15)",
        "description": "Ô màu cam (Dễ vỡ) sẽ sập nếu khối hộp ĐỨNG THẲNG trên đó. Hãy lăn NẰM qua chúng!",
        "grid": [
            [0, 0, 0, 2, 2, 2, 2, 0, 0, 0],
            [1, 1, 1, 2, 2, 2, 2, 1, 1, 1],
            [1, 1, 1, 2, 2, 2, 2, 1, 3, 1],
            [1, 1, 1, 0, 0, 0, 0, 1, 1, 1],
        ],
        "start_pos": [1, 1],
        "goal_pos": [2, 8],
        "bridges": [],
        "switches": [],
    },

    # =========================================================================
    # LEVEL 5: Mê Cung Gạch Cam (Classic Stage 4) - Trung bình
    # =========================================================================
    {
        "id": 5,
        "name": "Màn 5: Sàn Cam Tử Thần",
        "difficulty": "Trung bình (5/15)",
        "description": "Toàn bộ khu vực phía trên và xung quanh đích được lát gạch cam dễ vỡ.",
        "grid": [
            [0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0],
            [0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0],
            [1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0],
            [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
            [1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
            [1, 1, 1, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 0],
            [1, 1, 1, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2],
            [0, 0, 0, 0, 0, 1, 3, 1, 0, 0, 2, 2, 1, 2],
            [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 2, 2, 2, 2],
        ],
        "start_pos": [5, 1],
        "goal_pos": [7, 6],
        "bridges": [],
        "switches": [],
    },

    # =========================================================================
    # LEVEL 6: Công Tắc Nhẹ & Cầu (Soft Switch O) - Trung bình
    # =========================================================================
    {
        "id": 6,
        "name": "Màn 6: Cây Cầu Đầu Tiên",
        "difficulty": "Trung bình (6/15)",
        "description": "Công tắc tròn (O) là công tắc nhẹ: chạm bất kỳ phần nào của khối cũng bật/tắt cầu.",
        "grid": [
            [1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
            [1, 1, 4, 1, 7, 7, 1, 1, 1, 1, 0],
            [1, 1, 1, 1, 0, 0, 1, 1, 3, 1, 0],
            [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0],
        ],
        "start_pos": [1, 1],
        "goal_pos": [2, 8],
        "bridges": [
            {"id": 0, "positions": [[1, 4], [1, 5]], "initial_open": False}
        ],
        "switches": [
            {"pos": [1, 2], "type": "soft", "targets": [0], "behavior": "toggle"}
        ],
    },

    # =========================================================================
    # LEVEL 7: Công Tắc Nặng (Heavy Switch X) - Trung bình
    # =========================================================================
    {
        "id": 7,
        "name": "Màn 7: Sức Nặng Quyết Định",
        "difficulty": "Trung bình (7/15)",
        "description": "Công tắc chữ X (Nặng) chỉ kích hoạt khi khối hộp ĐỨNG THẲNG trực tiếp trên nó!",
        "grid": [
            [1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 5, 1, 0, 0, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 7, 7, 1, 1, 3, 1],
            [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
        ],
        "start_pos": [1, 1],
        "goal_pos": [2, 9],
        "bridges": [
            {"id": 0, "positions": [[2, 5], [2, 6]], "initial_open": False}
        ],
        "switches": [
            {"pos": [1, 3], "type": "heavy", "targets": [0], "behavior": "toggle"}
        ],
    },

    # =========================================================================
    # LEVEL 8: Hai Nhịp Cầu Liên Tiếp (Classic Stage 2) - Trung bình-Khá
    # =========================================================================
    {
        "id": 8,
        "name": "Màn 8: Hai Nhịp Cầu (Stage 2 Cổ Điển)",
        "difficulty": "Khá (8/15)",
        "description": "Kết hợp công tắc nhẹ (O) mở cầu thứ nhất và công tắc nặng (X) mở cầu thứ hai.",
        "grid": [
            [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 1, 0, 0, 1, 1, 5, 1, 0, 0, 1, 3, 1],
            [1, 1, 4, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 1, 7, 7, 1, 1, 1, 1, 7, 7, 1, 1, 1],
            [1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0],
        ],
        "start_pos": [3, 1],
        "goal_pos": [1, 13],
        "bridges": [
            {"id": 0, "positions": [[4, 4], [4, 5]], "initial_open": False},
            {"id": 1, "positions": [[4, 10], [4, 11]], "initial_open": False},
        ],
        "switches": [
            {"pos": [2, 2], "type": "soft", "targets": [0], "behavior": "toggle"},
            {"pos": [1, 8], "type": "heavy", "targets": [1], "behavior": "toggle"},
        ],
    },

    # =========================================================================
    # LEVEL 9: Bẫy Công Tắc Nhẹ & Gạch Cam - Khá
    # =========================================================================
    {
        "id": 9,
        "name": "Màn 9: Cạm Bẫy Công Tắc",
        "difficulty": "Khá (9/15)",
        "description": "Cầu thứ nhất đã mở sẵn, nhưng dẫm nhầm vào công tắc O sẽ đóng cầu! Hãy tìm công tắc X để mở cầu thứ hai.",
        "grid": [
            [1, 1, 1, 1, 7, 7, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 0, 0, 1, 4, 2, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 1, 0, 0, 1, 2, 5, 1, 1, 7, 7, 1, 3, 1],
            [1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1],
        ],
        "start_pos": [1, 1],
        "goal_pos": [2, 14],
        "bridges": [
            {"id": 0, "positions": [[0, 4], [0, 5]], "initial_open": True},
            {"id": 1, "positions": [[2, 11], [2, 12]], "initial_open": False},
        ],
        "switches": [
            {"pos": [1, 7], "type": "soft", "targets": [0], "behavior": "close"},
            {"pos": [2, 8], "type": "heavy", "targets": [1], "behavior": "open"},
        ],
    },

    # =========================================================================
    # LEVEL 10: Công Tắc Phân Tách Khối (Split Switch) - Khá
    # =========================================================================
    {
        "id": 10,
        "name": "Màn 10: Phân Thân Hợp Nhất",
        "difficulty": "Khá (10/15)",
        "description": "Đứng vào vòng tròn () để tách thành 2 khối đơn. Nhấn SPACE đổi khối, chạm nhau để hợp nhất!",
        "grid": [
            [1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
            [1, 1, 6, 1, 0, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 0, 1, 1, 3, 1, 1],
            [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        ],
        "start_pos": [1, 1],
        "goal_pos": [2, 7],
        "bridges": [],
        "switches": [
            {"pos": [1, 2], "type": "split", "spawn_positions": [[1, 5], [3, 5]]}
        ],
    },

    # =========================================================================
    # LEVEL 11: Song Hành Mở Cầu (Split + Soft Switch) - Khó
    # =========================================================================
    {
        "id": 11,
        "name": "Màn 11: Phối Hợp Hai Nửa",
        "difficulty": "Khó (11/15)",
        "description": "Khối đơn không thể kích hoạt công tắc nặng hay vào đích, nhưng mở được công tắc nhẹ (O)!",
        "grid": [
            [1, 1, 1, 1, 0, 0, 1, 1, 4, 0, 0, 0, 0],
            [1, 1, 6, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1],
            [1, 1, 1, 1, 0, 0, 7, 0, 0, 1, 1, 3, 1],
            [1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1],
        ],
        "start_pos": [1, 1],
        "goal_pos": [2, 11],
        "bridges": [
            {"id": 0, "positions": [[2, 6]], "initial_open": False}
        ],
        "switches": [
            {"pos": [1, 2], "type": "split", "spawn_positions": [[0, 6], [3, 6]]},
            {"pos": [0, 8], "type": "soft", "targets": [0], "behavior": "open"},
        ],
    },

    # =========================================================================
    # LEVEL 12: Đảo Cầu Đan Xen (Classic Stage 5 style) - Khó
    # =========================================================================
    {
        "id": 12,
        "name": "Màn 12: Liên Hoàn Cầu Kéo",
        "difficulty": "Khó (12/15)",
        "description": "Nhiều công tắc điều khiển các cầu khác nhau. Hãy tính kỹ tư thế khối khi qua cầu!",
        "grid": [
            [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 1, 4, 1, 1, 5, 1, 0, 0],
            [1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0],
            [1, 1, 1, 0, 0, 0, 0, 0, 0, 7, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 4, 1, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 7, 7, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 3, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1],
        ],
        "start_pos": [2, 1],
        "goal_pos": [7, 11],
        "bridges": [
            {"id": 0, "positions": [[3, 9]], "initial_open": False},
            {"id": 1, "positions": [[6, 7], [6, 8]], "initial_open": False},
        ],
        "switches": [
            {"pos": [1, 6], "type": "soft", "targets": [0], "behavior": "open"},
            {"pos": [1, 9], "type": "heavy", "targets": [0], "behavior": "toggle"},
            {"pos": [5, 5], "type": "soft", "targets": [1], "behavior": "open"},
        ],
    },

    # =========================================================================
    # LEVEL 13: Vách Đá Chênh Vênh (Classic Stage 6) - Khó
    # =========================================================================
    {
        "id": 13,
        "name": "Màn 13: Vách Đá Tử Thần",
        "difficulty": "Khó (13/15)",
        "description": "Bản đồ hẹp với nhiều khúc ngoặt chữ L buộc bạn phải xoay hướng khối ở không gian tối thiểu.",
        "grid": [
            [0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1],
            [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 3, 1],
            [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0],
        ],
        "start_pos": [3, 0],
        "goal_pos": [4, 13],
        "bridges": [],
        "switches": [],
    },

    # =========================================================================
    # LEVEL 14: Pháo Đài Gạch Cam & Cầu Đôi - Rất Khó
    # =========================================================================
    {
        "id": 14,
        "name": "Màn 14: Pháo Đài Trên Không",
        "difficulty": "Rất Khó (14/15)",
        "description": "Vượt qua thảm gạch cam, kích hoạt công tắc nặng ở đảo phụ rồi quay về mở cổng vào đích.",
        "grid": [
            [0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0],
            [1, 1, 1, 2, 2, 5, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 2, 2, 1, 1, 7, 7, 1, 3, 1],
            [1, 1, 1, 0, 1, 2, 2, 0, 0, 1, 1, 1],
            [0, 0, 0, 0, 1, 2, 2, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 4, 1, 0, 0, 0, 0],
        ],
        "start_pos": [2, 1],
        "goal_pos": [2, 10],
        "bridges": [
            {"id": 0, "positions": [[2, 7]], "initial_open": False},
            {"id": 1, "positions": [[2, 8]], "initial_open": False},
        ],
        "switches": [
            {"pos": [5, 6], "type": "soft", "targets": [0], "behavior": "open"},
            {"pos": [1, 5], "type": "heavy", "targets": [1], "behavior": "open"},
        ],
    },

    # =========================================================================
    # LEVEL 15: Thử Thách Tối Thượng (Tổng hợp mọi cơ chế) - Cực Khó
    # =========================================================================
    {
        "id": 15,
        "name": "Màn 15: Thử Thách Tối Thượng",
        "difficulty": "Cực Khó (15/15)",
        "description": "Tổng hợp tất cả cơ chế: Gạch cam dễ vỡ, Công tắc phân tách (), Công tắc nhẹ O, Công tắc nặng X và Cầu kép!",
        "grid": [
            [1, 1, 2, 1, 1, 1, 0, 0, 1, 1, 4, 0, 0, 0],
            [1, 1, 2, 1, 6, 1, 0, 0, 1, 0, 0, 1, 1, 1],
            [1, 1, 2, 1, 1, 1, 0, 0, 7, 0, 0, 1, 3, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 1, 5, 1, 7, 1, 1],
            [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0],
        ],
        "start_pos": [1, 1],
        "goal_pos": [2, 12],
        "bridges": [
            {"id": 0, "positions": [[2, 8]], "initial_open": False},
            {"id": 1, "positions": [[4, 11]], "initial_open": False},
        ],
        "switches": [
            {"pos": [1, 4], "type": "split", "spawn_positions": [[0, 8], [3, 8]]},
            {"pos": [0, 10], "type": "soft", "targets": [0], "behavior": "open"},
            {"pos": [4, 9], "type": "heavy", "targets": [1], "behavior": "open"},
        ],
    },
]


def get_level(level_idx: int) -> Dict[str, Any]:
    """Lấy dữ liệu màn chơi theo chỉ số (0 đến 14)."""
    idx = max(0, min(level_idx, len(LEVELS) - 1))
    return LEVELS[idx]


def export_levels_to_json(folder: str = "levels_json") -> None:
    """Xuất toàn bộ 15 màn chơi ra các file JSON chuẩn để các bộ giải hoặc test script tái sử dụng."""
    os.makedirs(folder, exist_ok=True)
    for lvl in LEVELS:
        filepath = os.path.join(folder, f"level_{lvl['id']:02d}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(lvl, f, ensure_ascii=False, indent=2)
