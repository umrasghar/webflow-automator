# data/data_generator.py
# WebFlow Automator - Data Generator
# This module provides functions for generating test data

import re
import random
import string
import datetime
import logging
from typing import Dict, Any, List, Optional, Union, Tuple

try:
    # Try to import Faker if available
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False

logger = logging.getLogger("WebFlowAutomator.Data.DataGenerator")

class DataGenerator:
    """
    Provides methods for generating various types of test data
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the data generator
        
        Args:
            seed: Random seed for reproducible data
        """
        # Set random seed if provided
        if seed is not None:
            random.seed(seed)
        
        # Initialize Faker if available
        if FAKER_AVAILABLE:
            self.faker = Faker()
            if seed is not None:
                Faker.seed(seed)
        else:
            self.faker = None
            logger.warning("Faker library not available. Using basic data generation.")
    
    def generate_name(self, name_type: str = "full") -> str:
        """
        Generate a random name
        
        Args:
            name_type: Type of name to generate (first, last, full)
        
        Returns:
            str: Generated name
        """
        if self.faker:
            if name_type == "first":
                return self.faker.first_name()
            elif name_type == "last":
                return self.faker.last_name()
            else:  # full
                return self.faker.name()
        else:
            # Fallback to basic name generation
            first_names = [
                "John", "Jane", "Michael", "Emily", "David", "Sarah", "Robert", "Emma",
                "William", "Olivia", "James", "Sophia", "Thomas", "Ava", "Christopher", "Mia"
            ]
            last_names = [
                "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson",
                "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin"
            ]
            
            if name_type == "first":
                return random.choice(first_names)
            elif name_type == "last":
                return random.choice(last_names)
            else:  # full
                return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def generate_email(self, name: Optional[str] = None) -> str:
        """
        Generate a random email address
        
        Args:
            name: Name to base email on (optional)
        
        Returns:
            str: Generated email address
        """
        if self.faker:
            if name:
                # Convert name to lowercase and replace spaces with dots
                name_part = name.lower().replace(" ", ".")
                # Remove special characters
                name_part = re.sub(r'[^a-z0-9.]', '', name_part)
                return f"{name_part}@{self.faker.domain_name()}"
            else:
                return self.faker.email()
        else:
            # Fallback to basic email generation
            domains = ["example.com", "test.com", "sample.org", "mail.net", "domain.io"]
            
            if name:
                # Convert name to lowercase and replace spaces with dots
                name_part = name.lower().replace(" ", ".")
                # Remove special characters
                name_part = re.sub(r'[^a-z0-9.]', '', name_part)
            else:
                # Generate random username
                name_part = ''.join(random.choice(string.ascii_lowercase) for _ in range(8))
            
            return f"{name_part}@{random.choice(domains)}"
    
    def generate_phone(self, format_str: str = "(###) ###-####") -> str:
        """
        Generate a random phone number
        
        Args:
            format_str: Format string for phone number (# will be replaced with a digit)
        
        Returns:
            str: Generated phone number
        """
        if self.faker:
            # Use faker's phone number format if no specific format provided
            if format_str == "(###) ###-####":
                return self.faker.phone_number()
            else:
                # Use custom format
                result = ""
                for char in format_str:
                    if char == "#":
                        result += str(random.randint(0, 9))
                    else:
                        result += char
                return result
        else:
            # Fallback to basic phone generation
            result = ""
            for char in format_str:
                if char == "#":
                    result += str(random.randint(0, 9))
                else:
                    result += char
            return result
    
    def generate_number(self, min_val: int = 1, max_val: int = 100) -> int:
        """
        Generate a random number
        
        Args:
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
        
        Returns:
            int: Generated number
        """
        return random.randint(min_val, max_val)
    
    def generate_date(self, min_date: Optional[str] = None, max_date: Optional[str] = None, 
                      format_str: str = "%Y-%m-%d") -> str:
        """
        Generate a random date
        
        Args:
            min_date: Minimum date (inclusive, format: YYYY-MM-DD)
            max_date: Maximum date (inclusive, format: YYYY-MM-DD)
            format_str: Format string for output date
        
        Returns:
            str: Generated date in specified format
        """
        # Set default date range if not provided
        if not min_date:
            min_date = "2000-01-01"
        if not max_date:
            max_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Convert date strings to datetime objects
        min_dt = datetime.datetime.strptime(min_date, "%Y-%m-%d")
        max_dt = datetime.datetime.strptime(max_date, "%Y-%m-%d")
        
        # Calculate days between min and max dates
        delta_days = (max_dt - min_dt).days
        
        if delta_days < 0:
            # Invalid date range, swap min and max
            min_dt, max_dt = max_dt, min_dt
            delta_days = abs(delta_days)
        
        # Generate random date
        random_days = random.randint(0, delta_days)
        result_date = min_dt + datetime.timedelta(days=random_days)
        
        # Format date
        return result_date.strftime(format_str)
    
    def generate_address(self) -> Dict[str, str]:
        """
        Generate a random address
        
        Returns:
            dict: Address components (street, city, state, postal_code, country)
        """
        if self.faker:
            address = {
                "street": self.faker.street_address(),
                "city": self.faker.city(),
                "state": self.faker.state(),
                "postal_code": self.faker.postcode(),
                "country": self.faker.country()
            }
            return address
        else:
            # Fallback to basic address generation
            streets = [
                "123 Main St", "456 Elm St", "789 Oak Ave", "321 Pine Rd", "654 Maple Dr",
                "987 Cedar Blvd", "741 Birch Ln", "852 Willow Way", "963 Spruce St", "159 Ash Ct"
            ]
            cities = [
                "Springfield", "Riverdale", "Franklin", "Clinton", "Georgetown",
                "Salem", "Kingston", "Oxford", "Burlington", "Manchester"
            ]
            states = [
                "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
                "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD"
            ]
            countries = ["United States", "Canada", "United Kingdom", "Australia"]
            
            address = {
                "street": random.choice(streets),
                "city": random.choice(cities),
                "state": random.choice(states),
                "postal_code": f"{random.randint(10000, 99999)}",
                "country": random.choice(countries)
            }
            return address
    
    def generate_credit_card(self) -> Dict[str, str]:
        """
        Generate random credit card details (for testing, not real cards)
        
        Returns:
            dict: Credit card details (number, expiry, cvv)
        """
        if self.faker:
            cc = {
                "number": self.faker.credit_card_number(card_type=None),
                "expiry": self.faker.credit_card_expire(start="now", end="+10y", date_format="%m/%y"),
                "cvv": self.faker.credit_card_security_code()
            }
            return cc
        else:
            # Fallback to basic credit card generation
            # Generate card number (not valid, just for testing)
            number = ''.join(random.choice(string.digits) for _ in range(16))
            
            # Generate expiry date (1-5 years in the future)
            now = datetime.datetime.now()
            years_ahead = random.randint(1, 5)
            month = random.randint(1, 12)
            expiry = f"{month:02d}/{(now.year + years_ahead) % 100:02d}"
            
            # Generate CVV
            cvv = ''.join(random.choice(string.digits) for _ in range(3))
            
            cc = {
                "number": number,
                "expiry": expiry,
                "cvv": cvv
            }
            return cc
    
    def generate_company(self) -> Dict[str, str]:
        """
        Generate random company details
        
        Returns:
            dict: Company details (name, industry, catch_phrase)
        """
        if self.faker:
            company = {
                "name": self.faker.company(),
                "industry": self.faker.industry(),
                "catch_phrase": self.faker.catch_phrase()
            }
            return company
        else:
            # Fallback to basic company generation
            names = [
                "Acme Corp", "TechSolutions", "Global Industries", "InnovateCo", "PrimeServices",
                "Apex Systems", "Elite Enterprises", "Summit Group", "Quantum Inc", "Dynamic Solutions"
            ]
            industries = [
                "Technology", "Finance", "Healthcare", "Manufacturing", "Retail",
                "Education", "Real Estate", "Energy", "Transportation", "Entertainment"
            ]
            phrases = [
                "Leading the way", "Innovation at its best", "Excellence in service",
                "Building the future", "Quality you can trust", "Solutions that work",
                "Committed to success", "Beyond expectations", "Creating value", "A new standard"
            ]
            
            company = {
                "name": random.choice(names),
                "industry": random.choice(industries),
                "catch_phrase": random.choice(phrases)
            }
            return company
    
    def generate_lorem_ipsum(self, words: int = 50) -> str:
        """
        Generate lorem ipsum text
        
        Args:
            words: Number of words to generate
        
        Returns:
            str: Generated lorem ipsum text
        """
        if self.faker:
            return self.faker.text(max_nb_chars=words * 6)[:words * 6]
        else:
            # Fallback to basic lorem ipsum generation
            lorem = """
            Lorem ipsum dolor sit amet consectetur adipisicing elit. Maxime mollitia,
            molestiae quas vel sint commodi repudiandae consequuntur voluptatum laborum
            numquam blanditiis harum quisquam eius sed odit fugiat iusto fuga praesentium
            optio, eaque rerum! Provident similique accusantium nemo autem. Veritatis
            obcaecati tenetur iure eius earum ut molestias architecto voluptate aliquam
            nihil, eveniet aliquid culpa officia aut! Impedit sit sunt quaerat, odit,
            tenetur error, harum nesciunt ipsum debitis quas aliquid. Reprehenderit,
            quia. Quo neque error repudiandae fuga? Ipsa laudantium molestias eos
            sapiente officiis modi at sunt excepturi expedita sint? Sed quibusdam
            recusandae alias error harum maxime adipisci amet laborum. Perspiciatis
            """
            
            # Clean up and split into words
            lorem = re.sub(r'\s+', ' ', lorem).strip()
            all_words = lorem.split()
            
            # Generate text with requested word count
            result_words = []
            for i in range(words):
                result_words.append(all_words[i % len(all_words)])
            
            return ' '.join(result_words)
    
    def generate_custom(self, pattern: str) -> str:
        """
        Generate custom formatted data based on a pattern
        
        Pattern can contain the following placeholders:
        - # : Random digit
        - A : Random uppercase letter
        - a : Random lowercase letter
        - X : Random uppercase letter or digit
        - x : Random lowercase letter or digit
        - ? : Random letter (upper or lower case)
        
        Args:
            pattern: Format pattern
        
        Returns:
            str: Generated formatted data
        """
        result = ""
        
        for char in pattern:
            if char == "#":
                # Random digit
                result += random.choice(string.digits)
            elif char == "A":
                # Random uppercase letter
                result += random.choice(string.ascii_uppercase)
            elif char == "a":
                # Random lowercase letter
                result += random.choice(string.ascii_lowercase)
            elif char == "X":
                # Random uppercase letter or digit
                result += random.choice(string.ascii_uppercase + string.digits)
            elif char == "x":
                # Random lowercase letter or digit
                result += random.choice(string.ascii_lowercase + string.digits)
            elif char == "?":
                # Random letter (upper or lower case)
                result += random.choice(string.ascii_letters)
            else:
                # Keep literal character
                result += char
        
        return result