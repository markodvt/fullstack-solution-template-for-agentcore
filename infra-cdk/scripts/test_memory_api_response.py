#!/usr/bin/env python3
"""
Test Memory API Response Structure

This script calls the AgentCore Memory API to see the actual response structure.
Run this to understand what the Memory API actually returns before implementing
frontend features that depend on it.
"""

import boto3
import json
import sys
from typing import Dict, Any


def test_list_memory_records(memory_id: str, actor_id: str) -> None:
    """
    Test ListMemoryRecords API and print actual response.
    
    Args:
        memory_id: The Memory ID from SSM parameter store
        actor_id: The Cognito user ID (sub claim from JWT)
    """
    client = boto3.client('bedrock-agentcore', region_name='us-east-1')
    
    # Test each namespace based on memory strategies in backend-stack.ts
    namespaces = [
        f"/summaries/{actor_id}",
        f"/preferences/{actor_id}",
        f"/facts/{actor_id}"
    ]
    
    for namespace in namespaces:
        print(f"\n{'='*80}")
        print(f"Testing namespace: {namespace}")
        print('='*80)
        
        try:
            response = client.list_memory_records(
                memoryId=memory_id,
                namespace=namespace,
                maxResults=5
            )
            
            print(f"\nResponse keys: {list(response.keys())}")
            print(f"Number of records: {len(response.get('memoryRecordSummaries', []))}")
            
            if response.get('memoryRecordSummaries'):
                print(f"\nFirst record structure:")
                first_record = response['memoryRecordSummaries'][0]
                print(json.dumps(first_record, indent=2, default=str))
                
                print(f"\nAll record keys in first record:")
                print(list(first_record.keys()))
            else:
                print("\nNo records found in this namespace")
                
        except Exception as e:
            print(f"\nError calling API: {type(e).__name__}: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_memory_api_response.py <memory-id> <actor-id>")
        print("\nExample:")
        print("  python test_memory_api_response.py marodonfastmarodonfastbackend8EA31761-64aLtD8bP1 a4a844c8-7061-70fb-bc1a-510f17246eb3")
        sys.exit(1)
    
    memory_id = sys.argv[1]
    actor_id = sys.argv[2]
    
    print(f"Memory ID: {memory_id}")
    print(f"Actor ID: {actor_id}")
    
    # Test the API
    test_list_memory_records(memory_id, actor_id)
    
    print(f"\n{'='*80}")
    print("Test complete!")
    print('='*80)
