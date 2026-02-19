import logging
import os
import datetime
import importlib
import re

class DWToolLogger:
    """
    Custom logger for DW Tool application
    Logs format: datetime : user_name : error/warning/info : log details
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DWToolLogger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance
    
    def _setup_logger(self):
        """Set up the logger with the required format"""
        self.logger = logging.getLogger('dwtool')
        
        # Read log level from environment variable, default to INFO
        log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
        
        # Map string to logging level constant
        log_level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        # Get the log level, default to INFO if invalid
        log_level = log_level_map.get(log_level_str, logging.INFO)
        
        # Set logger level
        self.logger.setLevel(log_level)
        
        # Prevent duplicate log entries
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Create logs directory if it doesn't exist
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dwtool.log')
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        # Set file handler level to match logger level
        file_handler.setLevel(log_level)
        
        # Create formatter - we'll handle the custom format in our methods
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Initialize filter patterns
        self.filter_patterns = [
            r'Request: \w+ /.*',  # Filter out API request logs
            r'Response: \d+',     # Filter out API response logs
        ]
    
    def _should_log(self, message):
        """Check if the message should be logged based on filter patterns"""
        for pattern in self.filter_patterns:
            if re.search(pattern, message):
                return False
        return True
    
    def _get_username(self):
        """Get the current user's username from Flask's g object or default to 'system'"""
        try:
            # Import Flask's g object lazily to avoid circular imports
            from flask import g
            if hasattr(g, 'user') and g.user:
                return g.user.get('username', 'system')
        except (ImportError, RuntimeError):
            # Flask app context might not be available or Flask might not be imported
            pass
        return 'system'
    
    def _format_message(self, level, message):
        """Format the log message according to requirements"""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        username = self._get_username()
        return f"{timestamp} : {username} : {level} : {message}"
    
    def debug(self, message, *args):
        """Log a debug message. Supports format strings: debug("format %s", arg)"""
        if args:
            message = message % args if '%' in message else message.format(*args)
        formatted_message = self._format_message('debug', message)
        if self._should_log(message):
            self.logger.debug(formatted_message)
    
    def info(self, message, *args):
        """Log an info message. Supports format strings: info("format %s", arg)"""
        if args:
            message = message % args if '%' in message else message.format(*args)
        formatted_message = self._format_message('info', message)
        if self._should_log(message):
            self.logger.info(formatted_message)
    
    def warning(self, message, *args):
        """Log a warning message. Supports format strings: warning("format %s", arg)"""
        if args:
            message = message % args if '%' in message else message.format(*args)
        formatted_message = self._format_message('warning', message)
        if self._should_log(message):
            self.logger.warning(formatted_message)
    
    def error(self, message, *args, **kwargs):
        """
        Log an error message. Supports format strings: error("format %s", arg)
        exc_info parameter is ignored - no tracebacks are included by default
        """
        if args:
            message = message % args if '%' in message else message.format(*args)
        formatted_message = self._format_message('error', message)
        # Always set exc_info to False to avoid tracebacks
        if self._should_log(message):
            self.logger.error(formatted_message, exc_info=False)
    
    def exception(self, message):
        """Log an exception message without traceback"""
        formatted_message = self._format_message('error', message)
        # Use error instead of exception to avoid traceback
        if self._should_log(message):
            self.logger.error(formatted_message)
    
    def add_filter_pattern(self, pattern):
        """Add a regex pattern to filter out log messages"""
        self.filter_patterns.append(pattern)
    
    def remove_filter_pattern(self, pattern):
        """Remove a regex pattern from the filter"""
        if pattern in self.filter_patterns:
            self.filter_patterns.remove(pattern)

# Create a singleton instance
logger = DWToolLogger()

# Export the logger functions for easy import
def debug(message, *args):
    """Log a debug message. Supports format strings: debug("format %s", arg)"""
    logger.debug(message, *args)

def info(message, *args):
    """Log an info message. Supports format strings: info("format %s", arg)"""
    logger.info(message, *args)

def warning(message, *args):
    """Log a warning message. Supports format strings: warning("format %s", arg)"""
    logger.warning(message, *args)

def error(message, *args, exc_info=False):
    """Log an error message. Supports format strings: error("format %s", arg)"""
    # exc_info parameter is ignored - no tracebacks are included by default
    logger.error(message, *args)

def exception(message):
    # Use error instead of exception to avoid traceback
    logger.error(message)

# Add or remove filter patterns
def add_filter_pattern(pattern):
    logger.add_filter_pattern(pattern)

def remove_filter_pattern(pattern):
    logger.remove_filter_pattern(pattern) 