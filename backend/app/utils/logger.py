import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

class LogColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ColoredFormatter(logging.Formatter):
    

    FORMATS = {
        logging.DEBUG: LogColors.OKCYAN + "%(levelname)s" + LogColors.ENDC + " - %(name)s - %(message)s",
        logging.INFO: LogColors.OKGREEN + "%(levelname)s" + LogColors.ENDC + " - %(name)s - %(message)s",
        logging.WARNING: LogColors.WARNING + "%(levelname)s" + LogColors.ENDC + " - %(name)s - %(message)s",
        logging.ERROR: LogColors.FAIL + "%(levelname)s" + LogColors.ENDC + " - %(name)s - %(message)s",
        logging.CRITICAL: LogColors.FAIL + LogColors.BOLD + "%(levelname)s" + LogColors.ENDC + " - %(name)s - %(message)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

def setup_logger(name: str, level=logging.DEBUG) -> logging.Logger:
    
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    log_file = LOGS_DIR / f"algoinsight_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColoredFormatter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_logger(component: str) -> logging.Logger:
    
    return setup_logger(f"AlgoInsight.{component}")

def log_error_with_context(logger: logging.Logger, error: Exception, context: dict = None):
    
    import traceback

    logger.error(f"Exception: {str(error)}")
    logger.error(f"Type: {type(error).__name__}")

    if context:
        logger.error(f"Context: {context}")

    logger.debug(f"Traceback:\n{traceback.format_exc()}")

def log_performance(logger: logging.Logger):
    
    import time
    import functools

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            logger.debug(f"Starting {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start
                logger.info(f"✓ {func.__name__} completed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"✗ {func.__name__} failed after {elapsed:.2f}s: {str(e)}")
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            logger.debug(f"Starting {func.__name__}")
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                logger.info(f"✓ {func.__name__} completed in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"✗ {func.__name__} failed after {elapsed:.2f}s: {str(e)}")
                raise

        if hasattr(func, '__code__') and func.__code__.co_flags & 0x100:
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

def print_startup_banner():
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     █████╗ ██╗      ██████╗  ██████╗ ██╗███╗   ██╗███████╗   ║
    ║    ██╔══██╗██║     ██╔════╝ ██╔═══██╗██║████╗  ██║██╔════╝   ║
    ║    ███████║██║     ██║  ███╗██║   ██║██║██╔██╗ ██║███████╗   ║
    ║    ██╔══██║██║     ██║   ██║██║   ██║██║██║╚██╗██║╚════██║   ║
    ║    ██║  ██║███████╗╚██████╔╝╚██████╔╝██║██║ ╚████║███████║   ║
    ║    ╚═╝  ╚═╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝╚══════╝   ║
    ║                     I N S I G H T                             ║
    ║                                                               ║
    ║         DSA Learning & Visualization Platform                 ║
    ║                    v2.6.0-stable                              ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(LogColors.OKGREEN + banner + LogColors.ENDC)
