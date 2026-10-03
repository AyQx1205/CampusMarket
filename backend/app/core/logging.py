"""loguru 日志配置。

- 统一在应用启动时调用 setup_logging()。
- 通过 InterceptHandler 把标准库 logging（uvicorn、sqlalchemy 等）的输出
  全部接管到 loguru，避免双份日志格式。
- 开发期输出到 stdout；生产可按需增加文件 sink（此处预留注释）。
"""

import inspect
import logging
import sys

from loguru import logger

from app.core.config import settings


class InterceptHandler(logging.Handler):
    """标准库 logging -> loguru 的桥接处理器（loguru 官方推荐方案）。"""

    def emit(self, record: logging.LogRecord) -> None:
        # 还原调用方在应用代码中的位置，而非拦截层
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    """初始化 loguru：清空默认 sink，接管标准库 logging。"""
    # 移除 loguru 默认 handler
    logger.remove()

    # 控制台输出；生产环境可将 sink 换成文件并做轮转（保留扩展点）
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.DEBUG else "INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        backtrace=True,
        diagnose=settings.DEBUG,
        enqueue=True,  # 多进程/异步下线程安全
    )

    # 接管标准库 logging 的所有输出（含 uvicorn / sqlalchemy）
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        _logger = logging.getLogger(name)
        _logger.handlers = [InterceptHandler()]
        _logger.propagate = False
