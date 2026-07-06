#!/usr/bin/env python3
"""
Simple CLI test script for AgentSON
This bypasses the Windows executable installation issue.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "agentsong")))

from cli.main import main

if __name__ == "__main__":
    main()
