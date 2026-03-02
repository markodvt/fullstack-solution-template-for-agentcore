#!/usr/bin/env python3
"""
Unit tests for get-cognito-token.py helper script.

Tests the core functionality of the Cognito token retrieval script.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the scripts directory to the path
sys.path.insert(0, str(Path(__file__).parent))

# Import the module to test
import importlib.util
spec = importlib.util.spec_from_file_location(
    "get_cognito_token",
    Path(__file__).parent / "get-cognito-token.py"
)
get_cognito_token = importlib.util.module_from_spec(spec)
spec.loader.exec_module(get_cognito_token)


class TestGetCognitoToken(unittest.TestCase):
    """Test cases for get-cognito-token.py helper script."""

    def test_load_config_success(self):
        """Test that load_config successfully reads config.yaml."""
        with patch('builtins.open', unittest.mock.mock_open(read_data='stack_name_base: test-stack\n')):
            with patch('pathlib.Path.exists', return_value=True):
                config = get_cognito_token.load_config()
                self.assertIn('stack_name_base', config)
                self.assertEqual(config['stack_name_base'], 'test-stack')

    def test_load_config_missing_file(self):
        """Test that load_config raises FileNotFoundError when config.yaml is missing."""
        with patch('pathlib.Path.exists', return_value=False):
            with self.assertRaises(FileNotFoundError):
                get_cognito_token.load_config()

    def test_get_credentials_from_args(self):
        """Test that get_credentials prioritizes command line arguments."""
        username, password = get_cognito_token.get_credentials('user1', 'pass1')
        self.assertEqual(username, 'user1')
        self.assertEqual(password, 'pass1')

    def test_get_credentials_from_env(self):
        """Test that get_credentials uses environment variables when args are None."""
        with patch.dict(os.environ, {'COGNITO_USERNAME': 'user2', 'COGNITO_PASSWORD': 'pass2'}):
            username, password = get_cognito_token.get_credentials(None, None)
            self.assertEqual(username, 'user2')
            self.assertEqual(password, 'pass2')

    def test_get_cognito_config_success(self):
        """Test that get_cognito_config successfully retrieves SSM parameters."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameters.return_value = {
            'Parameters': [
                {'Name': '/test-stack/cognito/user-pool-id', 'Value': 'us-east-1_ABC123'},
                {'Name': '/test-stack/cognito/client-id', 'Value': 'abc123def456'}
            ]
        }
        
        user_pool_id, client_id = get_cognito_token.get_cognito_config(mock_ssm, 'test-stack')
        
        self.assertEqual(user_pool_id, 'us-east-1_ABC123')
        self.assertEqual(client_id, 'abc123def456')
        mock_ssm.get_parameters.assert_called_once()

    def test_get_cognito_config_missing_params(self):
        """Test that get_cognito_config raises ValueError when parameters are missing."""
        mock_ssm = MagicMock()
        mock_ssm.get_parameters.return_value = {
            'Parameters': [
                {'Name': '/test-stack/cognito/user-pool-id', 'Value': 'us-east-1_ABC123'}
            ]
        }
        
        with self.assertRaises(ValueError) as context:
            get_cognito_token.get_cognito_config(mock_ssm, 'test-stack')
        
        self.assertIn('Missing parameters', str(context.exception))

    def test_authenticate_with_cognito_success(self):
        """Test successful authentication with Cognito."""
        mock_cognito = MagicMock()
        mock_cognito.initiate_auth.return_value = {
            'AuthenticationResult': {
                'IdToken': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                'AccessToken': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
                'RefreshToken': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
            }
        }
        
        token = get_cognito_token.authenticate_with_cognito(
            mock_cognito,
            'abc123def456',
            'testuser',
            'testpass'
        )
        
        self.assertEqual(token, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...')
        mock_cognito.initiate_auth.assert_called_once_with(
            ClientId='abc123def456',
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': 'testuser',
                'PASSWORD': 'testpass'
            }
        )

    def test_authenticate_with_cognito_no_auth_result(self):
        """Test authentication failure when no AuthenticationResult is returned."""
        mock_cognito = MagicMock()
        mock_cognito.initiate_auth.return_value = {}
        
        with self.assertRaises(ValueError) as context:
            get_cognito_token.authenticate_with_cognito(
                mock_cognito,
                'abc123def456',
                'testuser',
                'testpass'
            )
        
        self.assertIn('No AuthenticationResult', str(context.exception))

    def test_authenticate_with_cognito_no_id_token(self):
        """Test authentication failure when no IdToken is returned."""
        mock_cognito = MagicMock()
        mock_cognito.initiate_auth.return_value = {
            'AuthenticationResult': {
                'AccessToken': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
            }
        }
        
        with self.assertRaises(ValueError) as context:
            get_cognito_token.authenticate_with_cognito(
                mock_cognito,
                'abc123def456',
                'testuser',
                'testpass'
            )
        
        self.assertIn('No IdToken', str(context.exception))


if __name__ == '__main__':
    unittest.main()
