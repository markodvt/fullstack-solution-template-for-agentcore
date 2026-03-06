# URLA (Form 1003) Synthetic Data Generation Specification

## Section 1: Borrower Information

### 1a. Personal Information
- **First Name**: Common first names (string, 2-20 chars)
- **Middle Name**: Common middle names or initial (string, 0-20 chars, 30% null)
- **Last Name**: Common surnames (string, 2-30 chars)
- **Suffix**: Jr., Sr., II, III, IV (5% of records)
- **SSN**: Format XXX-XX-XXXX (string, 11 chars with dashes)
- **Date of Birth**: Range 1944-2005 (age 18-80)
- **Citizenship**: US Citizen, Permanent Resident, Non-Permanent Resident (80%, 15%, 5%)
- **Marital Status**: Married, Unmarried, Separated (50%, 45%, 5%)

### 1b. Contact Information
- **Home Phone**: Format (XXX) XXX-XXXX (optional, 60% populated)
- **Cell Phone**: Format (XXX) XXX-XXXX (95% populated)
- **Work Phone**: Format (XXX) XXX-XXXX (optional, 40% populated)
- **Email**: firstname.lastname@domain.com (95% populated)

### 1c. Current Address
- **Street Address**: Realistic street addresses
- **Unit #**: Apt/Unit number (20% of records)
- **City**: US cities
- **State**: US state codes (2 chars)
- **ZIP**: 5-digit ZIP codes
- **Country**: USA (default)
- **Housing Status**: Own, Rent, Living Rent Free (35%, 60%, 5%)
- **Years at Address**: 0-30 years
- **Months at Address**: 0-11 months

### 1d. Mailing Address (if different)
- Same fields as current address (10% of borrowers have different mailing address)

### 1e. Former Address (if < 2 years at current)
- Same fields as current address

## Section 2: Financial Information - Employment

### 2a. Current Employment
- **Employer Name**: Company names
- **Phone**: Format (XXX) XXX-XXXX
- **Street Address**: Business addresses
- **City, State, ZIP**: US locations
- **Position/Title**: Job titles
- **Start Date**: Within last 0-30 years
- **Employment Type**: W2, Self-Employed, Retired, Other (70%, 15%, 10%, 5%)
- **Years on Job**: 0-30 years
- **Months on Job**: 0-11 months
- **Gross Monthly Income**: $2,000 - $50,000
  - Base: $2,000 - $40,000
  - Overtime: $0 - $2,000 (30% have)
  - Bonus: $0 - $10,000 (40% have)
  - Commission: $0 - $5,000 (20% have)

### 2b. Previous Employment (if < 2 years at current)
- Same fields as current employment

### 2c. Additional Income (Optional, 30% of borrowers)
- **Income Type**: Alimony, Child Support, Investment, Rental, Other
- **Monthly Amount**: $200 - $5,000

## Section 3: Financial Information - Assets

### 3a. Bank Accounts
- **Account Type**: Checking, Savings, Money Market, CD (50%, 30%, 15%, 5%)
- **Financial Institution**: Bank names
- **Account Number**: 8-12 digit string
- **Balance**: $500 - $500,000 (log-normal distribution)
- **Number of Accounts**: 1-5 per borrower

### 3b. Retirement Accounts
- **Account Type**: 401k, IRA, Pension (60%, 30%, 10%)
- **Institution**: Financial institution names
- **Balance**: $5,000 - $2,000,000 (40% of borrowers)

### 3c. Stocks/Bonds
- **Value**: $1,000 - $500,000 (20% of borrowers)

### 3d. Other Assets
- **Type**: Vehicle, Other Real Estate, Business, Life Insurance
- **Value**: $5,000 - $1,000,000

## Section 4: Financial Information - Liabilities

### 4a. Credit Cards
- **Creditor Name**: Credit card companies
- **Account Number**: Last 4 digits (XXXX)
- **Monthly Payment**: $25 - $500
- **Balance**: $0 - $25,000
- **To Be Paid Off**: Yes/No (20% yes)
- **Number of Cards**: 0-5 per borrower (avg 2.5)

### 4b. Auto Loans
- **Creditor**: Auto lenders
- **Monthly Payment**: $200 - $800
- **Balance**: $5,000 - $60,000
- **Months Remaining**: 6-72 months
- **Percentage with Auto Loan**: 60%

### 4c. Student Loans
- **Creditor**: Student loan servicers
- **Monthly Payment**: $100 - $1,000
- **Balance**: $5,000 - $150,000
- **Percentage with Student Loans**: 35%

### 4d. Other Liabilities
- **Type**: Personal Loan, Alimony, Child Support, Other
- **Monthly Payment**: $100 - $2,000
- **Balance**: $1,000 - $50,000

## Section 5: Loan and Property Information

### 5a. Loan Information
- **Loan Amount**: $50,000 - $1,500,000
- **Loan Purpose**: Purchase, Refinance, Cash-Out Refinance (60%, 30%, 10%)
- **Loan Type**: Conventional, FHA, VA, USDA (70%, 20%, 8%, 2%)
- **Loan Term**: 15, 20, 30 years (15%, 10%, 75%)
- **Interest Rate**: 2.5% - 8.0%

### 5b. Property Information
- **Property Address**: Different from current address if purchase
- **Property Type**: Single Family, Condo, Townhouse, Multi-Family (70%, 15%, 10%, 5%)
- **Property Value**: $75,000 - $2,000,000
- **Occupancy**: Primary Residence, Secondary, Investment (85%, 10%, 5%)
- **Number of Units**: 1-4

### 5c. Down Payment
- **Amount**: 3% - 30% of property value
- **Source**: Savings, Gift, Sale of Property, Other (70%, 15%, 10%, 5%)

## Section 6: Declarations

### 6a. Yes/No Questions (Realistic distributions)
- **Outstanding Judgments**: 5% Yes
- **Bankruptcy (past 7 years)**: 3% Yes
- **Foreclosure (past 7 years)**: 2% Yes
- **Lawsuit**: 4% Yes
- **Loan Foreclosure**: 2% Yes
- **Delinquent on Federal Debt**: 3% Yes
- **Alimony/Child Support**: 15% Yes
- **Down Payment Borrowed**: 5% Yes
- **Co-Maker on Another Loan**: 10% Yes
- **US Citizen**: 85% Yes
- **Permanent Resident**: 12% Yes
- **Primary Residence**: 85% Yes
- **Ownership Interest (past 3 years)**: 40% Yes

## Section 7: Co-Borrower Information
- **Percentage with Co-Borrower**: 45%
- **Fields**: Same as Borrower sections 1-6

## Calculated Fields

### Debt-to-Income Ratio (DTI)
- **Front-End DTI**: 15% - 35% (housing payment / gross income)
- **Back-End DTI**: 25% - 50% (total debt / gross income)
- **Target Range**: 28% - 43%

### Loan-to-Value (LTV)
- **LTV Ratio**: 70% - 97%
- **Conventional**: 80% - 97%
- **FHA**: 96.5%
- **VA**: 100%

### Credit Score (not on URLA but needed for approval)
- **Range**: 580 - 850
- **Distribution**: Normal with mean 720, std dev 60

---

I'll help you with this mortgage application data generation project! This is a coding task, so let me route this to the Coder specialist agent who can provide detailed guidance on URLA fields and Python code generation.


invoke_coder
Input
{"query": "I want to generate synthetic data to fill out sample URLAs for residential mortgage applications. What fields do I need and what range of values? I will want to capture this in a md file and then write python code to generate it."}
Result
Error: RuntimeError - Failed to invoke specialist agent 'coder': Response ended prematurely
Let me provide you with comprehensive guidance on generating synthetic URLA (Uniform Residential Loan Application) data directly.

URLA Fields and Synthetic Data Specification
Here's a markdown file structure for your URLA synthetic data:

---

Installation Requirements
Create a requirements.txt file:

faker==19.12.0 pandas==2.1.3 numpy==1.26.2
Install with:

bash

pip install -r requirements.txt
Usage
bash

python generate_urla_data.py
This will generate:

urla_synthetic_data.json - Full detailed data in JSON format
urla_synthetic_data.csv - Flattened data for easy analysis
The code generates realistic URLA data with:

Proper field distributions and correlations
Realistic DTI and LTV calculations
Proper loan type constraints (e.g., VA loans with 0% down)
Correlated data (e.g., higher income → higher loan amounts)
Edge cases (bankruptcies, foreclosures, etc.)
You can adjust the num_applications parameter to generate as many samples as you need!