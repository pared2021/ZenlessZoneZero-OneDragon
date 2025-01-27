from enum import Enum

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.screen.screen_area import ScreenArea


class ScreenNormalWorldEnum(Enum):

    UID = ScreenArea(area_name='uid', pc_rect=Rect(1814, 1059, 1919, 1079))
    BATTLE_FAIL = ScreenArea(
        area_name='战斗失败',
        pc_rect=Rect(850, 400, 1070, 450),  # 这个坐标需要根据实际游戏UI调整
        text='挑战失败',
        lcs_percent=0.8,
        id_mark=True
    )
