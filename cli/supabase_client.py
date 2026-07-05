"""
Supabase client for AgentSON managed instance.

This module provides a simple client for pushing and pulling
AgentSON sessions to/from a Supabase instance.

Usage:
    from cli.supabase_client import AgentSONSupabase

    client = AgentSONSupabase(url="https://xxx.supabase.co", key="xxx")
    client.push(session_data)
    sessions = client.pull(search="nightscout")
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone


class AgentSONSupabase:
    """AgentSON Supabase client for managed instance."""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Supabase client.

        Args:
            url: Supabase project URL (or set SUPABASE_URL env var)
            key: Supabase anon key (or set SUPABASE_KEY env var)
        """
        self.url = url or os.environ.get("SUPABASE_URL")
        self.key = key or os.environ.get("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError(
                "Supabase URL and key required. "
                "Set SUPABASE_URL and SUPABASE_KEY environment variables, "
                "or pass url and key to constructor."
            )

        # Remove trailing slash
        self.url = self.url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        """Get request headers."""
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    def push(self, session_data: Dict) -> Dict:
        """
        Push an AgentSON session to Supabase.

        Args:
            session_data: AgentSON session data

        Returns:
            Created session record
        """
        import urllib.request
        import urllib.error

        # Extract metadata for indexed columns
        tool = session_data.get("tool", {}).get("id", "unknown")
        agent = session_data.get("agent", {}).get("id", "unknown")
        started_at = session_data.get("started_at")
        ended_at = session_data.get("ended_at")

        # Calculate metrics
        entries = session_data.get("entries", [])
        total_tokens = sum(
            entry.get("tokens", {}).get("total", 0)
            for entry in entries
            if isinstance(entry.get("tokens"), dict)
        )
        total_cost = sum(
            entry.get("tokens", {}).get("cost", 0)
            for entry in entries
            if isinstance(entry.get("tokens"), dict)
        )

        record = {
            "tool": tool,
            "agent": agent,
            "started_at": started_at,
            "ended_at": ended_at,
            "data": session_data,
            "total_tokens": total_tokens,
            "cost": total_cost,
            "message_count": len(entries)
        }

        url = f"{self.url}/rest/v1/sessions"
        data = json.dumps(record).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"Push failed: {e.code} {body}")

    def pull(
        self,
        search: Optional[str] = None,
        tool: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Pull sessions from Supabase.

        Args:
            search: Full-text search query
            tool: Filter by tool
            limit: Max sessions to return

        Returns:
            List of AgentSON sessions
        """
        import urllib.request
        import urllib.error
        import urllib.parse

        params = {"limit": str(limit)}

        if search:
            params["search"] = search
        if tool:
            params["tool"] = tool

        query = urllib.parse.urlencode(params)
        url = f"{self.url}/rest/v1/rpc/search_sessions?{query}"

        req = urllib.request.Request(url, headers=self._headers(), method="GET")

        try:
            with urllib.request.urlopen(req) as response:
                results = json.loads(response.read().decode("utf-8"))

                # Fetch full session data for each result
                sessions = []
                for result in results[:limit]:
                    session_url = f"{self.url}/rest/v1/sessions?id=eq.{result['id']}"
                    session_req = urllib.request.Request(session_url, headers=self._headers())
                    with urllib.request.urlopen(session_req) as session_response:
                        session_data = json.loads(session_response.read().decode("utf-8"))
                        if session_data:
                            sessions.append(session_data[0].get("data", {}))

                return sessions
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"Pull failed: {e.code} {body}")

    def list_sessions(self, limit: int = 50) -> List[Dict]:
        """
        List all sessions.

        Args:
            limit: Max sessions to return

        Returns:
            List of session metadata
        """
        import urllib.request
        import urllib.error

        url = f"{self.url}/rest/v1/sessions?select=id,tool,agent,started_at,created_at&limit={limit}&order=created_at.desc"

        req = urllib.request.Request(url, headers=self._headers(), method="GET")

        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"List failed: {e.code} {body}")

    def delete(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session UUID

        Returns:
            True if deleted
        """
        import urllib.request
        import urllib.error

        url = f"{self.url}/rest/v1/sessions?id=eq.{session_id}"

        req = urllib.request.Request(url, headers=self._headers(), method="DELETE")

        try:
            with urllib.request.urlopen(req) as response:
                return True
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            raise Exception(f"Delete failed: {e.code} {body}")
