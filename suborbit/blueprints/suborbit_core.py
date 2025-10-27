import threading
import time


class SubOrbitCore:
    """Manages the discovery job state and execution."""

    def __init__(self):
        self._thread = None
        self._running = False
        self._lock = threading.Lock()

    def is_running(self):
        """Return True if a discovery is in progress."""
        with self._lock:
            return self._running

    def run(self, form_data):
        """Run discovery job in a background thread."""
        with self._lock:
            if self._running:
                print("Discovery already running, skipping new start.")
                return
            self._running = True

        print(f"🚀 Starting discovery with parameters: {form_data}")
        try:
            # Simulate discovery (replace with real logic)
            for i in range(10):
                print(f"Processing movie {i+1}/10...")
                time.sleep(1)
        finally:
            with self._lock:
                self._running = False
            print("✅ Discovery completed.")

    def start(self, form_data):
        """Start the discovery process asynchronously."""
        if self.is_running():
            return False
        thread = threading.Thread(target=self.run, args=(form_data,), daemon=True)
        thread.start()
        self._thread = thread
        return True

    def stop(self):
        """Stop discovery (simple cooperative stop for now)."""
        with self._lock:
            if not self._running:
                return False
            # You can extend this with a real cancellation flag
            self._running = False
        print("🛑 Discovery stopped by user.")
        return True
