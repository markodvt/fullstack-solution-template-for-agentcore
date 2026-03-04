#!/usr/bin/env python3
"""
Bug Condition Exploration Test for Memory API Parameter Validation

This script tests the Memory API Lambda to confirm the parameter validation bugs exist
on unfixed code. It validates the root cause analysis by testing:

1. list_events() call without actorId/sessionId URI parameters (should fail)
2. retrieve_memory_records() method call (should fail with AttributeError)
3. list_memory_records() call with correct parameters (should succeed)
4. list_events() call with correct actorId/sessionId URI parameters (should succeed)

Expected Outcome:
- Tests 1 and 2 MUST FAIL on unfixed code (confirming the bug exists)
- Tests 3 and 4 should succeed (confirming correct API signatures)

Usage:
    python test_memory_api_bug.py

Environment Variables Required:
    AWS_REGION: AWS region (default: us-east-1)
    MEMORY_ID: AgentCore Memory ID (required)
    TEST_ACTOR_ID: Test user ID (default: test-user-123)
    TEST_SESSION_ID: Test session ID (default: test-session-456)
"""

import os
import sys
from typing import Dict, Any, Tuple

import boto3
from botocore.exceptions import ClientError, ParamValidationError


class MemoryApiBugTester:
    """Test harness for Memory API parameter validation bugs"""

    def __init__(self):
        """Initialize the test harness with AWS clients and test data"""
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.memory_id = os.environ.get("MEMORY_ID")
        self.test_actor_id = os.environ.get("TEST_ACTOR_ID", "test-user-123")
        self.test_session_id = os.environ.get("TEST_SESSION_ID", "test-session-456")
        
        if not self.memory_id:
            raise ValueError("MEMORY_ID environment variable is required")
        
        self.agentcore_client = boto3.client("bedrock-agentcore", region_name=self.region)
        self.test_results: Dict[str, Dict[str, Any]] = {}

    def test_list_events_without_uri_parameters(self) -> Tuple[bool, str, str]:
        """
        Test 1: list_events() without actorId/sessionId URI parameters
        
        Expected: Should fail with "Missing required parameter" error on unfixed code
        
        Returns:
            Tuple of (test_passed, error_type, error_message)
        """
        print("\n" + "="*80)
        print("TEST 1: list_events() without actorId/sessionId URI parameters")
        print("="*80)
        print(f"Testing with memoryId={self.memory_id}")
        print("Expected: ParamValidationError or ClientError about missing parameters")
        
        try:
            # This is the INCORRECT call from the unfixed code
            response = self.agentcore_client.list_events(
                memoryId=self.memory_id,
                maxResults=50
            )
            
            # If we get here, the test FAILED (bug doesn't exist)
            print("❌ UNEXPECTED: API call succeeded without required parameters")
            print(f"Response: {response}")
            return False, "NoError", "API call succeeded unexpectedly"
            
        except ParamValidationError as e:
            # Expected error - missing required parameters
            error_msg = str(e)
            print(f"✅ EXPECTED: ParamValidationError - {error_msg}")
            
            # Check if error mentions missing actorId or sessionId
            if "actorId" in error_msg or "sessionId" in error_msg:
                print("✅ CONFIRMED: Error mentions missing actorId or sessionId")
                return True, "ParamValidationError", error_msg
            else:
                print(f"⚠️  WARNING: Error doesn't mention actorId/sessionId: {error_msg}")
                return True, "ParamValidationError", error_msg
                
        except ClientError as e:
            # Also acceptable - AWS API validation error
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            print(f"✅ EXPECTED: ClientError [{error_code}] - {error_msg}")
            
            # Check if error mentions missing parameters
            if "parameter" in error_msg.lower() or "required" in error_msg.lower():
                print("✅ CONFIRMED: Error mentions missing required parameters")
                return True, error_code, error_msg
            else:
                print(f"⚠️  WARNING: Error doesn't mention parameters: {error_msg}")
                return True, error_code, error_msg
                
        except Exception as e:
            # Unexpected error type
            print(f"❌ UNEXPECTED ERROR: {type(e).__name__} - {str(e)}")
            return False, type(e).__name__, str(e)

    def test_retrieve_memory_records_method(self) -> Tuple[bool, str, str]:
        """
        Test 2: retrieve_memory_records() method call
        
        Expected: Should fail with AttributeError on unfixed code
        
        Returns:
            Tuple of (test_passed, error_type, error_message)
        """
        print("\n" + "="*80)
        print("TEST 2: retrieve_memory_records() method call")
        print("="*80)
        print("Testing if retrieve_memory_records() method exists")
        print("Expected: AttributeError - method does not exist")
        
        try:
            # Check if method exists
            if not hasattr(self.agentcore_client, "retrieve_memory_records"):
                print("✅ EXPECTED: retrieve_memory_records() method does not exist")
                return True, "AttributeError", "'AgentCore' object has no attribute 'retrieve_memory_records'"
            
            # If method exists, try calling it (this is the INCORRECT call from unfixed code)
            print("⚠️  WARNING: Method exists, attempting to call it...")
            response = self.agentcore_client.retrieve_memory_records(
                memoryId=self.memory_id,
                searchCriteria={"searchQuery": "*"},
                namespace=f"/summaries/{self.test_actor_id}",
                maxResults=50
            )
            
            # If we get here, the test FAILED (method exists and works)
            print("❌ UNEXPECTED: retrieve_memory_records() method exists and succeeded")
            print(f"Response: {response}")
            return False, "NoError", "Method exists and succeeded unexpectedly"
            
        except AttributeError as e:
            # Expected error - method doesn't exist
            error_msg = str(e)
            print(f"✅ EXPECTED: AttributeError - {error_msg}")
            return True, "AttributeError", error_msg
            
        except Exception as e:
            # Unexpected error type
            print(f"❌ UNEXPECTED ERROR: {type(e).__name__} - {str(e)}")
            return False, type(e).__name__, str(e)

    def test_list_memory_records_with_correct_parameters(self) -> Tuple[bool, str, str]:
        """
        Test 3: list_memory_records() with correct parameters
        
        Expected: Should succeed (confirming correct API signature)
        
        Returns:
            Tuple of (test_passed, error_type, error_message)
        """
        print("\n" + "="*80)
        print("TEST 3: list_memory_records() with correct parameters")
        print("="*80)
        print(f"Testing with memoryId={self.memory_id}")
        print(f"Testing with namespace=/summaries/{self.test_actor_id}")
        print("Expected: Success (HTTP 200) or ResourceNotFound (if namespace doesn't exist)")
        
        try:
            # This is the CORRECT call with proper parameters
            response = self.agentcore_client.list_memory_records(
                memoryId=self.memory_id,
                namespace=f"/summaries/{self.test_actor_id}",
                maxResults=50
            )
            
            # Success - correct API signature works
            record_count = len(response.get("memoryRecords", []))
            print(f"✅ SUCCESS: API call succeeded, returned {record_count} records")
            print(f"Response keys: {list(response.keys())}")
            return True, "Success", f"Returned {record_count} records"
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            
            # ResourceNotFound is acceptable - namespace might not exist yet
            if error_code == "ResourceNotFoundException":
                print(f"✅ ACCEPTABLE: ResourceNotFoundException - {error_msg}")
                print("(This is expected if the namespace doesn't exist yet)")
                return True, error_code, error_msg
            
            # Other errors indicate API signature issues
            print(f"❌ UNEXPECTED ERROR: [{error_code}] - {error_msg}")
            return False, error_code, error_msg
            
        except ParamValidationError as e:
            # Parameter validation error - API signature is wrong
            error_msg = str(e)
            print(f"❌ UNEXPECTED: ParamValidationError - {error_msg}")
            print("This suggests the API signature is incorrect")
            return False, "ParamValidationError", error_msg
            
        except Exception as e:
            # Unexpected error type
            print(f"❌ UNEXPECTED ERROR: {type(e).__name__} - {str(e)}")
            return False, type(e).__name__, str(e)

    def test_list_events_with_correct_uri_parameters(self) -> Tuple[bool, str, str]:
        """
        Test 4: list_events() with correct actorId/sessionId URI parameters
        
        Expected: Should succeed (confirming correct API signature)
        
        Returns:
            Tuple of (test_passed, error_type, error_message)
        """
        print("\n" + "="*80)
        print("TEST 4: list_events() with correct actorId/sessionId URI parameters")
        print("="*80)
        print(f"Testing with memoryId={self.memory_id}")
        print(f"Testing with actorId={self.test_actor_id}")
        print(f"Testing with sessionId={self.test_session_id}")
        print("Expected: Success (HTTP 200) or ResourceNotFound (if session doesn't exist)")
        
        try:
            # This is the CORRECT call with proper URI parameters
            response = self.agentcore_client.list_events(
                memoryId=self.memory_id,
                actorId=self.test_actor_id,
                sessionId=self.test_session_id,
                maxResults=50
            )
            
            # Success - correct API signature works
            event_count = len(response.get("events", []))
            print(f"✅ SUCCESS: API call succeeded, returned {event_count} events")
            print(f"Response keys: {list(response.keys())}")
            return True, "Success", f"Returned {event_count} events"
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            
            # ResourceNotFound is acceptable - session might not exist yet
            if error_code == "ResourceNotFoundException":
                print(f"✅ ACCEPTABLE: ResourceNotFoundException - {error_msg}")
                print("(This is expected if the session doesn't exist yet)")
                return True, error_code, error_msg
            
            # Other errors indicate API signature issues
            print(f"❌ UNEXPECTED ERROR: [{error_code}] - {error_msg}")
            return False, error_code, error_msg
            
        except ParamValidationError as e:
            # Parameter validation error - API signature is wrong
            error_msg = str(e)
            print(f"❌ UNEXPECTED: ParamValidationError - {error_msg}")
            print("This suggests the API signature is incorrect")
            return False, "ParamValidationError", error_msg
            
        except Exception as e:
            # Unexpected error type
            print(f"❌ UNEXPECTED ERROR: {type(e).__name__} - {str(e)}")
            return False, type(e).__name__, str(e)

    def run_all_tests(self) -> bool:
        """
        Run all bug condition exploration tests
        
        Returns:
            True if all tests passed (bug confirmed), False otherwise
        """
        print("\n" + "="*80)
        print("MEMORY API BUG CONDITION EXPLORATION TEST")
        print("="*80)
        print(f"Memory ID: {self.memory_id}")
        print(f"Test Actor ID: {self.test_actor_id}")
        print(f"Test Session ID: {self.test_session_id}")
        print(f"AWS Region: {self.region}")
        
        # Run all tests
        test1_passed, test1_error_type, test1_error_msg = self.test_list_events_without_uri_parameters()
        test2_passed, test2_error_type, test2_error_msg = self.test_retrieve_memory_records_method()
        test3_passed, test3_error_type, test3_error_msg = self.test_list_memory_records_with_correct_parameters()
        test4_passed, test4_error_type, test4_error_msg = self.test_list_events_with_correct_uri_parameters()
        
        # Store results
        self.test_results = {
            "test1_list_events_without_params": {
                "passed": test1_passed,
                "error_type": test1_error_type,
                "error_message": test1_error_msg
            },
            "test2_retrieve_memory_records": {
                "passed": test2_passed,
                "error_type": test2_error_type,
                "error_message": test2_error_msg
            },
            "test3_list_memory_records_correct": {
                "passed": test3_passed,
                "error_type": test3_error_type,
                "error_message": test3_error_msg
            },
            "test4_list_events_correct": {
                "passed": test4_passed,
                "error_type": test4_error_type,
                "error_message": test4_error_msg
            }
        }
        
        # Print summary
        self.print_summary()
        
        # Overall result: Tests 1 and 2 should fail (confirming bug), Tests 3 and 4 should succeed
        bug_confirmed = test1_passed and test2_passed
        correct_apis_work = test3_passed and test4_passed
        
        return bug_confirmed and correct_apis_work

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"\n{test_name}: {status}")
            print(f"  Error Type: {result['error_type']}")
            print(f"  Error Message: {result['error_message'][:100]}...")
        
        # Overall assessment
        print("\n" + "="*80)
        print("OVERALL ASSESSMENT")
        print("="*80)
        
        test1_passed = self.test_results["test1_list_events_without_params"]["passed"]
        test2_passed = self.test_results["test2_retrieve_memory_records"]["passed"]
        test3_passed = self.test_results["test3_list_memory_records_correct"]["passed"]
        test4_passed = self.test_results["test4_list_events_correct"]["passed"]
        
        if test1_passed and test2_passed:
            print("✅ BUG CONFIRMED: Incorrect API calls fail as expected")
            print("   - list_events() without URI parameters fails")
            print("   - retrieve_memory_records() method does not exist")
        else:
            print("❌ BUG NOT CONFIRMED: Incorrect API calls did not fail as expected")
            print("   This suggests the bug may not exist or root cause is different")
        
        if test3_passed and test4_passed:
            print("✅ CORRECT API SIGNATURES VALIDATED: Correct API calls succeed")
            print("   - list_memory_records() with correct parameters works")
            print("   - list_events() with correct URI parameters works")
        else:
            print("❌ CORRECT API SIGNATURES FAILED: Correct API calls did not succeed")
            print("   This suggests the API signatures may be incorrect")
        
        print("\n" + "="*80)
        print("COUNTEREXAMPLES FOUND:")
        print("="*80)
        
        if test1_passed:
            print(f"\n1. list_events() without actorId/sessionId:")
            print(f"   Error: {self.test_results['test1_list_events_without_params']['error_type']}")
            print(f"   Message: {self.test_results['test1_list_events_without_params']['error_message']}")
        
        if test2_passed:
            print(f"\n2. retrieve_memory_records() method:")
            print(f"   Error: {self.test_results['test2_retrieve_memory_records']['error_type']}")
            print(f"   Message: {self.test_results['test2_retrieve_memory_records']['error_message']}")


def main():
    """Main entry point for the test script"""
    try:
        tester = MemoryApiBugTester()
        success = tester.run_all_tests()
        
        if success:
            print("\n✅ ALL TESTS PASSED: Bug confirmed, ready to implement fix")
            sys.exit(0)
        else:
            print("\n❌ SOME TESTS FAILED: Review results and adjust root cause analysis")
            sys.exit(1)
            
    except ValueError as e:
        print(f"\n❌ CONFIGURATION ERROR: {e}")
        print("\nRequired environment variables:")
        print("  MEMORY_ID: AgentCore Memory ID (required)")
        print("  AWS_REGION: AWS region (optional, default: us-east-1)")
        print("  TEST_ACTOR_ID: Test user ID (optional, default: test-user-123)")
        print("  TEST_SESSION_ID: Test session ID (optional, default: test-session-456)")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
