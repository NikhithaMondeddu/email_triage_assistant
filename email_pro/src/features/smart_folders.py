"""Smart folders: virtual folders by category/priority (views over inbox)."""
from typing import Optional

import config
from src.models import Category, EmailThread, TriageResult


class SmartFolders:
    """Map threads to smart folder names for filtering/views."""

    def folder_for_triage(self, triage: TriageResult) -> str:
        return triage.suggested_folder

    def folder_for_category(self, category: Category, is_urgent: bool) -> str:
        if is_urgent:
            return config.FOLDER_URGENT
        return {
            Category.URGENT: config.FOLDER_URGENT,
            Category.FOLLOW_UP: config.FOLDER_FOLLOW_UP,
            Category.MEETING: config.FOLDER_MEETINGS,
            Category.NEWSLETTER: config.FOLDER_NEWSLETTER,
            Category.PROMOTION: config.FOLDER_PROMO,
            Category.OTHER: config.FOLDER_OTHER,
        }.get(category, config.FOLDER_OTHER)

    def filter_into_folders(
        self,
        threads_with_triage: list[tuple[EmailThread, TriageResult]],
        folder_name: Optional[str] = None,
    ) -> dict[str, list[EmailThread]]:
        """Group threads by smart folder. If folder_name given, return only that folder's threads."""
        by_folder: dict[str, list[EmailThread]] = {}
        for thread, triage in threads_with_triage:
            f = triage.suggested_folder
            by_folder.setdefault(f, []).append(thread)
        if folder_name:
            return {folder_name: by_folder.get(folder_name, [])}
        return by_folder
