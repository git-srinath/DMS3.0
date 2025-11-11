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
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate log entries
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Create logs directory if it doesn't exist
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dwtool.log')
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
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
    
    def info(self, message):
        """Log an info message"""
        formatted_message = self._format_message('info', message)
        if self._should_log(message):
            self.logger.info(formatted_message)
    
    def warning(self, message):
        """Log a warning message"""
        formatted_message = self._format_message('warning', message)
        if self._should_log(message):
            self.logger.warning(formatted_message)
    
    def error(self, message, exc_info=False):
        """
        Log an error message
        exc_info parameter is ignored - no tracebacks are included by default
        """
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
def info(message):
    logger.info(message)

def warning(message):
    logger.warning(message)

def error(message, exc_info=False):
    # Ignore exc_info parameter, always pass False
    logger.error(message, exc_info=False)

def exception(message):
    # Use error instead of exception to avoid traceback
    logger.error(message)

# Add or remove filter patterns
def add_filter_pattern(pattern):
    logger.add_filter_pattern(pattern)

def remove_filter_pattern(pattern):
    logger.remove_filter_pattern(pattern) 