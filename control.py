import threading

class Control:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._refresh_requested = False

    def request_refresh(self) -> None:
        with self._lock:
            self._refresh_requested = True

    def consume_refresh(self) -> bool:
        with self._lock:
            if self._refresh_requested:
                self._refresh_requested = False
                return True
            return False
