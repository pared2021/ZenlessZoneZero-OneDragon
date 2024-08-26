from enum import Enum

from typing import Optional

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig


class HollowZeroExtraTask(Enum):

    NONE = ConfigItem('不进行')
    LEVEL_2 = ConfigItem('2层业绩后退出')
    LEVEL_3 = ConfigItem('3层业绩后退出')


class HollowZeroConfig(YamlConfig):

    def __init__(self, instance_idx: Optional[int] = None):
        YamlConfig.__init__(
            self,
            module_name='hollow_zero',
            instance_idx=instance_idx,
        )

    @property
    def mission_name(self) -> str:
        return self.get('mission_name', '旧都列车-内部')

    @mission_name.setter
    def mission_name(self, new_value: str):
        self.update('mission_name', new_value)

    @property
    def challenge_config(self) -> str:
        return self.get('challenge_config', '以太')

    @challenge_config.setter
    def challenge_config(self, new_value: str):
        self.update('challenge_config', new_value)

    @property
    def weekly_times(self) -> int:
        return self.get('weekly_times', 2)

    @weekly_times.setter
    def weekly_times(self, new_value: int):
        self.update('weekly_times', new_value)

    @property
    def extra_task(self) -> str:
        return self.get('extra_task', HollowZeroExtraTask.LEVEL_3.value.value)

    @extra_task.setter
    def extra_task(self, new_value: str):
        self.update('extra_task', new_value)