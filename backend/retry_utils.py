"""Retry utilities for handling transient failures in external API calls."""

import asyncio
import logging
from typing import TypeVar, Callable, Optional, Union, Type
from functools import wraps
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')

class RetryError(Exception):
    """Raised when all retry attempts have been exhausted."""
    pass


async def exponential_backoff_with_jitter(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """Calculate exponential backoff delay with optional jitter.
    
    Args:
        attempt: The current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add random jitter to prevent thundering herd
        
    Returns:
        Delay in seconds
    """
    # Calculate exponential delay
    delay = min(base_delay * (2 ** attempt), max_delay)
    
    # Add jitter to prevent thundering herd problem
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)
    
    return delay


async def retry_with_exponential_backoff(
    func: Callable[..., T],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: Optional[Union[Type[Exception], tuple[Type[Exception], ...]]] = None,
    **kwargs
) -> T:
    """Retry an async function with exponential backoff.
    
    Args:
        func: The async function to retry
        *args: Positional arguments for the function
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retry_on: Exception types to retry on (default: all exceptions)
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function call
        
    Raises:
        RetryError: If all retry attempts fail
    """
    if retry_on is None:
        retry_on = Exception
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            # Try to call the function
            result = await func(*args, **kwargs)
            
            # If successful and this was a retry, log it
            if attempt > 0:
                logger.info(f"Successfully completed {func.__name__} after {attempt} retries")
            
            return result
            
        except retry_on as e:
            last_exception = e
            
            # If this was the last attempt, raise
            if attempt == max_retries:
                logger.error(
                    f"Failed {func.__name__} after {max_retries + 1} attempts: {str(e)}"
                )
                raise RetryError(
                    f"Failed after {max_retries + 1} attempts: {str(e)}"
                ) from e
            
            # Calculate delay
            delay = await exponential_backoff_with_jitter(
                attempt, base_delay, max_delay
            )
            
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {str(e)}. "
                f"Retrying in {delay:.2f} seconds..."
            )
            
            # Wait before retrying
            await asyncio.sleep(delay)
    
    # This should never be reached, but just in case
    raise RetryError(f"Unexpected retry failure") from last_exception


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_on: Optional[Union[Type[Exception], tuple[Type[Exception], ...]]] = None
):
    """Decorator to add retry logic to async functions.
    
    Usage:
        @with_retry(max_retries=3, base_delay=1.0)
        async def my_api_call():
            # Make API call that might fail
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_exponential_backoff(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                retry_on=retry_on,
                **kwargs
            )
        return wrapper
    return decorator


# Common retry configurations
OPENAI_RETRY_CONFIG = {
    "max_retries": 3,
    "base_delay": 1.0,
    "retry_on": (Exception,),  # Retry on all exceptions for now
}

RETRIEVAL_RETRY_CONFIG = {
    "max_retries": 2,
    "base_delay": 0.5,
    "retry_on": (Exception,),
}