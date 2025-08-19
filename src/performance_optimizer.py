import streamlit as st
import pandas as pd
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Class to handle performance optimizations for large datasets."""
    
    def __init__(self):
        self.cache = {}
        self.cache_timestamps = {}
        self.max_cache_size = 1000
        self.cache_ttl = 300  # 5 minutes
        
    def memory_efficient_cache(self, ttl: int = 300):
        """Decorator for memory-efficient caching with TTL."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key
                cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                current_time = time.time()
                
                # Check if cached result exists and is still valid
                if (cache_key in self.cache and 
                    cache_key in self.cache_timestamps and
                    current_time - self.cache_timestamps[cache_key] < ttl):
                    logger.debug(f"Cache hit for {func.__name__}")
                    return self.cache[cache_key]
                
                # Clean old cache entries if cache is getting too large
                if len(self.cache) > self.max_cache_size:
                    self._clean_cache()
                
                # Execute function and cache result
                logger.debug(f"Cache miss for {func.__name__}, executing...")
                result = func(*args, **kwargs)
                
                self.cache[cache_key] = result
                self.cache_timestamps[cache_key] = current_time
                
                return result
            return wrapper
        return decorator
    
    def _clean_cache(self):
        """Remove old cache entries."""
        current_time = time.time()
        keys_to_remove = []
        
        for key, timestamp in self.cache_timestamps.items():
            if current_time - timestamp > self.cache_ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            self.cache.pop(key, None)
            self.cache_timestamps.pop(key, None)
        
        logger.info(f"Cleaned {len(keys_to_remove)} cache entries")
    
    def batch_process_data(self, data: List[Any], batch_size: int = 100, 
                          processor_func: Callable = None) -> List[Any]:
        """Process large datasets in batches to avoid memory issues."""
        if not processor_func:
            return data
        
        results = []
        total_batches = len(data) // batch_size + (1 if len(data) % batch_size else 0)
        
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_results = processor_func(batch)
            results.extend(batch_results)
            
            # Update progress
            progress = (i // batch_size + 1) / total_batches
            progress_bar.progress(progress)
            status_text.text(f"Traitement: {i + len(batch)}/{len(data)} éléments")
            
            # Small delay to prevent UI freezing
            time.sleep(0.01)
        
        progress_bar.empty()
        status_text.empty()
        
        return results
    
    def parallel_api_calls(self, api_calls: List[Dict], max_workers: int = 5) -> List[Any]:
        """Execute multiple API calls in parallel."""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_call = {}
            for call_info in api_calls:
                future = executor.submit(self._execute_api_call, call_info)
                future_to_call[future] = call_info
            
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            completed = 0
            
            # Collect results as they complete
            for future in as_completed(future_to_call):
                call_info = future_to_call[future]
                try:
                    result = future.result()
                    results.append({
                        'call_info': call_info,
                        'result': result,
                        'success': True
                    })
                except Exception as e:
                    logger.error(f"API call failed: {e}")
                    results.append({
                        'call_info': call_info,
                        'result': None,
                        'success': False,
                        'error': str(e)
                    })
                
                completed += 1
                progress = completed / len(api_calls)
                progress_bar.progress(progress)
                status_text.text(f"Requêtes API: {completed}/{len(api_calls)} terminées")
        
        progress_bar.empty()
        status_text.empty()
        
        return results
    
    def _execute_api_call(self, call_info: Dict) -> Any:
        """Execute a single API call."""
        # This would be implemented based on the specific API being called
        # For now, it's a placeholder
        import requests
        
        method = call_info.get('method', 'GET')
        url = call_info.get('url')
        params = call_info.get('params', {})
        headers = call_info.get('headers', {})
        
        response = requests.request(method, url, params=params, headers=headers)
        response.raise_for_status()
        
        return response.json()
    
    def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage."""
        if df.empty:
            return df
        
        initial_memory = df.memory_usage(deep=True).sum()
        
        # Optimize numeric columns
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Optimize object columns (strings)
        for col in df.select_dtypes(include=['object']).columns:
            num_unique_values = len(df[col].unique())
            num_total_values = len(df[col])
            
            # Convert to category if it saves memory
            if num_unique_values / num_total_values < 0.5:
                df[col] = df[col].astype('category')
        
        # Convert datetime columns
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass
        
        final_memory = df.memory_usage(deep=True).sum()
        memory_reduction = (initial_memory - final_memory) / initial_memory * 100
        
        logger.info(f"DataFrame optimized: {memory_reduction:.1f}% memory reduction")
        
        return df
    
    def lazy_load_data(self, data_loader_func: Callable, chunk_size: int = 1000):
        """Implement lazy loading for large datasets."""
        def data_generator():
            offset = 0
            while True:
                chunk = data_loader_func(offset=offset, limit=chunk_size)
                if chunk is None or len(chunk) == 0:
                    break
                
                yield chunk
                offset += chunk_size
        
        return data_generator()
    
    def create_pagination_controls(self, total_items: int, items_per_page: int = 50):
        """Create pagination controls for large result sets."""
        if total_items <= items_per_page:
            return 0, items_per_page
        
        total_pages = (total_items + items_per_page - 1) // items_per_page
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Précédent", key="prev_page"):
                if st.session_state.get('current_page', 1) > 1:
                    st.session_state.current_page -= 1
        
        with col2:
            current_page = st.selectbox(
                "Page",
                range(1, total_pages + 1),
                index=st.session_state.get('current_page', 1) - 1,
                key="page_selector"
            )
            st.session_state.current_page = current_page
        
        with col3:
            if st.button("Suivant ➡️", key="next_page"):
                if st.session_state.get('current_page', 1) < total_pages:
                    st.session_state.current_page += 1
        
        # Display page info
        start_item = (current_page - 1) * items_per_page
        end_item = min(start_item + items_per_page, total_items)
        
        st.info(f"Affichage des éléments {start_item + 1}-{end_item} sur {total_items}")
        
        return start_item, end_item
    
    def show_performance_metrics(self):
        """Display performance metrics in the sidebar."""
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {
                'api_calls': 0,
                'cache_hits': 0,
                'total_processing_time': 0,
                'memory_usage': 0
            }
        
        metrics = st.session_state.performance_metrics
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("**📊 Métriques de Performance**")
        st.sidebar.metric("Appels API", metrics['api_calls'])
        st.sidebar.metric("Cache Hits", metrics['cache_hits'])
        st.sidebar.metric("Temps Total", f"{metrics['total_processing_time']:.2f}s")
        
        # Cache size info
        cache_size = len(self.cache)
        st.sidebar.metric("Éléments en Cache", cache_size)
        
        # Memory usage (approximate)
        if cache_size > 0:
            avg_cache_size = sum(len(str(v)) for v in self.cache.values()) / cache_size
            total_cache_memory = avg_cache_size * cache_size / 1024  # KB
            st.sidebar.metric("Mémoire Cache", f"{total_cache_memory:.1f} KB")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        try:
            import psutil
            import os
            
            # Get current process
            process = psutil.Process(os.getpid())
            
            # Memory usage in MB
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Cache metrics
            cache_size = len(self.cache)
            
            # Clean old cache entries
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self.cache_timestamps.items()
                if current_time - timestamp > self.cache_ttl
            ]
            
            metrics = {
                'memory_mb': memory_mb,
                'cache_size': cache_size,
                'expired_cache_entries': len(expired_keys),
                'cache_hit_ratio': getattr(self, '_cache_hits', 0) / max(getattr(self, '_cache_requests', 1), 1),
                'process_cpu_percent': process.cpu_percent(),
            }
            
            return metrics
            
        except ImportError:
            # Fallback if psutil is not available
            return {
                'memory_mb': 0.0,
                'cache_size': len(self.cache),
                'expired_cache_entries': 0,
                'cache_hit_ratio': 0.0,
                'process_cpu_percent': 0.0,
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {
                'memory_mb': 0.0,
                'cache_size': len(self.cache),
                'expired_cache_entries': 0,
                'cache_hit_ratio': 0.0,
                'process_cpu_percent': 0.0,
            }
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("Performance cache cleared")

class AsyncAPIManager:
    """Async API manager for better handling of concurrent requests."""
    
    def __init__(self, max_concurrent_requests: int = 10):
        self.max_concurrent_requests = max_concurrent_requests
        self.semaphore = None
        
    async def async_api_call(self, session: aiohttp.ClientSession, url: str, 
                           params: Dict = None) -> Dict:
        """Make an async API call."""
        async with self.semaphore:
            try:
                async with session.get(url, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                logger.error(f"Async API call failed: {e}")
                return {}
    
    async def batch_async_calls(self, urls_and_params: List[tuple]) -> List[Dict]:
        """Execute multiple API calls asynchronously."""
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url, params in urls_and_params:
                task = self.async_api_call(session, url, params)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return results

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

# Decorator for easy use
def cached(ttl: int = 300):
    """Easy-to-use caching decorator."""
    return performance_optimizer.memory_efficient_cache(ttl)

# Usage example
if __name__ == "__main__":
    optimizer = PerformanceOptimizer()
    
    # Example of using the caching decorator
    @optimizer.memory_efficient_cache(ttl=600)
    def expensive_calculation(x, y):
        time.sleep(1)  # Simulate expensive operation
        return x * y + 42
    
    # Test caching
    start_time = time.time()
    result1 = expensive_calculation(10, 20)
    print(f"First call took {time.time() - start_time:.2f}s")
    
    start_time = time.time()
    result2 = expensive_calculation(10, 20)  # Should be cached
    print(f"Second call took {time.time() - start_time:.2f}s")
