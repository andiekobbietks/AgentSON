"""Tests for opencode reader."""
import json
import sqlite3
import tempfile
import os
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from readers.opencode import OpencodeReader, list_sessions, read


def create_test_db():
    """Create a temporary opencode database for testing."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    
    # Create tables matching opencode schema
    cursor.execute("""
        CREATE TABLE session (
            id TEXT PRIMARY KEY,
            title TEXT,
            time_created INTEGER,
            time_updated INTEGER,
            model TEXT,
            agent TEXT,
            tokens_input INTEGER,
            tokens_output INTEGER,
            cost REAL,
            directory TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE message (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            time_created INTEGER,
            time_updated INTEGER,
            data TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE part (
            id TEXT PRIMARY KEY,
            message_id TEXT,
            session_id TEXT,
            time_created INTEGER,
            time_updated INTEGER,
            data TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE todo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            content TEXT,
            status TEXT,
            priority TEXT,
            position INTEGER
        )
    """)
    
    # Insert test data
    cursor.execute("""
        INSERT INTO session (id, title, time_created, time_updated, model, agent, tokens_input, tokens_output, cost, directory)
        VALUES ('test-session-1', 'Test Session', 1783100000000, 1783100060000, '{"id":"mimo-v2.5-free","providerID":"opencode","variant":"high"}', 'opencode', 1000, 500, 0.0, '/test/dir')
    """)
    
    cursor.execute("""
        INSERT INTO message (id, session_id, time_created, time_updated, data)
        VALUES ('msg-1', 'test-session-1', 1783100000000, 1783100000000, '{"role":"user"}')
    """)
    
    cursor.execute("""
        INSERT INTO message (id, session_id, time_created, time_updated, data)
        VALUES ('msg-2', 'test-session-1', 1783100001000, 1783100001000, '{"role":"assistant"}')
    """)
    
    cursor.execute("""
        INSERT INTO part (id, message_id, session_id, time_created, time_updated, data)
        VALUES ('part-1', 'msg-1', 'test-session-1', 1783100000000, 1783100000000, '{"type":"text","text":"Hello, what is 2+2?"}')
    """)
    
    cursor.execute("""
        INSERT INTO part (id, message_id, session_id, time_created, time_updated, data)
        VALUES ('part-2', 'msg-2', 'test-session-1', 1783100001000, 1783100001000, '{"type":"text","text":"4"}')
    """)
    
    cursor.execute("""
        INSERT INTO part (id, message_id, session_id, time_created, time_updated, data)
        VALUES ('part-3', 'msg-2', 'test-session-1', 1783100002000, 1783100002000, '{"type":"tool-invocation","toolName":"bash","args":{"command":"echo hello"},"result":"hello"}')
    """)
    
    cursor.execute("""
        INSERT INTO todo (session_id, content, status, priority, position)
        VALUES ('test-session-1', 'Complete testing', 'pending', 'high', 1)
    """)
    
    conn.commit()
    return conn


def test_list_sessions():
    """Test listing sessions."""
    conn = create_test_db()
    cursor = conn.cursor()
    
    # Get the temp file path
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    # Create a temp file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    
    # Save in-memory db to file
    conn2 = sqlite3.connect(temp_path)
    conn.backup(conn2)
    conn2.close()
    conn.close()
    
    try:
        sessions = list_sessions(temp_path, limit=10)
        assert len(sessions) == 1
        assert sessions[0]["id"] == "test-session-1"
        assert sessions[0]["title"] == "Test Session"
        print("PASS: test_list_sessions")
    finally:
        os.unlink(temp_path)


def test_read_session():
    """Test reading a full session."""
    conn = create_test_db()
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    
    conn2 = sqlite3.connect(temp_path)
    conn.backup(conn2)
    conn2.close()
    conn.close()
    
    try:
        data = read(temp_path, "test-session-1")
        
        assert data["id"] == "test-session-1"
        assert data["tool"]["name"] == "opencode"
        assert data["agent"]["name"] == "mimo-v2.5-free"
        assert len(data["entries"]) > 0
        
        # Check entry types
        entry_types = [e["type"] for e in data["entries"]]
        assert "user-query" in entry_types
        assert "answer" in entry_types
        assert "action" in entry_types
        assert "side-effect" in entry_types
        
        print("PASS: test_read_session")
    finally:
        os.unlink(temp_path)


def test_agentson_format():
    """Test that output matches AgentSON schema."""
    conn = create_test_db()
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        temp_path = f.name
    
    conn2 = sqlite3.connect(temp_path)
    conn.backup(conn2)
    conn2.close()
    conn.close()
    
    try:
        data = read(temp_path, "test-session-1")
        
        # Check required fields
        assert "$schema" in data
        assert "id" in data
        assert "tool" in data
        assert "agent" in data
        assert "entries" in data
        assert "metadata" in data
        
        # Check tool structure
        assert "name" in data["tool"]
        assert "session_id" in data["tool"]
        
        # Check agent structure
        assert "name" in data["agent"]
        assert "provider" in data["agent"]
        
        print("PASS: test_agentson_format")
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    test_list_sessions()
    test_read_session()
    test_agentson_format()
    print("\nAll tests passed!")