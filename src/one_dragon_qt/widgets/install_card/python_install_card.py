import os
from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIcon, FluentThemeColor
from typing import Tuple

from one_dragon.base.operation.one_dragon_env_context import OneDragonEnvContext
from one_dragon_qt.widgets.install_card.base_install_card import BaseInstallCard
from one_dragon.utils.i18_utils import gt


class PythonInstallCard(BaseInstallCard):

    def __init__(self, ctx: OneDragonEnvContext):
        BaseInstallCard.__init__(
            self,
            ctx=ctx,
            title_cn='Python虚拟环境',
            install_method=ctx.python_service.uv_install_python_venv,
        )

    def after_progress_done(self, success: bool, msg: str) -> None:
        """
        安装结束的回调，由子类自行实现
        :param success: 是否成功
        :param msg: 提示信息
        :return:
        """
        if success:
            self.check_and_update_display()
        else:
            self.update_display(FluentIcon.INFO.icon(color=FluentThemeColor.RED.value), gt(msg, 'ui'))

    def get_display_content(self) -> Tuple[QIcon, str]:
        """
        获取需要显示的状态，由子类自行实现
        :return: 显示的图标、文本
        """
        python_path = self.ctx.env_config.python_path

        if python_path == '':
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('未安装', 'ui')
        elif not os.path.exists(python_path):
            icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
            msg = gt('文件不存在', 'ui') + ' ' + python_path
        else:
            python_version = self.ctx.python_service.get_python_version()
            if python_version is None:
                icon = FluentIcon.INFO.icon(color=FluentThemeColor.RED.value)
                msg = gt('无法获取Python版本', 'ui') + ' ' + python_path
            elif python_version != self.ctx.project_config.python_version and python_version != self.ctx.project_config.uv_python_version:
                icon = FluentIcon.INFO.icon(color=FluentThemeColor.GOLD.value)
                msg = (f"{gt('当前版本', 'ui')}: {python_version}; {gt('建议版本', 'ui')}: {self.ctx.project_config.python_version}"
                       + ' ' + python_path)
            else:
                icon = FluentIcon.INFO.icon(color=FluentThemeColor.DEFAULT_BLUE.value)
                msg = f"{gt('已安装', 'ui')}" + ' ' + python_path

        return icon, msg
