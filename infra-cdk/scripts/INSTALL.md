# Installation Instructions for Post-Deployment Scripts

## Quick Start

```bash
# Install dependencies
pip install -r infra-cdk/scripts/requirements.txt

# Run the script
python infra-cdk/scripts/generate-long-descriptions.py
```

## Detailed Instructions

### 1. Install Python Dependencies

The scripts require Python 3.8 or higher and the following packages:

```bash
pip install boto3>=1.34.0 pyyaml>=6.0.1
```

Or install from the requirements file:

```bash
pip install -r infra-cdk/scripts/requirements.txt
```

### 2. Configure AWS Credentials

Ensure your AWS credentials are configured. You can use:

**Option A: AWS CLI Configuration**
```bash
aws configure
```

**Option B: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

**Option C: AWS Profile**
```bash
export AWS_PROFILE=your_profile_name
```

### 3. Verify Installation

Test that all dependencies are available:

```bash
python3 -c "import boto3, yaml; print('✓ All dependencies installed')"
```

### 4. Run the Script

```bash
python infra-cdk/scripts/generate-long-descriptions.py
```

## Troubleshooting

### ModuleNotFoundError: No module named 'yaml'

Install PyYAML:
```bash
pip install pyyaml
```

### ModuleNotFoundError: No module named 'boto3'

Install boto3:
```bash
pip install boto3
```

### AWS Credentials Not Found

Configure AWS credentials using one of the methods above.

### Permission Denied

Make sure the script is executable:
```bash
chmod +x infra-cdk/scripts/generate-long-descriptions.py
```

## Virtual Environment (Recommended)

For isolated dependency management:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r infra-cdk/scripts/requirements.txt

# Run script
python infra-cdk/scripts/generate-long-descriptions.py

# Deactivate when done
deactivate
```
