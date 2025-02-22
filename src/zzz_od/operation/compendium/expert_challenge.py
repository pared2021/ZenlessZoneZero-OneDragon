"""
专业挑战室自动战斗模块。
提供专业挑战室的自动战斗功能，包括战斗状态检测、失败判断等。
"""

import time

from typing import Optional, ClassVar

from one_dragon.base.operation.operation import Operation
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from zzz_od.application.charge_plan.charge_plan_config import ChargePlanItem
from zzz_od.auto_battle import auto_battle_utils
from zzz_od.auto_battle.auto_battle_operator import AutoBattleOperator
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.challenge_mission.check_next_after_battle import ChooseNextOrFinishAfterBattle
from zzz_od.operation.choose_predefined_team import ChoosePredefinedTeam
from zzz_od.operation.deploy import Deploy
from zzz_od.operation.exit_in_battle import ExitInBattle
from zzz_od.operation.zzz_operation import ZOperation
from zzz_od.screen_area.screen_normal_world import ScreenNormalWorldEnum


class ExpertChallenge(ZOperation):
    """
    专业挑战室操作类。
    包含战斗状态检测、失败判断等功能。
    """

    STATUS_CHARGE_NOT_ENOUGH: ClassVar[str] = '电量不足'
    STATUS_CHARGE_ENOUGH: ClassVar[str] = '电量充足'
    STATUS_BATTLE_FAILED: ClassVar[str] = '战斗失败'

    def __init__(self, ctx: ZContext, plan: ChargePlanItem,
                 can_run_times: Optional[int] = None,
                 need_check_power: bool = False):
        """
        初始化专业挑战室操作。
        :param ctx: 游戏上下文
        :param plan: 充值计划项
        :param can_run_times: 可运行次数
        :param need_check_power: 是否需要检查体力
        """
        ZOperation.__init__(
            self, ctx,
            op_name=f'{gt("专业挑战室")} {gt(plan.mission_type_name)}'
        )

        self.plan: ChargePlanItem = plan
        self.need_check_power: bool = need_check_power
        self.can_run_times: int = can_run_times
        self.charge_left: Optional[int] = None
        self.charge_need: Optional[int] = None

        self.auto_op: Optional[AutoBattleOperator] = None

    @operation_node(name='等待入口加载', is_start_node=True, node_max_retry_times=60)
    def wait_entry_load(self) -> OperationRoundResult:
        """
        等待入口加载。
        :return: 操作结果
        """
        screen = self.screenshot()
        return self.round_by_find_area(
            screen, '实战模拟室', '挑战等级',
            success_wait=1, retry_wait=1
        )

    @node_from(from_name='等待入口加载')
    @operation_node(name='识别电量')
    def check_charge(self) -> OperationRoundResult:
        """
        识别电量。
        :return: 操作结果
        """
        if not self.need_check_power:
            if self.can_run_times > 0:
                return self.round_success(ExpertChallenge.STATUS_CHARGE_ENOUGH)
            else:
                return self.round_success(ExpertChallenge.STATUS_CHARGE_NOT_ENOUGH)
        screen = self.screenshot()

        area = self.ctx.screen_loader.get_area('专业挑战室', '剩余电量')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result = self.ctx.ocr.run_ocr_single_line(part)
        self.charge_left = str_utils.get_positive_digits(ocr_result, None)
        if self.charge_left is None:
            return self.round_retry(status='识别 %s 失败' % '剩余电量', wait=1)

        area = self.ctx.screen_loader.get_area('专业挑战室', '需要电量')
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_result = self.ctx.ocr.run_ocr_single_line(part)
        self.charge_need = str_utils.get_positive_digits(ocr_result, None)
        if self.charge_need is None:
            return self.round_retry(status='识别 %s 失败' % '需要电量', wait=1)

        log.info('所需电量 %d 剩余电量 %d', self.charge_need, self.charge_left)
        if self.charge_need > self.charge_left:
            return self.round_success(ExpertChallenge.STATUS_CHARGE_NOT_ENOUGH)

        self.can_run_times = self.charge_left // self.charge_need
        max_need_run_times = self.plan.plan_times - self.plan.run_times

        if self.can_run_times > max_need_run_times:
            self.can_run_times = max_need_run_times

        return self.round_success(ExpertChallenge.STATUS_CHARGE_ENOUGH)

    @node_from(from_name='识别电量', status=STATUS_CHARGE_ENOUGH)
    @operation_node(name='下一步', node_max_retry_times=10)  # 部分机器加载较慢 延长出战的识别时间
    def click_next(self) -> OperationRoundResult:
        """
        点击下一步。
        :return: 操作结果
        """
        screen = self.screenshot()

        # 防止前面电量识别错误
        result = self.round_by_find_area(screen, '实战模拟室', '恢复电量')
        if result.is_success:
            return self.round_success(status=ExpertChallenge.STATUS_CHARGE_NOT_ENOUGH)

        # 点击直到出战按钮出现
        result = self.round_by_find_area(screen, '实战模拟室', '出战')
        if result.is_success:
            return self.round_success(result.status)

        result = self.round_by_find_and_click_area(screen, '实战模拟室', '下一步')
        if result.is_success:
            time.sleep(0.5)
            self.ctx.controller.mouse_move(ScreenNormalWorldEnum.UID.value.center)  # 点击后 移开鼠标 防止识别不到出战
            return self.round_wait(result.status, wait=0.5)

        return self.round_retry(result.status, wait=1)

    @node_from(from_name='下一步', status='出战')
    @operation_node(name='选择预备编队')
    def choose_predefined_team(self) -> OperationRoundResult:
        """
        选择预备编队。
        :return: 操作结果
        """
        if self.plan.predefined_team_idx == -1:
            return self.round_success('无需选择预备编队')
        else:
            op = ChoosePredefinedTeam(self.ctx, [self.plan.predefined_team_idx])
            return self.round_by_op_result(op.execute())

    @node_from(from_name='选择预备编队')
    @operation_node(name='出战')
    def deploy(self) -> OperationRoundResult:
        """
        出战。
        :return: 操作结果
        """
        op = Deploy(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='出战')
    @node_from(from_name='判断下一次', status='战斗结果-再来一次')
    @operation_node(name='加载自动战斗指令')
    def init_auto_battle(self) -> OperationRoundResult:
        """
        加载自动战斗指令。
        :return: 操作结果
        """
        if self.plan.predefined_team_idx == -1:
            auto_battle = self.plan.auto_battle_config
        else:
            team_list = self.ctx.team_config.team_list
            auto_battle = team_list[self.plan.predefined_team_idx].auto_battle

        return auto_battle_utils.load_auto_op(self, 'auto_battle', auto_battle)

    @node_from(from_name='加载自动战斗指令')
    @operation_node(name='等待战斗画面加载', node_max_retry_times=60)
    def wait_battle_screen(self) -> OperationRoundResult:
        """
        等待战斗画面加载。
        :return: 操作结果
        """
        screen = self.screenshot()
        result = self.round_by_find_area(screen, '战斗画面', '按键-普通攻击', retry_wait_round=1)
        return result

    @node_from(from_name='等待战斗画面加载')
    @operation_node(name='向前移动准备战斗')
    def move_to_battle(self) -> OperationRoundResult:
        """
        向前移动准备战斗。
        :return: 操作结果
        """
        self.ctx.controller.move_w(press=True, press_time=1, release=True)
        self.auto_op.start_running_async()
        return self.round_success()

    @node_from(from_name='向前移动准备战斗')
    @operation_node(name='自动战斗', mute=True, timeout_seconds=600)
    def auto_battle(self) -> OperationRoundResult:
        """
        自动战斗。
        :return: 操作结果
        """
        if self.auto_op.auto_battle_context.last_check_end_result is not None:
            auto_battle_utils.stop_running(self.auto_op)
            return self.round_success(status=self.auto_op.auto_battle_context.last_check_end_result)
        now = time.time()
        screen = self.screenshot()

        self.auto_op.auto_battle_context.check_battle_state(screen, now, check_battle_end_normal_result=True)

        return self.round_wait(wait=self.ctx.battle_assistant_config.screenshot_interval)

    @node_from(from_name='自动战斗')
    @operation_node(name='战斗结束')
    def after_battle(self) -> OperationRoundResult:
        """
        战斗结束。
        :return: 操作结果
        """
        screen = self.screenshot()
        now = time.time()
        
        # 检查战斗是否失败
        if self.auto_op.auto_battle_context.check_battle_fail(screen, now):
            log.info('战斗失败')
            return self.round_success(self.STATUS_BATTLE_FAILED)
        
        # 原有的成功处理逻辑
        self.can_run_times -= 1
        self.ctx.charge_plan_config.add_plan_run_times(self.plan)
        return self.round_success()

    @node_from(from_name='战斗结束')
    @operation_node(name='判断下一次')
    def check_next(self) -> OperationRoundResult:
        """
        检查是否继续下一轮。
        :return: 操作结果
        """
        op = ChooseNextOrFinishAfterBattle(self.ctx, self.can_run_times > 0)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='识别电量', success=False)
    @operation_node(name='识别电量失败')
    def check_charge_fail(self) -> OperationRoundResult:
        """
        识别电量失败。
        :return: 操作结果
        """
        return self.round_success(ExpertChallenge.STATUS_CHARGE_NOT_ENOUGH)

    @node_from(from_name='自动战斗', success=False, status=Operation.STATUS_TIMEOUT)
    @operation_node(name='战斗超时')
    def battle_timeout(self) -> OperationRoundResult:
        """
        战斗超时。
        :return: 操作结果
        """
        auto_battle_utils.stop_running(self.auto_op)
        op = ExitInBattle(self.ctx, '战斗-挑战结果-失败', '按钮-退出')
        return self.round_by_op_result(op.execute())

    @node_from(from_name='战斗超时')
    @operation_node(name='点击挑战结果退出')
    def click_result_exit(self) -> OperationRoundResult:
        """
        点击挑战结果退出。
        :return: 操作结果
        """
        return self.round_by_find_and_click_area(screen_name='战斗-挑战结果-失败', area_name='按钮-退出',
                                                 until_not_find_all=[('战斗-挑战结果-失败', '按钮-退出')],
                                                 success_wait=1, retry_wait=1)

    def handle_pause(self):
        """
        处理暂停。
        """
        if self.auto_op is not None:
            self.auto_op.stop_running()

    def handle_resume(self):
        """
        处理恢复。
        """
        auto_battle_utils.resume_running(self.auto_op)

    def after_operation_done(self, result: OperationResult):
        """
        操作完成后。
        :param result: 操作结果
        """
        ZOperation.after_operation_done(self, result)
        if self.auto_op is not None:
            self.auto_op.dispose()
            self.auto_op = None


def __debug():
    ctx = ZContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.start_running()
    op = ExpertChallenge(ctx, ChargePlanItem(
        category_name='专业挑战室',
        mission_type_name='恶名·杜拉罕',
        auto_battle_config='全配队通用',
        predefined_team_idx=-1
    ))
    op.execute()


if __name__ == '__main__':
    __debug()
