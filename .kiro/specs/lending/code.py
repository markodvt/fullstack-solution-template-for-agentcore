import random
import string
from datetime import datetime, timedelta
from faker import Faker
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import json

fake = Faker('en_US')
random.seed(42)
np.random.seed(42)

@dataclass
class Address:
    street: str
    unit: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"

@dataclass
class Employment:
    employer_name: str
    phone: str
    address: Address
    position: str
    start_date: str
    employment_type: str
    years: int
    months: int
    base_income: float
    overtime: float
    bonus: float
    commission: float

@dataclass
class Asset:
    asset_type: str
    institution: str
    account_number: str
    balance: float

@dataclass
class Liability:
    creditor: str
    account_last_four: str
    monthly_payment: float
    balance: float
    to_be_paid_off: bool

@dataclass
class Property:
    address: Address
    property_type: str
    property_value: float
    occupancy: str
    units: int

@dataclass
class Borrower:
    first_name: str
    middle_name: str
    last_name: str
    suffix: str
    ssn: str
    date_of_birth: str
    citizenship: str
    marital_status: str
    home_phone: str
    cell_phone: str
    work_phone: str
    email: str
    current_address: Address
    housing_status: str
    years_at_address: int
    months_at_address: int
    mailing_address: Address
    former_address: Address
    current_employment: Employment
    previous_employment: Employment
    assets: list
    liabilities: list
    declarations: dict

@dataclass
class URLA:
    borrower: Borrower
    co_borrower: Borrower
    loan_amount: float
    loan_purpose: str
    loan_type: str
    loan_term: int
    interest_rate: float
    property_info: Property
    down_payment: float
    down_payment_source: str
    ltv: float
    dti: float
    credit_score: int

class URLAGenerator:
    def __init__(self):
        self.fake = Faker('en_US')
        
    def generate_ssn(self):
        """Generate a fake SSN"""
        return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
    
    def generate_phone(self):
        """Generate a phone number"""
        return f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"
    
    def generate_address(self):
        """Generate a random address"""
        unit = f"Apt {random.randint(1, 999)}" if random.random() < 0.2 else ""
        return Address(
            street=self.fake.street_address(),
            unit=unit,
            city=self.fake.city(),
            state=self.fake.state_abbr(),
            zip_code=self.fake.zipcode(),
            country="USA"
        )
    
    def generate_employment(self):
        """Generate employment information"""
        employment_type = random.choices(
            ['W2', 'Self-Employed', 'Retired', 'Other'],
            weights=[70, 15, 10, 5]
        )[0]
        
        years = random.randint(0, 30)
        months = random.randint(0, 11)
        
        base_income = round(random.uniform(2000, 40000), 2)
        overtime = round(random.uniform(0, 2000), 2) if random.random() < 0.3 else 0
        bonus = round(random.uniform(0, 10000), 2) if random.random() < 0.4 else 0
        commission = round(random.uniform(0, 5000), 2) if random.random() < 0.2 else 0
        
        start_date = (datetime.now() - timedelta(days=365*years + 30*months)).strftime("%Y-%m-%d")
        
        return Employment(
            employer_name=self.fake.company(),
            phone=self.generate_phone(),
            address=self.generate_address(),
            position=self.fake.job(),
            start_date=start_date,
            employment_type=employment_type,
            years=years,
            months=months,
            base_income=base_income,
            overtime=overtime,
            bonus=bonus,
            commission=commission
        )
    
    def generate_assets(self, num_assets=None):
        """Generate asset accounts"""
        if num_assets is None:
            num_assets = random.randint(1, 5)
        
        assets = []
        
        # Bank accounts
        for _ in range(random.randint(1, 3)):
            account_type = random.choices(
                ['Checking', 'Savings', 'Money Market', 'CD'],
                weights=[50, 30, 15, 5]
            )[0]
            
            balance = round(np.random.lognormal(9, 1.5), 2)
            balance = min(max(balance, 500), 500000)
            
            assets.append(Asset(
                asset_type=account_type,
                institution=self.fake.company() + " Bank",
                account_number=''.join([str(random.randint(0, 9)) for _ in range(10)]),
                balance=balance
            ))
        
        # Retirement accounts (40% of borrowers)
        if random.random() < 0.4:
            account_type = random.choices(
                ['401k', 'IRA', 'Pension'],
                weights=[60, 30, 10]
            )[0]
            
            balance = round(random.uniform(5000, 2000000), 2)
            
            assets.append(Asset(
                asset_type=account_type,
                institution=self.fake.company() + " Financial",
                account_number=''.join([str(random.randint(0, 9)) for _ in range(10)]),
                balance=balance
            ))
        
        # Stocks/Bonds (20% of borrowers)
        if random.random() < 0.2:
            assets.append(Asset(
                asset_type='Stocks/Bonds',
                institution=self.fake.company() + " Investments",
                account_number=''.join([str(random.randint(0, 9)) for _ in range(10)]),
                balance=round(random.uniform(1000, 500000), 2)
            ))
        
        return assets
    
    def generate_liabilities(self):
        """Generate liabilities"""
        liabilities = []
        
        # Credit cards (avg 2.5 per borrower)
        num_cards = max(0, int(np.random.normal(2.5, 1.5)))
        for _ in range(num_cards):
            liabilities.append(Liability(
                creditor=random.choice(['Visa', 'Mastercard', 'Amex', 'Discover']),
                account_last_four=''.join([str(random.randint(0, 9)) for _ in range(4)]),
                monthly_payment=round(random.uniform(25, 500), 2),
                balance=round(random.uniform(0, 25000), 2),
                to_be_paid_off=random.random() < 0.2
            ))
        
        # Auto loan (60% of borrowers)
        if random.random() < 0.6:
            balance = round(random.uniform(5000, 60000), 2)
            months_remaining = random.randint(6, 72)
            monthly_payment = round(balance / months_remaining, 2)
            
            liabilities.append(Liability(
                creditor=random.choice(['Toyota Finance', 'Ford Credit', 'Chase Auto', 'Capital One Auto']),
                account_last_four=''.join([str(random.randint(0, 9)) for _ in range(4)]),
                monthly_payment=monthly_payment,
                balance=balance,
                to_be_paid_off=False
            ))
        
        # Student loans (35% of borrowers)
        if random.random() < 0.35:
            liabilities.append(Liability(
                creditor=random.choice(['Navient', 'Great Lakes', 'FedLoan', 'Nelnet']),
                account_last_four=''.join([str(random.randint(0, 9)) for _ in range(4)]),
                monthly_payment=round(random.uniform(100, 1000), 2),
                balance=round(random.uniform(5000, 150000), 2),
                to_be_paid_off=False
            ))
        
        return liabilities
    
    def generate_declarations(self):
        """Generate declaration responses"""
        return {
            'outstanding_judgments': random.random() < 0.05,
            'bankruptcy_past_7_years': random.random() < 0.03,
            'foreclosure_past_7_years': random.random() < 0.02,
            'lawsuit': random.random() < 0.04,
            'loan_foreclosure': random.random() < 0.02,
            'delinquent_federal_debt': random.random() < 0.03,
            'alimony_child_support': random.random() < 0.15,
            'down_payment_borrowed': random.random() < 0.05,
            'co_maker_on_loan': random.random() < 0.10,
            'us_citizen': random.random() < 0.85,
            'permanent_resident': random.random() < 0.12,
            'primary_residence': random.random() < 0.85,
            'ownership_interest_past_3_years': random.random() < 0.40
        }
    
    def generate_borrower(self):
        """Generate a complete borrower profile"""
        first_name = self.fake.first_name()
        last_name = self.fake.last_name()
        middle_name = self.fake.first_name() if random.random() < 0.7 else ""
        suffix = random.choice(['Jr.', 'Sr.', 'II', 'III', 'IV']) if random.random() < 0.05 else ""
        
        dob = self.fake.date_of_birth(minimum_age=18, maximum_age=80)
        
        citizenship = random.choices(
            ['US Citizen', 'Permanent Resident', 'Non-Permanent Resident'],
            weights=[80, 15, 5]
        )[0]
        
        marital_status = random.choices(
            ['Married', 'Unmarried', 'Separated'],
            weights=[50, 45, 5]
        )[0]
        
        current_address = self.generate_address()
        years_at_address = random.randint(0, 30)
        months_at_address = random.randint(0, 11)
        
        # Mailing address (10% different)
        mailing_address = self.generate_address() if random.random() < 0.1 else current_address
        
        # Former address (if < 2 years at current)
        former_address = self.generate_address() if years_at_address < 2 else None
        
        current_employment = self.generate_employment()
        previous_employment = self.generate_employment() if current_employment.years < 2 else None
        
        housing_status = random.choices(
            ['Own', 'Rent', 'Living Rent Free'],
            weights=[35, 60, 5]
        )[0]
        
        return Borrower(
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            suffix=suffix,
            ssn=self.generate_ssn(),
            date_of_birth=dob.strftime("%Y-%m-%d"),
            citizenship=citizenship,
            marital_status=marital_status,
            home_phone=self.generate_phone() if random.random() < 0.6 else "",
            cell_phone=self.generate_phone() if random.random() < 0.95 else "",
            work_phone=self.generate_phone() if random.random() < 0.4 else "",
            email=f"{first_name.lower()}.{last_name.lower()}@{self.fake.free_email_domain()}",
            current_address=current_address,
            housing_status=housing_status,
            years_at_address=years_at_address,
            months_at_address=months_at_address,
            mailing_address=mailing_address,
            former_address=former_address,
            current_employment=current_employment,
            previous_employment=previous_employment,
            assets=self.generate_assets(),
            liabilities=self.generate_liabilities(),
            declarations=self.generate_declarations()
        )
    
    def calculate_monthly_income(self, borrower):
        """Calculate total monthly income"""
        emp = borrower.current_employment
        return emp.base_income + emp.overtime + emp.bonus + emp.commission
    
    def calculate_monthly_debt(self, borrower):
        """Calculate total monthly debt payments"""
        return sum([liability.monthly_payment for liability in borrower.liabilities])
    
    def generate_property(self, loan_purpose):
        """Generate property information"""
        property_type = random.choices(
            ['Single Family', 'Condo', 'Townhouse', 'Multi-Family'],
            weights=[70, 15, 10, 5]
        )[0]
        
        property_value = round(random.uniform(75000, 2000000), 2)
        
        occupancy = random.choices(
            ['Primary Residence', 'Secondary', 'Investment'],
            weights=[85, 10, 5]
        )[0]
        
        units = 1 if property_type != 'Multi-Family' else random.randint(2, 4)
        
        return Property(
            address=self.generate_address(),
            property_type=property_type,
            property_value=property_value,
            occupancy=occupancy,
            units=units
        )
    
    def generate_urla(self):
        """Generate a complete URLA application"""
        borrower = self.generate_borrower()
        
        # Co-borrower (45% of applications)
        co_borrower = self.generate_borrower() if random.random() < 0.45 else None
        
        # Loan information
        loan_purpose = random.choices(
            ['Purchase', 'Refinance', 'Cash-Out Refinance'],
            weights=[60, 30, 10]
        )[0]
        
        loan_type = random.choices(
            ['Conventional', 'FHA', 'VA', 'USDA'],
            weights=[70, 20, 8, 2]
        )[0]
        
        loan_term = random.choices([15, 20, 30], weights=[15, 10, 75])[0]
        
        interest_rate = round(random.uniform(2.5, 8.0), 3)
        
        # Property
        property_info = self.generate_property(loan_purpose)
        
        # Down payment
        if loan_type == 'Conventional':
            down_payment_pct = random.uniform(0.03, 0.30)
        elif loan_type == 'FHA':
            down_payment_pct = 0.035
        elif loan_type == 'VA':
            down_payment_pct = 0.0
        else:  # USDA
            down_payment_pct = 0.0
        
        down_payment = round(property_info.property_value * down_payment_pct, 2)
        loan_amount = round(property_info.property_value - down_payment, 2)
        
        down_payment_source = random.choices(
            ['Savings', 'Gift', 'Sale of Property', 'Other'],
            weights=[70, 15, 10, 5]
        )[0]
        
        # Calculate LTV
        ltv = round((loan_amount / property_info.property_value) * 100, 2)
        
        # Calculate DTI
        monthly_income = self.calculate_monthly_income(borrower)
        if co_borrower:
            monthly_income += self.calculate_monthly_income(co_borrower)
        
        monthly_debt = self.calculate_monthly_debt(borrower)
        if co_borrower:
            monthly_debt += self.calculate_monthly_debt(co_borrower)
        
        # Add estimated housing payment
        monthly_payment = loan_amount * (interest_rate/100/12) * (1 + interest_rate/100/12)**(loan_term*12) / ((1 + interest_rate/100/12)**(loan_term*12) - 1)
        property_tax = property_info.property_value * 0.012 / 12  # 1.2% annual
        insurance = property_info.property_value * 0.005 / 12  # 0.5% annual
        total_housing_payment = monthly_payment + property_tax + insurance
        
        total_debt = monthly_debt + total_housing_payment
        dti = round((total_debt / monthly_income) * 100, 2) if monthly_income > 0 else 0
        
        # Credit score
        credit_score = int(np.random.normal(720, 60))
        credit_score = min(max(credit_score, 580), 850)
        
        return URLA(
            borrower=borrower,
            co_borrower=co_borrower,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            loan_type=loan_type,
            loan_term=loan_term,
            interest_rate=interest_rate,
            property_info=property_info,
            down_payment=down_payment,
            down_payment_source=down_payment_source,
            ltv=ltv,
            dti=dti,
            credit_score=credit_score
        )

def dataclass_to_dict(obj):
    """Convert dataclass to dictionary recursively"""
    if obj is None:
        return None
    if isinstance(obj, list):
        return [dataclass_to_dict(item) for item in obj]
    if hasattr(obj, '__dataclass_fields__'):
        return {key: dataclass_to_dict(value) for key, value in asdict(obj).items()}
    return obj

def generate_dataset(num_applications=100, output_format='json'):
    """Generate a dataset of URLA applications"""
    generator = URLAGenerator()
    applications = []
    
    print(f"Generating {num_applications} URLA applications...")
    
    for i in range(num_applications):
        if (i + 1) % 10 == 0:
            print(f"Generated {i + 1}/{num_applications} applications")
        
        urla = generator.generate_urla()
        applications.append(dataclass_to_dict(urla))
    
    if output_format == 'json':
        with open('urla_synthetic_data.json', 'w') as f:
            json.dump(applications, f, indent=2)
        print(f"\nSaved {num_applications} applications to urla_synthetic_data.json")
    
    elif output_format == 'csv':
        # Flatten the data for CSV
        flattened = []
        for app in applications:
            flat_record = {
                'borrower_first_name': app['borrower']['first_name'],
                'borrower_last_name': app['borrower']['last_name'],
                'borrower_ssn': app['borrower']['ssn'],
                'borrower_dob': app['borrower']['date_of_birth'],
                'borrower_email': app['borrower']['email'],
                'borrower_city': app['borrower']['current_address']['city'],
                'borrower_state': app['borrower']['current_address']['state'],
                'borrower_income': app['borrower']['current_employment']['base_income'],
                'loan_amount': app['loan_amount'],
                'loan_purpose': app['loan_purpose'],
                'loan_type': app['loan_type'],
                'loan_term': app['loan_term'],
                'interest_rate': app['interest_rate'],
                'property_value': app['property_info']['property_value'],
                'property_type': app['property_info']['property_type'],
                'down_payment': app['down_payment'],
                'ltv': app['ltv'],
                'dti': app['dti'],
                'credit_score': app['credit_score'],
                'has_co_borrower': app['co_borrower'] is not None
            }
            flattened.append(flat_record)
        
        df = pd.DataFrame(flattened)
        df.to_csv('urla_synthetic_data.csv', index=False)
        print(f"\nSaved {num_applications} applications to urla_synthetic_data.csv")
    
    return applications

if __name__ == "__main__":
    # Generate 100 sample URLA applications
    applications = generate_dataset(num_applications=100, output_format='json')
    
    # Also generate CSV version
    generate_dataset(num_applications=100, output_format='csv')
    
    # Print sample application
    print("\n" + "="*80)
    print("SAMPLE APPLICATION:")
    print("="*80)
    print(json.dumps(applications[0], indent=2))