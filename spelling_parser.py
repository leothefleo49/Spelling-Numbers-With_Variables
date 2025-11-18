"""
Spelling Parser
Parses number words and applies multiplication/addition rules.
"""

import re
from number_to_words import number_to_words


class SpellingParser:
    """
    Parses spelled numbers and calculates their value based on letter variables.
    
    Rules:
    - Configurable operators for spaces (multiply, add, divide, subtract)
    - Configurable operator for hyphens (default: minus)
    - Support for decimal precision control
    """
    
    # Magnitude values for each word component
    WORD_VALUES = {
        "ZERO": 0,
        "ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5,
        "SIX": 6, "SEVEN": 7, "EIGHT": 8, "NINE": 9,
        "TEN": 10, "ELEVEN": 11, "TWELVE": 12, "THIRTEEN": 13, "FOURTEEN": 14,
        "FIFTEEN": 15, "SIXTEEN": 16, "SEVENTEEN": 17, "EIGHTEEN": 18, "NINETEEN": 19,
        "TWENTY": 20, "THIRTY": 30, "FORTY": 40, "FIFTY": 50,
        "SIXTY": 60, "SEVENTY": 70, "EIGHTY": 80, "NINETY": 90,
        "HUNDRED": 100,
        "THOUSAND": 1000,
        "MILLION": 1000000,
        "BILLION": 1000000000,
        "NEGATIVE": -1  # Special handling
    }
    
    def __init__(self, letter_values=None, space_operator='auto', hyphen_operator='minus', 
                 decimal_places=4):
        """
        Initialize parser with letter values (A-Z).
        
        Args:
            letter_values (dict): Dictionary mapping letters to numerical values.
                                 If None, all letters are set to 1.0
            space_operator (str): Operation for spaces: 'auto', 'multiply', 'add', 'divide', 'subtract'
            hyphen_operator (str): Operation for hyphens: 'minus', 'multiply', 'add', 'divide'
            decimal_places (int): Number of decimal places for rounding (0-100)
        """
        if letter_values is None:
            # Default: all letters = 1.0
            self.letter_values = {chr(65 + i): 1.0 for i in range(26)}
        else:
            self.letter_values = letter_values
        
        self.space_operator = space_operator
        self.hyphen_operator = hyphen_operator
        self.decimal_places = decimal_places
    
    def set_letter_values(self, letter_values):
        """Update letter values"""
        self.letter_values = letter_values
    
    def set_operators(self, space_operator='auto', hyphen_operator='minus'):
        """Update operator settings"""
        self.space_operator = space_operator
        self.hyphen_operator = hyphen_operator
    
    def word_product(self, word):
        """
        Calculate the product of letter values in a word.
        
        Args:
            word (str): A single word (e.g., "TWENTY", "THREE")
            
        Returns:
            float: Product of all letter values in the word
        """
        # Remove hyphens and spaces, keep only letters
        letters = [c for c in word.upper() if c.isalpha()]
        product = 1.0
        for letter in letters:
            product *= self.letter_values.get(letter, 1.0)
        
        # Round to specified decimal places
        if self.decimal_places is not None:
            product = round(product, self.decimal_places)
        
        return product
    
    def apply_operator(self, left, right, operator):
        """
        Apply an operator between two values.
        
        Args:
            left (float): Left operand
            right (float): Right operand
            operator (str): Operation to apply
            
        Returns:
            float: Result of operation
        """
        if operator == 'multiply':
            result = left * right
        elif operator == 'add':
            result = left + right
        elif operator == 'subtract' or operator == 'minus':
            result = left - right
        elif operator == 'divide':
            result = left / right if right != 0 else 0
        else:
            result = left + right  # Default to add
        
        # Round to specified decimal places
        if self.decimal_places is not None:
            result = round(result, self.decimal_places)
        
        return result
    
    def parse_components(self, spelling):
        """
        Break a spelled number into its components with operators.
        
        Args:
            spelling (str): Full spelling (e.g., "TWENTY-THREE", "THREE HUNDRED")
            
        Returns:
            list: List of (word, magnitude, separator) tuples
        """
        # Handle NEGATIVE separately
        is_negative = spelling.startswith("NEGATIVE ")
        if is_negative:
            spelling = spelling[9:]  # Remove "NEGATIVE "
        
        # Parse into components with their separators
        components = []
        current_word = ""
        
        i = 0
        while i < len(spelling):
            char = spelling[i]
            
            if char == ' ':
                if current_word and current_word in self.WORD_VALUES:
                    magnitude = self.WORD_VALUES[current_word]
                    components.append((current_word, magnitude, 'space'))
                current_word = ""
            elif char == '-':
                if current_word and current_word in self.WORD_VALUES:
                    magnitude = self.WORD_VALUES[current_word]
                    components.append((current_word, magnitude, 'hyphen'))
                current_word = ""
            else:
                current_word += char
            
            i += 1
        
        # Add final word
        if current_word and current_word in self.WORD_VALUES:
            magnitude = self.WORD_VALUES[current_word]
            components.append((current_word, magnitude, None))
        
        result = []
        # Add NEGATIVE at the front if present
        if is_negative:
            result.append(("NEGATIVE", -1, 'multiply'))
        
        result.extend(components)
        return result
    
    def calculate_spelled_value(self, spelling):
        """
        Calculate the "spelled value" using configurable operators.
        
        Args:
            spelling (str): Full spelling (e.g., "TWENTY-THREE")
            
        Returns:
            tuple: (float, str) - The calculated value and explanation
        """
        components = self.parse_components(spelling)
        
        if not components:
            return 0.0, "Empty spelling"
        
        # Start with first component
        current_value = self.word_product(components[0][0])
        explanation_parts = [f"{components[0][0]}={current_value:.{self.decimal_places}f}"]
        
        # Process remaining components
        for i in range(1, len(components)):
            word, magnitude, separator = components[i-1]
            next_word, next_magnitude, _ = components[i]
            next_value = self.word_product(next_word)
            
            # Determine operator
            if separator == 'space':
                if self.space_operator == 'auto':
                    # Auto mode: use magnitude ordering
                    if next_magnitude > magnitude:
                        operator = 'multiply'
                    else:
                        operator = 'add'
                else:
                    operator = self.space_operator
            elif separator == 'hyphen':
                operator = self.hyphen_operator
            elif separator == 'multiply':
                operator = 'multiply'  # For NEGATIVE
            else:
                operator = 'add'  # Default
            
            # Apply operator
            current_value = self.apply_operator(current_value, next_value, operator)
            
            # Build explanation
            op_symbol = {'multiply': '×', 'add': '+', 'subtract': '-', 'minus': '-', 'divide': '÷'}
            symbol = op_symbol.get(operator, '+')
            explanation_parts.append(f"{symbol} {next_word}={next_value:.{self.decimal_places}f}")
        
        explanation = " ".join(explanation_parts) + f" = {current_value:.{self.decimal_places}f}"
        
        return current_value, explanation
    
    def get_error(self, number):
        """
        Calculate the error between the spelled value and the actual number.
        
        Args:
            number (int): The target number
            
        Returns:
            float: Squared error (spelled_value - number)^2
        """
        spelling = number_to_words(number)
        spelled_value, _ = self.calculate_spelled_value(spelling)
        error = (spelled_value - number) ** 2
        return error


if __name__ == "__main__":
    # Test with default letter values (all = 1.0)
    parser = SpellingParser()
    
    test_numbers = [1, 3, 20, 23, 100, 300, -1, -45]
    
    for num in test_numbers:
        spelling = number_to_words(num)
        value, explanation = parser.calculate_spelled_value(spelling)
        print(f"\n{num}: {spelling}")
        print(f"  Calculation: {explanation}")
        print(f"  Spelled Value: {value:.4f}")
        print(f"  Target: {num}, Error: {(value - num)**2:.4f}")
