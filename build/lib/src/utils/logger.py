import logging
from enum import Enum

class LogLevel(Enum):
    FATAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARN = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    TRACE = logging.DEBUG - 5  # Custom level for TRACE
    SILENT = logging.NOTSET

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        # Create logger
        self._logger = logging.getLogger('reclaim')
        
        # Create console handler and set formatter
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        self._logger.addHandler(console_handler)
        
        # Set default level
        self._logger.setLevel(logging.INFO)

    @staticmethod
    def set_log_level(level: LogLevel):
        logger = logging.getLogger('reclaim')
        if level == LogLevel.SILENT:
            logger.setLevel(logging.CRITICAL + 1)  # Set to higher than CRITICAL
        else:
            logger.setLevel(level.value)

    def fatal(self, message, error=None, stack_trace=None):
        extra_info = f" - Error: {error}" if error else ""
        extra_info += f"\nStack trace: {stack_trace}" if stack_trace else ""
        self._logger.critical(f"{message}{extra_info}")

    def error(self, message, error=None, stack_trace=None):
        extra_info = f" - Error: {error}" if error else ""
        extra_info += f"\nStack trace: {stack_trace}" if stack_trace else ""
        self._logger.error(f"{message}{extra_info}")

    def warn(self, message, error=None, stack_trace=None):
        extra_info = f" - Error: {error}" if error else ""
        extra_info += f"\nStack trace: {stack_trace}" if stack_trace else ""
        self._logger.warning(f"{message}{extra_info}")

    def info(self, message, error=None, stack_trace=None):
        extra_info = f" - Error: {error}" if error else ""
        extra_info += f"\nStack trace: {stack_trace}" if stack_trace else ""
        self._logger.info(f"{message}{extra_info}")

    def debug(self, message, error=None, stack_trace=None):
        extra_info = f" - Error: {error}" if error else ""
        extra_info += f"\nStack trace: {stack_trace}" if stack_trace else ""
        self._logger.debug(f"{message}{extra_info}")

    def trace(self, message, error=None, stack_trace=None):
        extra_info = f" - Error: {error}" if error else ""
        extra_info += f"\nStack trace: {stack_trace}" if stack_trace else ""
        self._logger.log(LogLevel.TRACE.value, f"{message}{extra_info}")

# Create a global instance of the logger
logger = Logger()
