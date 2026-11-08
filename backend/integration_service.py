"""
Integration Service - Aggregator Module

This file serves as a compatibility layer that imports functions from 
specialized service modules. All integration logic has been moved to:
- github_service.py: GitHub API integration
- onenote_service.py: OneNote/Microsoft Graph API integration

This file can be safely deleted if no other modules depend on it.
"""

from github_service import (
    fetch_github_repos,
    get_github_repo_count,
    create_github_repo,
    get_github_repo,
    update_github_repo,
    delete_github_repo
)

from onenote_service import (
    fetch_onenote_pages,
    get_onenote_page_count,
    get_onenote_sections,
    get_onenote_page
)

__all__ = [
    'fetch_github_repos',
    'get_github_repo_count',
    'create_github_repo',
    'get_github_repo',
    'update_github_repo',
    'delete_github_repo',
    'fetch_onenote_pages',
    'get_onenote_page_count',
    'get_onenote_sections',
    'get_onenote_page'
]
