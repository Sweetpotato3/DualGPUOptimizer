"""
Update Checker for DualGPUOptimizer

Checks for updates from GitHub and notifies the user when a new version is available.
"""
import json
import logging
import threading
import time
from typing import Optional, Dict, Any, Tuple, Callable
import re
import os
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger("DualGPUOpt.UpdateChecker")

# Current version
VERSION = "1.0.0"

# URLs for checking updates
DEFAULT_REPO_URL = "https://api.github.com/repos/yourusername/DualGPUOptimizer/releases/latest"
RELEASES_URL = "https://github.com/yourusername/DualGPUOptimizer/releases"

# Check frequency (in hours)
DEFAULT_CHECK_FREQUENCY = 24  # Check once per day by default

# Local cache file
LOCAL_CACHE_DIR = os.path.join(os.path.expanduser('~'), '.dualgpuopt')
os.makedirs(LOCAL_CACHE_DIR, exist_ok=True)
UPDATE_CACHE_FILE = os.path.join(LOCAL_CACHE_DIR, 'update_cache.json')

class Version:
    """Version parser and comparison"""

    def __init__(self, version_str: str):
        """Initialize from version string"""
        self.version_str = version_str

        # Parse version string
        match = re.match(r'v?(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9.-]+))?', version_str)
        if match:
            self.major = int(match.group(1))
            self.minor = int(match.group(2))
            self.patch = int(match.group(3))
            self.prerelease = match.group(4) or ""
        else:
            logger.warning(f"Failed to parse version: {version_str}")
            self.major = 0
            self.minor = 0
            self.patch = 0
            self.prerelease = ""

    def __str__(self) -> str:
        """String representation"""
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            return f"{base}-{self.prerelease}"
        return base

    def __lt__(self, other) -> bool:
        """Less than comparison"""
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch

        # Pre-release versions are less than release versions
        if not self.prerelease and other.prerelease:
            return False
        if self.prerelease and not other.prerelease:
            return True

        # Both have pre-release versions or both don't
        return self.prerelease < other.prerelease

    def __eq__(self, other) -> bool:
        """Equality comparison"""
        return (self.major == other.major and
                self.minor == other.minor and
                self.patch == other.patch and
                self.prerelease == other.prerelease)

    def __le__(self, other) -> bool:
        """Less than or equal comparison"""
        return self < other or self == other

    def __gt__(self, other) -> bool:
        """Greater than comparison"""
        return not (self <= other)

    def __ge__(self, other) -> bool:
        """Greater than or equal comparison"""
        return not (self < other)


class UpdateInfo:
    """Information about an available update"""

    def __init__(self, version: str, release_date: str,
                 release_notes: str, download_url: str):
        """Initialize update info

        Args:
            version: Version string (e.g., "1.2.3")
            release_date: Release date string
            release_notes: Release notes markdown
            download_url: URL to download the update
        """
        self.version = Version(version)
        self.release_date = release_date
        self.release_notes = release_notes
        self.download_url = download_url

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization

        Returns:
            Dictionary representation
        """
        return {
            "version": str(self.version),
            "release_date": self.release_date,
            "release_notes": self.release_notes,
            "download_url": self.download_url
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UpdateInfo':
        """Create from dictionary

        Args:
            data: Dictionary with update info

        Returns:
            UpdateInfo object
        """
        return cls(
            version=data.get("version", "0.0.0"),
            release_date=data.get("release_date", ""),
            release_notes=data.get("release_notes", ""),
            download_url=data.get("download_url", "")
        )


class UpdateChecker:
    """Checks for updates and notifies the user"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UpdateChecker, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, check_frequency: int = DEFAULT_CHECK_FREQUENCY,
                 repo_url: str = DEFAULT_REPO_URL,
                 current_version: str = VERSION,
                 auto_check: bool = True):
        """Initialize the update checker

        Args:
            check_frequency: How often to check for updates (in hours)
            repo_url: URL to check for updates
            current_version: Current version string
            auto_check: Whether to automatically check for updates
        """
        # Skip initialization if already initialized
        if self._initialized:
            return

        self.check_frequency = check_frequency
        self.repo_url = repo_url
        self.current_version = Version(current_version)
        self.auto_check = auto_check

        self._update_available = False
        self._update_info: Optional[UpdateInfo] = None
        self._last_check_time: Optional[datetime] = None
        self._check_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._listeners: list[Callable[[UpdateInfo], None]] = []

        # Load cache
        self._load_cache()

        # Start background thread if auto-check is enabled
        if auto_check:
            self._start_background_checker()

        self._initialized = True

    def _load_cache(self) -> None:
        """Load update cache from disk"""
        if not os.path.exists(UPDATE_CACHE_FILE):
            logger.debug("Update cache file not found")
            return

        try:
            with open(UPDATE_CACHE_FILE, 'r') as f:
                cache = json.load(f)

            # Parse last check time
            last_check_str = cache.get("last_check_time")
            if last_check_str:
                self._last_check_time = datetime.fromisoformat(last_check_str)

            # Parse update info
            update_info_dict = cache.get("update_info")
            if update_info_dict:
                self._update_info = UpdateInfo.from_dict(update_info_dict)

                # Check if the cached update is newer than current version
                if self._update_info.version > self.current_version:
                    self._update_available = True
                    logger.info(f"Update available from cache: {self._update_info.version}")

        except Exception as e:
            logger.error(f"Failed to load update cache: {e}")

    def _save_cache(self) -> None:
        """Save update cache to disk"""
        try:
            cache = {
                "last_check_time": self._last_check_time.isoformat() if self._last_check_time else None,
                "update_info": self._update_info.to_dict() if self._update_info else None
            }

            with open(UPDATE_CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save update cache: {e}")

    def _start_background_checker(self) -> None:
        """Start background thread for checking updates"""
        if self._check_thread is not None and self._check_thread.is_alive():
            return

        self._stop_event.clear()
        self._check_thread = threading.Thread(
            target=self._background_check_loop,
            daemon=True
        )
        self._check_thread.start()

    def _background_check_loop(self) -> None:
        """Background thread for periodic update checks"""
        try:
            while not self._stop_event.is_set():
                # Check if it's time to check for updates
                if self._should_check_now():
                    self.check_for_updates()

                # Sleep for an hour (or until stopped)
                self._stop_event.wait(3600)  # 1 hour
        except Exception as e:
            logger.error(f"Error in update check background thread: {e}")

    def _should_check_now(self) -> bool:
        """Check if it's time to check for updates

        Returns:
            True if should check now, False otherwise
        """
        # If never checked, check now
        if self._last_check_time is None:
            return True

        # Calculate time since last check
        now = datetime.now()
        time_since_last_check = now - self._last_check_time

        # Check if it's been long enough
        return time_since_last_check > timedelta(hours=self.check_frequency)

    def stop(self) -> None:
        """Stop the background update checker"""
        self._stop_event.set()
        if self._check_thread is not None:
            self._check_thread.join(timeout=1.0)

    def check_for_updates(self) -> Tuple[bool, Optional[UpdateInfo]]:
        """Check for updates

        Returns:
            Tuple of (update_available, update_info)
        """
        # Record check time
        self._last_check_time = datetime.now()

        try:
            # Import requests lazily
            try:
                import requests
            except ImportError:
                logger.warning("Requests library not installed, cannot check for updates")
                return self._update_available, self._update_info

            # Fetch latest release info
            response = requests.get(self.repo_url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Failed to check for updates: HTTP {response.status_code}")
                return self._update_available, self._update_info

            # Parse response
            release_data = response.json()

            # Extract version from tag name
            version_str = release_data.get("tag_name", "0.0.0")
            if version_str.startswith("v"):
                version_str = version_str[1:]

            # Create Version objects
            latest_version = Version(version_str)

            # Check if update is available
            if latest_version > self.current_version:
                # Create update info
                self._update_info = UpdateInfo(
                    version=version_str,
                    release_date=release_data.get("published_at", ""),
                    release_notes=release_data.get("body", ""),
                    download_url=release_data.get("html_url", RELEASES_URL)
                )

                self._update_available = True
                logger.info(f"Update available: {latest_version}")

                # Notify listeners
                self._notify_listeners()
            else:
                self._update_available = False
                logger.info("No update available")

            # Save cache
            self._save_cache()

            return self._update_available, self._update_info

        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return self._update_available, self._update_info

    def is_update_available(self) -> bool:
        """Check if an update is available

        Returns:
            True if an update is available, False otherwise
        """
        return self._update_available

    def get_update_info(self) -> Optional[UpdateInfo]:
        """Get information about the available update

        Returns:
            UpdateInfo object or None if no update is available
        """
        return self._update_info

    def add_listener(self, listener: Callable[[UpdateInfo], None]) -> None:
        """Add a listener for update notifications

        Args:
            listener: Function to call when an update is available
        """
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[UpdateInfo], None]) -> bool:
        """Remove a listener

        Args:
            listener: Listener to remove

        Returns:
            True if removed, False if not found
        """
        if listener in self._listeners:
            self._listeners.remove(listener)
            return True
        return False

    def _notify_listeners(self) -> None:
        """Notify listeners about an available update"""
        if self._update_info is None:
            return

        for listener in self._listeners:
            try:
                listener(self._update_info)
            except Exception as e:
                logger.error(f"Error in update listener: {e}")


# Singleton instance
_update_checker: Optional[UpdateChecker] = None

def get_update_checker() -> UpdateChecker:
    """Get the global update checker instance

    Returns:
        UpdateChecker instance
    """
    global _update_checker
    if _update_checker is None:
        _update_checker = UpdateChecker()
    return _update_checker


def check_for_updates() -> Tuple[bool, Optional[UpdateInfo]]:
    """Check for updates

    Returns:
        Tuple of (update_available, update_info)
    """
    return get_update_checker().check_for_updates()


def is_update_available() -> bool:
    """Check if an update is available

    Returns:
        True if an update is available, False otherwise
    """
    return get_update_checker().is_update_available()


def get_update_info() -> Optional[UpdateInfo]:
    """Get information about the available update

    Returns:
        UpdateInfo object or None if no update is available
    """
    return get_update_checker().get_update_info()


if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)

    # Create update checker
    checker = get_update_checker()

    # Check for updates
    available, info = checker.check_for_updates()

    if available:
        print(f"Update available: {info.version}")
        print(f"Release date: {info.release_date}")
        print(f"Download URL: {info.download_url}")
        print(f"Release notes:\n{info.release_notes}")
    else:
        print("No update available")