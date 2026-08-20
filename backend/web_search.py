"""
Brave Search API Integration
=============================

Provides web search capabilities using the Brave Search API.
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BraveSearchClient:
    """Client for Brave Search API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Brave Search client

        Args:
            api_key: Brave Search API key (if not provided, will use BRAVE_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('BRAVE_API_KEY')
        if not self.api_key:
            raise ValueError("Brave API key is required")

        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }

    def search(
        self,
        query: str,
        count: int = 5,
        search_lang: str = "en",
        country: str = "US"
    ) -> Dict[str, Any]:
        """
        Perform a web search using Brave Search API

        Args:
            query: Search query
            count: Number of results to return (default: 5, max: 20)
            search_lang: Search language (default: "en")
            country: Country code for search (default: "US")

        Returns:
            Dictionary containing search results
        """
        try:
            params = {
                "q": query,
                "count": min(count, 20),  # Max 20 results
                "search_lang": search_lang,
                "country": country
            }

            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Brave Search API error: {e}")
            return {"web": {"results": []}, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in Brave Search: {e}")
            return {"web": {"results": []}, "error": str(e)}

    def format_results(self, search_response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Format Brave Search results into a simpler structure

        Args:
            search_response: Raw response from Brave Search API

        Returns:
            List of formatted search results
        """
        formatted_results = []

        try:
            web_results = search_response.get("web", {}).get("results", [])

            for result in web_results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "description": result.get("description", ""),
                    "url": result.get("url", ""),
                    "age": result.get("age", ""),  # How recent the page is
                })

        except Exception as e:
            logger.error(f"Error formatting Brave Search results: {e}")

        return formatted_results

    def search_and_format(
        self,
        query: str,
        count: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search and return formatted results in one call

        Args:
            query: Search query
            count: Number of results to return

        Returns:
            List of formatted search results
        """
        raw_results = self.search(query, count)
        return self.format_results(raw_results)


def create_web_search_context(query: str, search_results: List[Dict[str, Any]]) -> str:
    """
    Create a context string from web search results for the AI

    Args:
        query: The user's search query
        search_results: List of formatted search results

    Returns:
        Formatted context string
    """
    if not search_results:
        return "No web search results found."

    context = f"Web search results for '{query}':\n\n"

    for idx, result in enumerate(search_results, 1):
        context += f"{idx}. {result['title']}\n"
        context += f"   {result['description']}\n"
        context += f"   URL: {result['url']}\n"
        if result.get('age'):
            context += f"   Age: {result['age']}\n"
        context += "\n"

    return context
