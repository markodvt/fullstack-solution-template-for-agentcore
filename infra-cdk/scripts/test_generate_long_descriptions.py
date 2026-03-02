#!/usr/bin/env python3
"""
Unit tests for generate-long-descriptions.py

Tests the docstring and system prompt extraction functions to ensure
they correctly parse Python source code.
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent))

from generate_long_descriptions import extract_docstring, extract_system_prompt


class TestExtractDocstring(unittest.TestCase):
    """Test cases for extract_docstring function."""

    def test_extract_simple_docstring(self):
        """Test extraction of a simple module docstring."""
        source = '''"""
This is a simple docstring.
"""

import os
'''
        result = extract_docstring(source)
        self.assertEqual(result, "This is a simple docstring.")

    def test_extract_multiline_docstring(self):
        """Test extraction of a multi-line docstring."""
        source = '''"""
UMich Agent - A helpful assistant who LOVES the University of Michigan.

This agent has access to HTTP requests and current time tools, making it useful
for fetching web content and providing time-based information.
"""

import os
'''
        result = extract_docstring(source)
        self.assertIn("UMich Agent", result)
        self.assertIn("University of Michigan", result)

    def test_extract_docstring_with_comments(self):
        """Test extraction when there are comments before the docstring."""
        source = '''# This is a comment
# Another comment

"""
This is the docstring.
"""

import os
'''
        result = extract_docstring(source)
        self.assertEqual(result, "This is the docstring.")

    def test_no_docstring(self):
        """Test when there is no docstring."""
        source = '''import os

def main():
    pass
'''
        result = extract_docstring(source)
        self.assertEqual(result, "")

    def test_single_quotes_docstring(self):
        """Test extraction with single quotes."""
        source = """'''
This is a docstring with single quotes.
'''

import os
"""
        result = extract_docstring(source)
        self.assertEqual(result, "This is a docstring with single quotes.")


class TestExtractSystemPrompt(unittest.TestCase):
    """Test cases for extract_system_prompt function."""

    def test_extract_simple_system_prompt(self):
        """Test extraction of a simple system prompt."""
        source = '''
def create_agent():
    system_prompt = """You are a helpful assistant."""
    return Agent(system_prompt=system_prompt)
'''
        result = extract_system_prompt(source)
        self.assertEqual(result, "You are a helpful assistant.")

    def test_extract_multiline_system_prompt(self):
        """Test extraction of a multi-line system prompt."""
        source = '''
def create_agent():
    system_prompt = """You are a helpful assistant who LOVES the University of Michigan.

You have access to:
- Short-term memory: Recent conversation history
- Long-term memory: User preferences and facts
- Tools: http_request, current_time"""
    
    return Agent(system_prompt=system_prompt)
'''
        result = extract_system_prompt(source)
        self.assertIn("University of Michigan", result)
        self.assertIn("Short-term memory", result)
        self.assertIn("Tools:", result)

    def test_extract_system_prompt_single_quotes(self):
        """Test extraction with single quotes."""
        source = """
def create_agent():
    system_prompt = '''You are a helpful assistant.'''
    return Agent(system_prompt=system_prompt)
"""
        result = extract_system_prompt(source)
        self.assertEqual(result, "You are a helpful assistant.")

    def test_no_system_prompt(self):
        """Test when there is no system prompt."""
        source = '''
def create_agent():
    return Agent()
'''
        result = extract_system_prompt(source)
        self.assertEqual(result, "")

    def test_system_prompt_with_formatting(self):
        """Test extraction preserves formatting."""
        source = '''
def create_agent():
    system_prompt = """You are a helpful assistant.

When responding:
- Reference relevant information
- Learn and remember preferences
- Show enthusiasm"""
    
    return Agent(system_prompt=system_prompt)
'''
        result = extract_system_prompt(source)
        self.assertIn("When responding:", result)
        self.assertIn("- Reference relevant information", result)


class TestIntegration(unittest.TestCase):
    """Integration tests using real agent file structure."""

    def test_extract_from_umich_agent_structure(self):
        """Test extraction from a structure similar to umich_agent.py."""
        source = '''"""
UMich Agent - A helpful assistant who LOVES the University of Michigan.

This agent has access to HTTP requests and current time tools.
"""

import os
from strands import Agent

def create_umich_agent(user_id: str, session_id: str) -> Agent:
    """
    Create the UMich agent with memory integration and tools.
    """
    system_prompt = """You are a helpful assistant who LOVES the University of Michigan.

You have access to:
- Short-term memory: Recent conversation history
- Long-term memory: User preferences and facts"""

    agent = Agent(
        name="UMichAgent",
        system_prompt=system_prompt
    )
    
    return agent
'''
        docstring = extract_docstring(source)
        system_prompt = extract_system_prompt(source)
        
        self.assertIn("UMich Agent", docstring)
        self.assertIn("University of Michigan", docstring)
        self.assertIn("University of Michigan", system_prompt)
        self.assertIn("Short-term memory", system_prompt)


if __name__ == '__main__':
    unittest.main()
