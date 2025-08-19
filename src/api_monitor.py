import logging
import time

logger = logging.getLogger(__name__)

class APIMonitor:
    """Simplified API monitor - logs only."""
    
    def start_request(self, method: str, url: str, params: dict = None) -> str:
        """Start monitoring an API request."""
        request_id = f"req_{int(time.time() * 1000)}"
        logger.info(f"API Monitor: Started {method} request {request_id}")
        return request_id
    
    def update_status(self, request_id: str, status: str, 
                     duration: float = 0.0, response_size: int = 0, 
                     error_message: str = ""):
        """Update request status."""
        logger.info(f"API Monitor: {request_id} -> {status}")
        if error_message:
            logger.error(f"API Monitor: {request_id} error: {error_message}")
    
    def show_current_request(self):
        """Disabled."""
        pass
    
    def show_history_sidebar(self):
        """Disabled."""
        pass
    
    def show_live_stats(self):
        """Disabled."""
        pass
    
    def clear_history(self):
        """Disabled."""
        pass

# Global instance
api_monitor = APIMonitor()
