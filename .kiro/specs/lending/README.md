# Mortgage Application Automation

## Business Challenge & Opportunity
Mortgage applications can require 75+ document types bundled into an application package totalling 600+ pages. To experiment and showcase AI capabilities, AWS and customers need the ability to generte dozens or hundreds of synthetic mortgage application packages with realistic data. This includes a mix of semi-structured data about the customer, along with PDF files.

## Alternative Approaches:
1. **Real Data**: Not an option, as it contains PII.
2. **Redacted Data**: The ability to redact or tokenize PII from real lending data is useful to our customers, especially if the process retains some of the shape of the real data but without the PII.
3. **Synthetic Data**: Generating synthetic but realistic data from scratch holds the most promise - especially if it includes structured, semi-structured, and PDF data. Bonus points for being able to influence the distribution (e.g. % of applications with higher or lower credit worthiness or borrowing needs) and if the data is internally consistent (e.g. a strong borrower would have a strong credit score as well as more granular data elements that are consistent with that strong credit score.)

## Solution
As a quick attempt, we prompted a general agent with: