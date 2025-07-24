"""
Resource Manager for YouTube MCP Server.
Manages persistent storage of search results, analysis sessions, and generated content.
"""

import json
import logging
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import hashlib
import asyncio

from mcp.types import Resource, TextResourceContents, BlobResourceContents

logger = logging.getLogger(__name__)


class AnalysisSession:
    """Represents an analysis session with associated resources."""
    
    def __init__(self, session_id: str, title: str, description: str = ""):
        self.session_id = session_id
        self.title = title
        self.description = description
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.video_ids: Set[str] = set()
        self.search_queries: List[str] = []
        self.resources: List[str] = []  # Resource URIs
        self.metadata: Dict[str, Any] = {}
    
    def add_video_ids(self, video_ids: Union[str, List[str]]) -> None:
        """Add video IDs to the session."""
        if isinstance(video_ids, str):
            video_ids = [video_ids]
        self.video_ids.update(video_ids)
        self.updated_at = datetime.utcnow()
    
    def add_search_query(self, query: str) -> None:
        """Add a search query to the session."""
        if query not in self.search_queries:
            self.search_queries.append(query)
            self.updated_at = datetime.utcnow()
    
    def add_resource(self, resource_uri: str) -> None:
        """Add a resource URI to the session."""
        if resource_uri not in self.resources:
            self.resources.append(resource_uri)
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "video_ids": list(self.video_ids),
            "search_queries": self.search_queries,
            "resources": self.resources,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisSession":
        """Create session from dictionary."""
        session = cls(
            session_id=data["session_id"],
            title=data["title"],
            description=data.get("description", "")
        )
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.updated_at = datetime.fromisoformat(data["updated_at"])
        session.video_ids = set(data.get("video_ids", []))
        session.search_queries = data.get("search_queries", [])
        session.resources = data.get("resources", [])
        session.metadata = data.get("metadata", {})
        return session


class ResourceManager:
    """Manages MCP resources for YouTube analytics sessions."""
    
    def __init__(self, base_path: Union[str, Path]):
        """Initialize resource manager.
        
        Args:
            base_path: Base directory for storing resources
        """
        self.base_path = Path(base_path)
        self.sessions_path = self.base_path / "sessions"
        self.searches_path = self.base_path / "searches"
        self.visualizations_path = self.base_path / "visualizations"
        self.cache_path = self.base_path / "cache"
        
        # Create directory structure
        for path in [self.sessions_path, self.searches_path, self.visualizations_path, self.cache_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Session management
        self.sessions: Dict[str, AnalysisSession] = {}
        self.current_session_id: Optional[str] = None
        
        # Load existing sessions
        self._load_sessions()
        
        logger.info(f"Resource manager initialized at {self.base_path}")
    
    def _load_sessions(self) -> None:
        """Load existing sessions from disk."""
        sessions_file = self.sessions_path / "sessions.json"
        if sessions_file.exists():
            try:
                with open(sessions_file, 'r') as f:
                    sessions_data = json.load(f)
                
                for session_data in sessions_data.get("sessions", []):
                    session = AnalysisSession.from_dict(session_data)
                    self.sessions[session.session_id] = session
                
                self.current_session_id = sessions_data.get("current_session_id")
                logger.info(f"Loaded {len(self.sessions)} existing sessions")
                
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")
    
    def _save_sessions(self) -> None:
        """Save sessions to disk."""
        sessions_file = self.sessions_path / "sessions.json"
        try:
            sessions_data = {
                "current_session_id": self.current_session_id,
                "sessions": [session.to_dict() for session in self.sessions.values()]
            }
            
            with open(sessions_file, 'w') as f:
                json.dump(sessions_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def create_session(self, title: str, description: str = "", auto_switch: bool = True) -> str:
        """Create a new analysis session.
        
        Args:
            title: Session title
            description: Session description
            auto_switch: Whether to automatically switch to this session
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        session = AnalysisSession(session_id, title, description)
        
        self.sessions[session_id] = session
        
        if auto_switch or not self.current_session_id:
            self.current_session_id = session_id
        
        # Create session directory
        session_dir = self.sessions_path / session_id
        session_dir.mkdir(exist_ok=True)
        
        self._save_sessions()
        logger.info(f"Created session '{title}' with ID: {session_id}")
        
        return session_id
    
    def get_session(self, session_id: Optional[str] = None) -> Optional[AnalysisSession]:
        """Get a session by ID or current session.
        
        Args:
            session_id: Session ID, or None for current session
            
        Returns:
            Analysis session or None if not found
        """
        if session_id is None:
            session_id = self.current_session_id
        
        if session_id is None:
            return None
            
        return self.sessions.get(session_id)
    
    def switch_session(self, session_id: str) -> bool:
        """Switch to a different session.
        
        Args:
            session_id: Target session ID
            
        Returns:
            True if successful, False if session not found
        """
        if session_id in self.sessions:
            self.current_session_id = session_id
            self._save_sessions()
            logger.info(f"Switched to session: {session_id}")
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its resources.
        
        Args:
            session_id: Session to delete
            
        Returns:
            True if successful
        """
        if session_id not in self.sessions:
            return False
        
        # Remove session directory
        session_dir = self.sessions_path / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
        
        # Remove from memory
        del self.sessions[session_id]
        
        # Update current session if needed
        if self.current_session_id == session_id:
            self.current_session_id = next(iter(self.sessions.keys())) if self.sessions else None
        
        self._save_sessions()
        logger.info(f"Deleted session: {session_id}")
        return True
    
    def save_search_results(self, query: str, results: List[Dict[str, Any]], 
                          session_id: Optional[str] = None) -> str:
        """Save search results and extract video IDs.
        
        Args:
            query: Search query
            results: Search results
            session_id: Target session ID
            
        Returns:
            Resource URI for the saved search
        """
        session = self.get_session(session_id)
        if not session:
            # Create a new session for this search
            session_id = self.create_session(f"Search: {query[:50]}")
            session = self.get_session(session_id)
        
        # Generate search ID
        search_hash = hashlib.md5(f"{query}_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:8]
        search_id = f"search_{search_hash}"
        
        # Extract video IDs
        video_ids = []
        for result in results:
            if 'id' in result:
                video_ids.append(result['id'])
            elif 'video_id' in result:
                video_ids.append(result['video_id'])
        
        # Save search data
        search_data = {
            "query": query,
            "search_id": search_id,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session.session_id,
            "video_count": len(results),
            "video_ids": video_ids,
            "results": results
        }
        
        search_file = self.searches_path / f"{search_id}.json"
        with open(search_file, 'w') as f:
            json.dump(search_data, f, indent=2)
        
        # Update session
        session.add_search_query(query)
        session.add_video_ids(video_ids)
        
        resource_uri = f"youtube://search/{search_id}"
        session.add_resource(resource_uri)
        
        self._save_sessions()
        
        logger.info(f"Saved search results: {search_id} ({len(video_ids)} videos)")
        return resource_uri
    
    def save_video_details(self, video_details: List[Dict[str, Any]], 
                         session_id: Optional[str] = None) -> str:
        """Save detailed video information.
        
        Args:
            video_details: Video details data
            session_id: Target session ID
            
        Returns:
            Resource URI for the saved details
        """
        session = self.get_session(session_id)
        if not session:
            session_id = self.create_session("Video Details Analysis")
            session = self.get_session(session_id)
        
        # Generate details ID
        video_ids = [v.get('id', v.get('video_id', '')) for v in video_details]
        details_hash = hashlib.md5(f"details_{'_'.join(video_ids[:5])}".encode()).hexdigest()[:8]
        details_id = f"details_{details_hash}"
        
        # Save details data
        details_data = {
            "details_id": details_id,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session.session_id,
            "video_count": len(video_details),
            "video_ids": video_ids,
            "details": video_details
        }
        
        details_file = self.sessions_path / session.session_id / f"{details_id}.json"
        with open(details_file, 'w') as f:
            json.dump(details_data, f, indent=2)
        
        # Update session
        session.add_video_ids(video_ids)
        
        resource_uri = f"youtube://details/{details_id}"
        session.add_resource(resource_uri)
        
        self._save_sessions()
        
        logger.info(f"Saved video details: {details_id} ({len(video_ids)} videos)")
        return resource_uri
    
    def save_visualization(self, viz_type: str, viz_data: Dict[str, Any], 
                         session_id: Optional[str] = None) -> str:
        """Save visualization data and files.
        
        Args:
            viz_type: Type of visualization
            viz_data: Visualization data including file paths
            session_id: Target session ID
            
        Returns:
            Resource URI for the saved visualization
        """
        session = self.get_session(session_id)
        if not session:
            session_id = self.create_session(f"Visualization: {viz_type}")
            session = self.get_session(session_id)
        
        # Generate visualization ID
        viz_hash = hashlib.md5(f"{viz_type}_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:8]
        viz_id = f"viz_{viz_type}_{viz_hash}"
        
        # Create visualization directory
        viz_dir = self.visualizations_path / session.session_id / viz_id
        viz_dir.mkdir(parents=True, exist_ok=True)
        
        # Save visualization metadata
        viz_metadata = {
            "viz_id": viz_id,
            "viz_type": viz_type,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session.session_id,
            "data": viz_data
        }
        
        metadata_file = viz_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(viz_metadata, f, indent=2)
        
        # Copy visualization files if they exist
        if 'filepath' in viz_data and Path(viz_data['filepath']).exists():
            source_file = Path(viz_data['filepath'])
            dest_file = viz_dir / source_file.name
            shutil.copy2(source_file, dest_file)
            viz_metadata['data']['local_filepath'] = str(dest_file)
        
        # Update session
        resource_uri = f"youtube://visualization/{viz_id}"
        session.add_resource(resource_uri)
        
        self._save_sessions()
        
        logger.info(f"Saved visualization: {viz_id} ({viz_type})")
        return resource_uri
    
    def get_session_video_ids(self, session_id: Optional[str] = None) -> List[str]:
        """Get all video IDs from a session.
        
        Args:
            session_id: Session ID, or None for current session
            
        Returns:
            List of video IDs
        """
        session = self.get_session(session_id)
        if session:
            return list(session.video_ids)
        return []
    
    def get_session_resources(self, session_id: Optional[str] = None) -> List[Resource]:
        """Get all MCP resources for a session.
        
        Args:
            session_id: Session ID, or None for current session
            
        Returns:
            List of MCP Resource objects
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        resources = []
        
        # Add session overview resource
        session_uri = f"youtube://session/{session.session_id}"
        resources.append(Resource(
            uri=session_uri,
            name=f"Session: {session.title}",
            description=f"Analysis session with {len(session.video_ids)} videos",
            mimeType="application/json"
        ))
        
        # Add individual resources
        for resource_uri in session.resources:
            try:
                resource = self._load_resource_by_uri(resource_uri)
                if resource:
                    resources.append(resource)
            except Exception as e:
                logger.warning(f"Failed to load resource {resource_uri}: {e}")
        
        return resources
    
    def _load_resource_by_uri(self, resource_uri: str) -> Optional[Resource]:
        """Load a resource by its URI.
        
        Args:
            resource_uri: Resource URI (youtube://type/id)
            
        Returns:
            MCP Resource object or None
        """
        if not resource_uri.startswith("youtube://"):
            return None
        
        parts = resource_uri[10:].split('/')
        if len(parts) != 2:
            return None
        
        resource_type, resource_id = parts
        
        if resource_type == "search":
            return self._load_search_resource(resource_id)
        elif resource_type == "details":
            return self._load_details_resource(resource_id)
        elif resource_type == "visualization":
            return self._load_visualization_resource(resource_id)
        elif resource_type == "session":
            return self._load_session_resource(resource_id)
        
        return None
    
    def _load_search_resource(self, search_id: str) -> Optional[Resource]:
        """Load a search resource."""
        search_file = self.searches_path / f"{search_id}.json"
        if not search_file.exists():
            return None
        
        with open(search_file, 'r') as f:
            search_data = json.load(f)
        
        return Resource(
            uri=f"youtube://search/{search_id}",
            name=f"Search: {search_data['query']}",
            description=f"Search results for '{search_data['query']}' ({search_data['video_count']} videos)",
            mimeType="application/json"
        )
    
    def _load_details_resource(self, details_id: str) -> Optional[Resource]:
        """Load a video details resource."""
        # Search for the details file in session directories
        for session_dir in self.sessions_path.iterdir():
            if session_dir.is_dir():
                details_file = session_dir / f"{details_id}.json"
                if details_file.exists():
                    with open(details_file, 'r') as f:
                        details_data = json.load(f)
                    
                    return Resource(
                        uri=f"youtube://details/{details_id}",
                        name=f"Video Details ({details_data['video_count']} videos)",
                        description=f"Detailed information for {details_data['video_count']} videos",
                        mimeType="application/json"
                    )
        
        return None
    
    def _load_visualization_resource(self, viz_id: str) -> Optional[Resource]:
        """Load a visualization resource."""
        # Search for the visualization in session directories
        for session_dir in self.visualizations_path.iterdir():
            if session_dir.is_dir():
                viz_dir = session_dir / viz_id
                if viz_dir.exists():
                    metadata_file = viz_dir / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            viz_metadata = json.load(f)
                        
                        return Resource(
                            uri=f"youtube://visualization/{viz_id}",
                            name=f"Visualization: {viz_metadata['viz_type']}",
                            description=f"{viz_metadata['viz_type']} visualization",
                            mimeType="image/png"
                        )
        
        return None
    
    def _load_session_resource(self, session_id: str) -> Optional[Resource]:
        """Load a session overview resource."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return Resource(
            uri=f"youtube://session/{session_id}",
            name=f"Session: {session.title}",
            description=f"Analysis session with {len(session.video_ids)} videos, {len(session.resources)} resources",
            mimeType="application/json"
        )
    
    async def read_resource(self, uri: str) -> Union[TextResourceContents, BlobResourceContents, None]:
        """Read resource contents by URI.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource contents or None if not found
        """
        if not uri.startswith("youtube://"):
            return None
        
        parts = uri[10:].split('/')
        if len(parts) != 2:
            return None
        
        resource_type, resource_id = parts
        
        try:
            if resource_type == "search":
                return await self._read_search_contents(resource_id)
            elif resource_type == "details":
                return await self._read_details_contents(resource_id)
            elif resource_type == "visualization":
                return await self._read_visualization_contents(resource_id)
            elif resource_type == "session":
                return await self._read_session_contents(resource_id)
        except Exception as e:
            logger.error(f"Failed to read resource {uri}: {e}")
        
        return None
    
    async def _read_search_contents(self, search_id: str) -> Optional[TextResourceContents]:
        """Read search resource contents."""
        search_file = self.searches_path / f"{search_id}.json"
        if not search_file.exists():
            return None
        
        with open(search_file, 'r') as f:
            search_data = json.load(f)
        
        return TextResourceContents(
            uri=f"youtube://search/{search_id}",
            mimeType="application/json",
            text=json.dumps(search_data, indent=2)
        )
    
    async def _read_details_contents(self, details_id: str) -> Optional[TextResourceContents]:
        """Read video details resource contents."""
        for session_dir in self.sessions_path.iterdir():
            if session_dir.is_dir():
                details_file = session_dir / f"{details_id}.json"
                if details_file.exists():
                    with open(details_file, 'r') as f:
                        details_data = json.load(f)
                    
                    return TextResourceContents(
                        uri=f"youtube://details/{details_id}",
                        mimeType="application/json",
                        text=json.dumps(details_data, indent=2)
                    )
        
        return None
    
    async def _read_visualization_contents(self, viz_id: str) -> Optional[BlobResourceContents]:
        """Read visualization resource contents."""
        for session_dir in self.visualizations_path.iterdir():
            if session_dir.is_dir():
                viz_dir = session_dir / viz_id
                if viz_dir.exists():
                    # Look for image files
                    for img_file in viz_dir.glob("*.png"):
                        with open(img_file, 'rb') as f:
                            blob_data = f.read()
                        
                        return BlobResourceContents(
                            uri=f"youtube://visualization/{viz_id}",
                            mimeType="image/png",
                            blob=blob_data
                        )
        
        return None
    
    async def _read_session_contents(self, session_id: str) -> Optional[TextResourceContents]:
        """Read session resource contents."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return TextResourceContents(
            uri=f"youtube://session/{session_id}",
            mimeType="application/json",
            text=json.dumps(session.to_dict(), indent=2)
        )
    
    def list_all_resources(self) -> List[Resource]:
        """List all available resources across all sessions."""
        all_resources = []
        
        # Add session resources
        for session in self.sessions.values():
            session_resources = self.get_session_resources(session.session_id)
            all_resources.extend(session_resources)
        
        return all_resources
    
    def cleanup_old_resources(self, max_age_days: int = 30) -> int:
        """Clean up old resources and sessions.
        
        Args:
            max_age_days: Maximum age in days for resources
            
        Returns:
            Number of resources cleaned up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        cleaned_count = 0
        
        # Clean up old sessions
        sessions_to_delete = []
        for session in self.sessions.values():
            if session.updated_at < cutoff_date:
                sessions_to_delete.append(session.session_id)
        
        for session_id in sessions_to_delete:
            if self.delete_session(session_id):
                cleaned_count += 1
        
        # Clean up orphaned search files
        for search_file in self.searches_path.glob("*.json"):
            if datetime.fromtimestamp(search_file.stat().st_mtime) < cutoff_date:
                search_file.unlink()
                cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old resources")
        return cleaned_count