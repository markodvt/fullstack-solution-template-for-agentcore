#!/usr/bin/env python3
"""
Memory API Validation Script

This script validates the AgentCore Memory API response schemas by making
real API calls and documenting the actual response structures.

Usage:
    python validate_memory_api.py --memory-id <memory-id> --region <region>

Requirements:
    - AWS credentials configured
    - Memory ID from deployed stack
    - boto3 installed
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_list_events(client: Any, memory_id: str, actor_id: str) -> Dict[str, Any]:
    """
    Validate ListEvents API response schema.
    
    Args:
        client: boto3 bedrock-agentcore client
        memory_id: Memory ID to query
        actor_id: Actor ID for scoping
        
    Returns:
        Dictionary containing response structure and sample data
    """
    logger.info("Testing ListEvents API...")
    
    try:
        response = client.list_events(
            memoryId=memory_id,
            maxResults=10
        )
        
        logger.info(f"ListEvents response keys: {response.keys()}")
        
        # Document response structure
        result = {
            "api": "ListEvents",
            "success": True,
            "response_keys": list(response.keys()),
            "events_count": len(response.get('events', [])),
            "has_next_token": 'nextToken' in response,
        }
        
        # Sample first event if available
        if response.get('events'):
            first_event = response['events'][0]
            result["sample_event_keys"] = list(first_event.keys())
            result["sample_event"] = first_event
            logger.info(f"Sample event keys: {first_event.keys()}")
        
        return result
        
    except ClientError as e:
        logger.error(f"ListEvents failed: {e}")
        return {
            "api": "ListEvents",
            "success": False,
            "error": str(e)
        }


def validate_retrieve_memory_records(
    client: Any,
    memory_id: str,
    actor_id: str
) -> Dict[str, Any]:
    """
    Validate RetrieveMemoryRecords API response schema.
    
    Args:
        client: boto3 bedrock-agentcore client
        memory_id: Memory ID to query
        actor_id: Actor ID for scoping
        
    Returns:
        Dictionary containing response structure and sample data
    """
    logger.info("Testing RetrieveMemoryRecords API...")
    
    # Test each memory strategy namespace
    namespaces = [
        f"/summaries/{actor_id}",
        f"/preferences/{actor_id}",
        f"/facts/{actor_id}"
    ]
    
    results = []
    
    for namespace in namespaces:
        try:
            response = client.retrieve_memory_records(
                memoryId=memory_id,
                namespace=namespace,
                maxResults=10
            )
            
            logger.info(f"RetrieveMemoryRecords ({namespace}) response keys: {response.keys()}")
            
            # Document response structure
            result = {
                "api": "RetrieveMemoryRecords",
                "namespace": namespace,
                "success": True,
                "response_keys": list(response.keys()),
                "records_count": len(response.get('memoryRecords', [])),
                "has_next_token": 'nextToken' in response,
            }
            
            # Sample first record if available
            if response.get('memoryRecords'):
                first_record = response['memoryRecords'][0]
                result["sample_record_keys"] = list(first_record.keys())
                result["sample_record"] = first_record
                logger.info(f"Sample record keys for {namespace}: {first_record.keys()}")
            
            results.append(result)
            
        except ClientError as e:
            logger.warning(f"RetrieveMemoryRecords ({namespace}) failed: {e}")
            results.append({
                "api": "RetrieveMemoryRecords",
                "namespace": namespace,
                "success": False,
                "error": str(e)
            })
    
    return results


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description='Validate AgentCore Memory API response schemas'
    )
    parser.add_argument(
        '--memory-id',
        required=True,
        help='Memory ID from deployed stack'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    parser.add_argument(
        '--actor-id',
        default='test-user',
        help='Actor ID for testing (default: test-user)'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Validating Memory API with Memory ID: {args.memory_id}")
    logger.info(f"Region: {args.region}")
    logger.info(f"Actor ID: {args.actor_id}")
    
    # Initialize boto3 client
    try:
        client = boto3.client('bedrock-agentcore', region_name=args.region)
    except Exception as e:
        logger.error(f"Failed to create boto3 client: {e}")
        sys.exit(1)
    
    # Validate APIs
    validation_results = {
        "memory_id": args.memory_id,
        "region": args.region,
        "actor_id": args.actor_id,
        "validations": []
    }
    
    # Test ListEvents
    list_events_result = validate_list_events(client, args.memory_id, args.actor_id)
    validation_results["validations"].append(list_events_result)
    
    # Test RetrieveMemoryRecords
    retrieve_results = validate_retrieve_memory_records(
        client,
        args.memory_id,
        args.actor_id
    )
    validation_results["validations"].extend(retrieve_results)
    
    # Save results to file
    output_file = "memory_api_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    logger.info(f"Validation results saved to {output_file}")
    
    # Print summary
    print("\n" + "="*80)
    print("MEMORY API VALIDATION SUMMARY")
    print("="*80)
    
    for validation in validation_results["validations"]:
        api = validation.get("api")
        namespace = validation.get("namespace", "N/A")
        success = validation.get("success")
        
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"\n{api} ({namespace}): {status}")
        
        if success:
            if "sample_event_keys" in validation:
                print(f"  Event keys: {validation['sample_event_keys']}")
            if "sample_record_keys" in validation:
                print(f"  Record keys: {validation['sample_record_keys']}")
        else:
            print(f"  Error: {validation.get('error')}")
    
    print("\n" + "="*80)
    print(f"Full results saved to: {output_file}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
