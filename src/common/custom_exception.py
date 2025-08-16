class CustomException(Exception):
    """Custom exception class for the application"""
    
    def __init__(self, message: str, original_exception: Exception = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)
    
    def __str__(self):
        if self.original_exception:
            return f"{self.message}. Original error: {str(self.original_exception)}"
        return self.message
