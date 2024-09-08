import ctypes
from ctypes.wintypes import RECT
import pyautogui
from pygetwindow import Win32Window
from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils.log_utils import log
import win32api  # 用于获取屏幕分辨率
import win32con
import win32gui

class PcGameWindow:

    def __init__(self, win_title: str,
                 standard_width: int = 1920,
                 standard_height: int = 1080):
        self.win_title: str = win_title
        self.standard_width: int = standard_width
        self.standard_height: int = standard_height
        self.standard_game_rect: Rect = Rect(0, 0, standard_width, standard_height)

        self.win: Win32Window = None
        self.hWnd = None

        self.init_win()

    def init_win(self) -> None:
        """
        初始化窗口，若未检测到窗口则给出提示信息
        :return:
        """
        self.win = None
        self.hWnd = None
        try:
            windows = pyautogui.getWindowsWithTitle(self.win_title)
            if len(windows) > 0:
                for win in windows:
                    if win.title == self.win_title:
                        self.win = win
                        self.hWnd = win._hWnd
            else:
                log.warning(f"未检测到名为 '{self.win_title}' 的游戏窗口，请确认游戏已启动。")
        except Exception as e:
            log.error(f"初始化窗口失败: {e}")

    def check_resolution_and_fullscreen(self) -> bool:
        """
        检查当前游戏窗口是否是16:9的分辨率，并处理全屏模式
        """
        try:
            screen_resolutions = [(1920, 1080), (2560, 1440), (3840, 2160)]
            game_rect = self.win_rect

            if game_rect is None:  # 如果 game_rect 是 None，表示窗口未初始化成功
                log.error("无法获取游戏窗口信息，窗口未正确初始化。")
                return False
            
            # 检查窗口是否是16:9的分辨率
            current_res = (game_rect.width, game_rect.height)
            if current_res not in screen_resolutions:
                log.warning(f"警告: 当前游戏分辨率 {current_res} 可能有问题，建议使用16:9分辨率。")
                return False

            # 检查是否是全屏，并且显示器的分辨率是否也是16:9
            if self.win.isMaximized:
                screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                if (screen_width, screen_height) not in screen_resolutions:
                    log.warning(f"警告: 当前显示器分辨率 {(screen_width, screen_height)} 不是16:9，全屏模式可能无法正确显示。")
                    return False

            log.info(f"当前游戏分辨率为 {current_res}，符合16:9要求。")
            return True
        except Exception as e:
            log.error(f"检查分辨率和全屏模式失败: {e}")
            return False

    @property
    def is_win_valid(self) -> bool:
        """
        当前窗口是否正常
        :return:
        """
        try:
            return self.win is not None and self.hWnd is not None and ctypes.windll.user32.IsWindow(self.hWnd) != 0
        except Exception as e:
            log.error(f"检测窗口有效性失败: {e}")
            return False

    @property
    def is_win_active(self) -> bool:
        """
        是否当前激活的窗口
        :return:
        """
        try:
            return self.win.isActive
        except Exception as e:
            log.error(f"检测窗口激活状态失败: {e}")
            return False

    @property
    def win_rect(self) -> Rect:
        """
        获取游戏窗口在桌面上面的位置
        Win32Window 里是整个window的信息 参考源码获取里面client部分的
        :return: 游戏窗口信息，如果窗口未初始化则返回 None
        """
        try:
            if self.hWnd is None:
                return None  # 如果 hWnd 是 None，返回 None
            client_rect = RECT()
            ctypes.windll.user32.GetClientRect(self.hWnd, ctypes.byref(client_rect))
            left_top_pos = ctypes.wintypes.POINT(client_rect.left, client_rect.top)
            ctypes.windll.user32.ClientToScreen(self.hWnd, ctypes.byref(left_top_pos))
            return Rect(left_top_pos.x, left_top_pos.y, left_top_pos.x + client_rect.right, left_top_pos.y + client_rect.bottom)
        except Exception as e:
            log.error(f"获取游戏窗口矩形失败: {e}")
            return None

    @property
    def is_win_scale(self) -> bool:
        """
        判断窗口是否需要缩放。如果当前窗口分辨率与标准分辨率不符，则需要缩放。
        :return: 是否需要缩放
        """
        try:
            game_rect = self.win_rect
            if game_rect is None:
                return False  # 如果未获取到窗口信息，则不缩放
            return game_rect.width != self.standard_width or game_rect.height != self.standard_height
        except Exception as e:
            log.error(f"判断窗口缩放失败: {e}")
            return False

    def active(self) -> bool:
        """
        显示并激活当前窗口
        :return: True 表示成功激活窗口, False 表示失败
        """
        try:
            if self.win is None:
                log.error("无法激活窗口，未检测到有效的游戏窗口。")
                return False

            if self.is_win_active:
                return True
            
            self.win.restore()
            self.win.activate()
            log.info("游戏窗口已成功激活。")
            return True
        except Exception as e:
            log.error(f"激活游戏窗口失败: {e}")
            return False

    def get_scaled_game_pos(self, game_pos: Point) -> Point:
        """
        获取当前分辨率下游戏窗口里的坐标
        :param game_pos: 默认分辨率下的游戏窗口里的坐标
        :return: 当前分辨率下的游戏窗口里坐标
        """
        try:
            if self.win is None:
                return None
            rect = self.win_rect
            xs = 1 if rect.width == self.standard_width else rect.width * 1.0 / self.standard_width
            ys = 1 if rect.height == self.standard_height else rect.height * 1.0 / self.standard_height
            s_pos = Point(game_pos.x * xs, game_pos.y * ys)
            return s_pos if self.is_valid_game_pos(game_pos, self.standard_game_rect) else None
        except Exception as e:
            log.error(f"获取缩放游戏坐标失败: {e}")
            return None

    def is_valid_game_pos(self, s_pos: Point, rect: Rect = None) -> bool:
        """
        判断游戏中坐标是否在游戏窗口内
        :param s_pos: 游戏中坐标 已经缩放
        :param rect: 窗口位置信息
        :return: 是否在游戏窗口内
        """
        try:
            if self.win is None:
                return False
            if rect is None:
                rect = self.standard_game_rect
            return 0 <= s_pos.x < rect.width and 0 <= s_pos.y < rect.height
        except Exception as e:
            log.error(f"判断游戏坐标有效性失败: {e}")
            return False

    def game2win_pos(self, game_pos: Point) -> Point:
        """
        获取在屏幕中的坐标
        :param game_pos: 默认分辨率下的游戏窗口里的坐标
        :return: 当前分辨率下的屏幕中的坐标
        """
        try:
            if self.win is None:
                return None
            rect = self.win_rect
            gp: Point = self.get_scaled_game_pos(game_pos)
            # 缺少一个屏幕边界判断 游戏窗口拖动后可能会超出整个屏幕
            return rect.left_top + gp if gp is not None else None
        except Exception as e:
            log.error(f"获取屏幕坐标失败: {e}")
            return None

    def get_dpi(self):
        try:
            if self.hWnd is None:
                return None
            return ctypes.windll.user32.GetDpiForWindow(self.hWnd)
        except Exception as e:
            log.error(f"获取 DPI 失败: {e}")
            return None
