import time
import ctypes
import cv2
import numpy as np
import pyautogui
from PIL.Image import Image
from cv2.typing import MatLike
from functools import lru_cache
from pynput import keyboard
from typing import Optional

from one_dragon.base.controller.controller_base import ControllerBase
from one_dragon.base.controller.pc_button import pc_button_utils
from one_dragon.base.controller.pc_button.ds4_button_controller import Ds4ButtonController
from one_dragon.base.controller.pc_button.keyboard_mouse_controller import KeyboardMouseController
from one_dragon.base.controller.pc_button.pc_button_controller import PcButtonController
from one_dragon.base.controller.pc_button.xbox_button_controller import XboxButtonController
from one_dragon.base.controller.pc_game_window import PcGameWindow
from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils.log_utils import log


class PcControllerBase(ControllerBase):

    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    def __init__(self, win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        ControllerBase.__init__(self)
        self.standard_width: int = standard_width
        self.standard_height: int = standard_height
        self.game_win: PcGameWindow = PcGameWindow(win_title,
                                                   standard_width=standard_width, standard_height=standard_height)

        self.keyboard_controller: KeyboardMouseController = KeyboardMouseController()
        self.xbox_controller: Optional[XboxButtonController] = None
        self.ds4_controller: Optional[Ds4ButtonController] = None

        self.btn_controller: PcButtonController = self.keyboard_controller
        self.sct = None

    def init_before_context_run(self) -> bool:
        if self.sct is not None:  # 新一次app前 先关闭上一个
            try:
                self.sct.close()
            except Exception as e:
                log.error('关闭上一个截图工具失败: %s', str(e))
        try:
            import mss
            self.sct = mss.mss()
        except Exception as e:
            log.error('初始化截图工具失败: %s', str(e))
        self.active_window()

        return True

    def active_window(self) -> None:
        """
        前置窗口并检查分辨率和全屏状态，未检测到窗口时给出提示
        """
        self.game_win.init_win()

        # 检查是否检测到窗口
        if not self.game_win.is_win_valid:
            log.warning("未检测到游戏窗口，请确认游戏已启动。")
            return

        # 检查游戏窗口分辨率和全屏状态
        if not self.game_win.check_resolution_and_fullscreen():
            log.warning("游戏窗口的分辨率或全屏设置有潜在问题。")
        
        self.game_win.active()

    def enable_xbox(self):
        try:
            if pc_button_utils.is_vgamepad_installed():
                if self.xbox_controller is None:
                    self.xbox_controller = XboxButtonController()
                self.btn_controller = self.xbox_controller
                self.btn_controller.reset()
        except Exception as e:
            log.error('启用 Xbox 控制器失败: %s', str(e))

    def enable_ds4(self):
        try:
            if pc_button_utils.is_vgamepad_installed():
                if self.ds4_controller is None:
                    self.ds4_controller = Ds4ButtonController()
                self.btn_controller = self.ds4_controller
                self.btn_controller.reset()
        except Exception as e:
            log.error('启用 DS4 控制器失败: %s', str(e))

    def enable_keyboard(self):
        try:
            self.btn_controller = self.keyboard_controller
        except Exception as e:
            log.error('启用键盘控制器失败: %s', str(e))

    @property
    def is_game_window_ready(self) -> bool:
        """
        游戏窗口是否已经准备好了
        :return:
        """
        return self.game_win.is_win_valid

    def click(self, pos: Point = None, press_time: float = 0, pc_alt: bool = False) -> bool:
        """
        点击位置
        :param pos: 游戏中的位置 (x,y)
        :param press_time: 大于0时长按若干秒
        :param pc_alt: 只在PC端有用 使用ALT键进行点击
        :return: 不在窗口区域时不点击 返回False
        """
        try:
            click_pos: Point
            if pos is not None:
                click_pos: Point = self.game_win.game2win_pos(pos)
                if click_pos is None:
                    log.error('点击非游戏窗口区域 (%s)', pos)
                    return False
            else:
                click_pos = get_current_mouse_pos()

            if pc_alt:
                self.keyboard_controller.keyboard.press(keyboard.Key.alt)
                time.sleep(0.2)
            win_click(click_pos, press_time=press_time)
            if pc_alt:
                self.keyboard_controller.keyboard.release(keyboard.Key.alt)
            return True
        except Exception as e:
            log.error('点击失败: %s', str(e))
            return False

    def get_screenshot(self, independent: bool = False) -> MatLike:
        """
        截图 如果分辨率和默认不一样则进行缩放
        :return: 截图
        """
        try:
            rect: Rect = self.game_win.win_rect

            left = rect.x1
            top = rect.y1
            width = rect.width
            height = rect.height

            if self.sct is not None:
                monitor = {"top": top, "left": left, "width": width, "height": height}
                if independent:
                    try:
                        import mss
                        with mss.mss() as sct:
                            screenshot = cv2.cvtColor(np.array(sct.grab(monitor)), cv2.COLOR_BGRA2RGB)
                    except Exception as e:
                        log.error('独立截图失败: %s', str(e))
                        screenshot = np.zeros((height, width, 3), dtype=np.uint8)
                else:
                    screenshot = cv2.cvtColor(np.array(self.sct.grab(monitor)), cv2.COLOR_BGRA2RGB)
            else:
                img: Image = pyautogui.screenshot(region=(left, top, width, height))
                screenshot = np.array(img)

            if self.game_win.is_win_scale:
                result = cv2.resize(screenshot, (self.standard_width, self.standard_height))
            else:
                result = screenshot

            return result
        except Exception as e:
            log.error('截图失败: %s', str(e))
            return np.zeros((self.standard_height, self.standard_width, 3), dtype=np.uint8)

    def scroll(self, down: int, pos: Point = None):
        """
        向下滚动
        :param down: 负数时为相上滚动
        :param pos: 滚动位置 默认分辨率下的游戏窗口里的坐标
        :return:
        """
        try:
            if pos is None:
                pos = get_current_mouse_pos()
            win_pos = self.game_win.game2win_pos(pos)
            win_scroll(down, win_pos)
        except Exception as e:
            log.error('滚动失败: %s', str(e))

    def drag_to(self, end: Point, start: Point = None, duration: float = 0.5):
        """
        按住拖拽
        :param end: 拖拽目的点
        :param start: 拖拽开始点
        :param duration: 拖拽持续时间
        :return:
        """
        try:
            from_pos: Point
            if start is None:
                from_pos = get_current_mouse_pos()
            else:
                from_pos = self.game_win.game2win_pos(start)

            to_pos = self.game_win.game2win_pos(end)
            drag_mouse(from_pos, to_pos, duration=duration)
        except Exception as e:
            log.error('拖拽失败: %s', str(e))

    def close_game(self):
        """
        关闭游戏
        :return:
        """
        try:
            self.game_win.win.close()
            log.info('关闭游戏成功')
        except Exception as e:
            log.error('关闭游戏失败: %s', str(e))

    def input_str(self, to_input: str, interval: float = 0.1):
        """
        输入文本 需要自己先选择好输入框
        :param to_input: 文本
        :return:
        """
        try:
            self.keyboard_controller.keyboard.type(to_input)
        except Exception as e:
            log.error('输入文本失败: %s', str(e))


def win_click(pos: Point = None, press_time: float = 0, primary: bool = True):
    """
    点击鼠标
    :param pos: 屏幕坐标
    :param press_time: 按住时间
    :param primary: 是否点击鼠标主要按键（通常是左键）
    :return:
    """
    try:
        btn = pyautogui.PRIMARY if primary else pyautogui.SECONDARY
        if pos is None:
            pos = get_current_mouse_pos()
        if press_time > 0:
            pyautogui.moveTo(pos.x, pos.y)
            pyautogui.mouseDown(button=btn)
            time.sleep(press_time)
            pyautogui.mouseUp(button=btn)
        else:
            pyautogui.click(pos.x, pos.y, button=btn)
    except Exception as e:
        log.error('鼠标点击失败: %s', str(e))


def win_scroll(clicks: int, pos: Point = None):
    """
    向下滚动
    :param clicks: 负数时为相上滚动
    :param pos: 滚动位置 不传入时为鼠标当前位置
    :return:
    """
    try:
        if pos is not None:
            pyautogui.moveTo(pos.x, pos.y)
        d = 2000 if get_mouse_sensitivity() <= 10 else 1000
        pyautogui.scroll(-d * clicks, pos.x, pos.y)
    except Exception as e:
        log.error('鼠标滚动失败: %s', str(e))


@lru_cache
def get_mouse_sensitivity():
    """
    获取鼠标灵敏度
    :return:
    """
    try:
        user32 = ctypes.windll.user32
        speed = ctypes.c_int()
        user32.SystemParametersInfoA(0x0070, 0, ctypes.byref(speed), 0)
        return speed.value
    except Exception as e:
        log.error('获取鼠标灵敏度失败: %s', str(e))
        return 10  # 返回一个默认值以防止程序崩溃


def drag_mouse(start: Point, end: Point, duration: float = 0.5):
    """
    按住鼠标左键进行画面拖动
    :param start: 原位置
    :param end: 拖动位置
    :param duration: 拖动鼠标到目标位置，持续秒数
    :return:
    """
    try:
        pyautogui.moveTo(start.x, start.y)  # 将鼠标移动到起始位置
        pyautogui.dragTo(end.x, end.y, duration=duration)
    except Exception as e:
        log.error('拖动鼠标失败: %s', str(e))


def get_current_mouse_pos() -> Point:
    """
    获取鼠标当前坐标
    :return:
    """
    try:
        pos = pyautogui.position()
        return Point(pos.x, pos.y)
    except Exception as e:
        log.error('获取鼠标位置失败: %s', str(e))
        return Point(0, 0)  # 返回一个默认值以防止程序崩溃
