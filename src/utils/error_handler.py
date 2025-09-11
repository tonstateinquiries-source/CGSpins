"""
Professional error handling system for CG Spins Bot
Provides centralized error handling, logging, and recovery mechanisms
"""

import asyncio
import traceback
from typing import Any, Callable, Dict, Optional, Union
from functools import wraps

from .logger import get_logger

logger = get_logger("ErrorHandler")

class BotError(Exception):
    """Base exception class for bot-specific errors"""
    def __init__(self, message: str, user_id: Optional[int] = None, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.user_id = user_id
        self.context = context or {}

class TONAPIError(BotError):
    """Exception for TON API related errors"""
    pass

class DatabaseError(BotError):
    """Exception for database related errors"""
    pass

class PaymentError(BotError):
    """Exception for payment related errors"""
    pass

class UserDataError(BotError):
    """Exception for user data related errors"""
    pass

def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle errors gracefully in async functions
    
    Args:
        func: Function to wrap with error handling
    
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Extract user_id from function arguments if possible
            user_id = None
            for arg in args:
                if hasattr(arg, 'from_user') and hasattr(arg.from_user, 'id'):
                    user_id = arg.from_user.id
                    break
            
            # Log the error with context
            logger.error(
                f"Error in {func.__name__}: {str(e)}",
                extra={
                    "function": func.__name__,
                    "user_id": user_id,
                    "args": str(args),
                    "kwargs": str(kwargs),
                    "traceback": traceback.format_exc()
                }
            )
            
            # Try to send user-friendly error message
            if user_id:
                try:
                    from aiogram import Bot
                    # Find bot instance in args
                    bot = None
                    for arg in args:
                        if isinstance(arg, Bot):
                            bot = arg
                            break
                    
                    if bot:
                        await bot.send_message(
                            chat_id=user_id,
                            text="❌ An error occurred. Please try again later or contact support if the problem persists.",
                            parse_mode="HTML"
                        )
                except Exception as send_error:
                    logger.error(f"Failed to send error message to user {user_id}: {send_error}")
            
            # Re-raise the exception for proper handling
            raise
    
    return wrapper

def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """
    Safely execute a function and return result or None on error
    
    Args:
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Function result or None if error occurred
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {str(e)}")
        return None

async def safe_async_execute(func: Callable, *args, **kwargs) -> Any:
    """
    Safely execute an async function and return result or None on error
    
    Args:
        func: Async function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Function result or None if error occurred
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {str(e)}")
        return None

class ErrorRecovery:
    """Class for handling error recovery strategies"""
    
    @staticmethod
    async def retry_with_backoff(
        func: Callable, 
        max_retries: int = 3, 
        base_delay: float = 1.0,
        *args, 
        **kwargs
    ) -> Any:
        """
        Retry a function with exponential backoff
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Base delay between retries
            *args: Function arguments
            **kwargs: Function keyword arguments
        
        Returns:
            Function result or raises last exception
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {max_retries} attempts failed. Last error: {str(e)}")
        
        raise last_exception

def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function calls for debugging
    
    Args:
        func: Function to wrap with logging
    
    Returns:
        Wrapped function with logging
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {str(e)}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {str(e)}")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper 