"""Session and cookie manager for authenticated sources."""

import json
from datetime import datetime
from app.cache.metadata_repo import repo, MetadataRepository
from app.domain.models import SourceCredential
from app.logging import logger


class SessionManager:
    """Manages session cookies and credentials for VIP sources."""

    def __init__(self, metadata_repo: MetadataRepository | None = None) -> None:
        self.repo = metadata_repo or repo
        self._memory_cookies: dict[str, dict[str, str]] = {}

    def get_cookies(self, source_id: str) -> dict[str, str]:
        """Retrieve cookies for a source, first from memory then from database."""
        if source_id in self._memory_cookies:
            return self._memory_cookies[source_id]

        cred = self.repo.get_credential(source_id)
        if cred and cred.session_cookies_json:
            try:
                cookies = json.loads(cred.session_cookies_json)
                self._memory_cookies[source_id] = cookies
                return cookies
            except Exception as e:
                logger.warning(f"Failed to parse stored cookies for {source_id}: {e}")

        return {}

    def update_cookies(self, source_id: str, cookies: dict[str, str]) -> None:
        """Update cookie store for a source."""
        current = self.get_cookies(source_id)
        current.update(cookies)
        self._memory_cookies[source_id] = current

        cred = self.repo.get_credential(source_id)
        if cred:
            cred.session_cookies_json = json.dumps(current)
            cred.last_login_at = datetime.now()
            self.repo.save_credential(cred)

    def set_credential(self, source_id: str, username: str, password: str) -> None:
        """Store or update username and password for a source."""
        cred = SourceCredential(
            source_id=source_id,
            username=username,
            password_encrypted=password,  # In production, encrypt with local master key
            session_cookies_json=json.dumps(self.get_cookies(source_id)),
            last_login_at=datetime.now(),
        )
        self.repo.save_credential(cred)


session_manager = SessionManager()
