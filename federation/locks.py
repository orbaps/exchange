import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass
from federation.clock import global_clock

@dataclass
class LockInfo:
    lock_name: str
    client_id: str
    expires_at: float

class DistributedLockManager:
    """Thread-safe lease-based locking system utilizing the virtual DeterministicClock."""

    def __init__(self):
        self._locks: Dict[str, LockInfo] = {}
        self._lock = threading.Lock()
        self.lock_contention: int = 0

    def acquire(self, lock_name: str, client_id: str, lease_duration: float) -> bool:
        """Acquire a lease-based lock. Returns True if successful, False otherwise."""
        with self._lock:
            now = global_clock.now()
            existing = self._locks.get(lock_name)
            
            # Check if lock exists and is still valid
            if existing and existing.expires_at > now:
                if existing.client_id == client_id:
                    # Same client can re-acquire/renew
                    existing.expires_at = now + lease_duration
                    return True
                else:
                    # Contention occurred: another client holds the lock
                    self.lock_contention += 1
                    return False
            
            # Lock doesn't exist or has expired
            self._locks[lock_name] = LockInfo(
                lock_name=lock_name,
                client_id=client_id,
                expires_at=now + lease_duration
            )
            return True

    def release(self, lock_name: str, client_id: str) -> bool:
        """Release a lock held by a client."""
        with self._lock:
            existing = self._locks.get(lock_name)
            if existing:
                if existing.client_id == client_id:
                    del self._locks[lock_name]
                    return True
            return False

    def renew(self, lock_name: str, client_id: str, lease_duration: float) -> bool:
        """Renew the lease on an actively held lock."""
        with self._lock:
            now = global_clock.now()
            existing = self._locks.get(lock_name)
            if existing and existing.expires_at > now and existing.client_id == client_id:
                existing.expires_at = now + lease_duration
                return True
            self.lock_contention += 1
            return False

    def expire(self, lock_name: str) -> bool:
        """Explicitly check and expire a lock if its lease has elapsed."""
        with self._lock:
            now = global_clock.now()
            existing = self._locks.get(lock_name)
            if existing and existing.expires_at <= now:
                del self._locks[lock_name]
                return True
            return False

    def cleanup_expired_locks(self) -> int:
        """Scan and clear all expired locks. Returns the count of expired locks removed."""
        with self._lock:
            now = global_clock.now()
            expired_keys = [k for k, v in self._locks.items() if v.expires_at <= now]
            for k in expired_keys:
                del self._locks[k]
            return len(expired_keys)

    def get_lock_owner(self, lock_name: str) -> Optional[str]:
        """Retrieve the client ID currently holding the lock, if it hasn't expired."""
        with self._lock:
            now = global_clock.now()
            existing = self._locks.get(lock_name)
            if existing and existing.expires_at > now:
                return existing.client_id
            return None

    def get_locks_state(self) -> Dict[str, Dict[str, Any]]:
        """Return raw dictionary representation of all active locks for snapshots/checkpoints."""
        with self._lock:
            now = global_clock.now()
            return {
                k: {
                    "lock_name": v.lock_name,
                    "client_id": v.client_id,
                    "expires_at": v.expires_at
                }
                for k, v in self._locks.items() if v.expires_at > now
            }

    def restore_locks_state(self, state: Dict[str, Dict[str, Any]]) -> None:
        """Restore locks from a serialized snapshot/checkpoint."""
        with self._lock:
            self._locks.clear()
            for k, v in state.items():
                self._locks[k] = LockInfo(
                    lock_name=v["lock_name"],
                    client_id=v["client_id"],
                    expires_at=v["expires_at"]
                )
