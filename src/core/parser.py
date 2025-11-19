"""
Spelling Parser
Parses number words and applies multiplication/addition rules.
"""

from typing import List, Tuple, Dict, Any, Optional
from .number_to_words import number_to_words

class SpellingParser:
    """
    Parses spelled numbers and calculates their value based on letter variables.
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
        "TRILLION": 1000000000000,
        "NEGATIVE": -1
    }
    
    def __init__(self, letter_values: Optional[Dict[str, float]] = None, space_operator='auto', hyphen_operator='minus', decimal_places=4):
        self.letter_values = letter_values or {chr(65 + i): 1.0 for i in range(26)}
        self.space_operator = space_operator
        self.hyphen_operator = hyphen_operator
        self.decimal_places = decimal_places

    def parse_components(self, spelling: str) -> List[Tuple[str, int, str]]:
        """
        Break a spelled number into its components with operators.
        """
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
        
        if current_word and current_word in self.WORD_VALUES:
            magnitude = self.WORD_VALUES[current_word]
            components.append((current_word, magnitude, None))
        
        return components

    def compile_to_terms(self, spelling: str) -> List[Tuple[float, List[int]]]:
        """
        Compiles the spelling into a list of additive terms.
        Each term is (coefficient, [list of letter indices 0-25]).
        """
        components = self.parse_components(spelling)
        if not components:
            return []

        # Initial value: first word
        current_terms = self._word_to_terms(components[0][0])
        
        for i in range(1, len(components)):
            prev_word, prev_mag, sep = components[i-1]
            next_word, next_mag, _ = components[i]
            
            next_terms = self._word_to_terms(next_word)
            
            # Determine operator
            operator = 'add'
            if sep == 'space':
                if self.space_operator == 'auto':
                    if next_mag > prev_mag:
                        operator = 'multiply'
                    else:
                        operator = 'add'
                else:
                    operator = self.space_operator
            elif sep == 'hyphen':
                operator = self.hyphen_operator
            elif sep == 'multiply':
                operator = 'multiply'
            
            if operator == 'multiply':
                # Multiply every term in current by every term in next
                new_terms = []
                for c1, l1 in current_terms:
                    for c2, l2 in next_terms:
                        new_terms.append((c1 * c2, l1 + l2))
                current_terms = new_terms
            elif operator in ('add', 'plus'):
                current_terms.extend(next_terms)
            elif operator in ('subtract', 'minus'):
                # Negate next terms and add
                for j in range(len(next_terms)):
                    next_terms[j] = (-next_terms[j][0], next_terms[j][1])
                current_terms.extend(next_terms)
            elif operator == 'divide':
                # Division not supported in fast compiled mode
                pass

        return current_terms

    def _word_to_terms(self, word: str) -> List[Tuple[float, List[int]]]:
        """Converts a word to a single term [(1.0, [indices])]"""
        indices = []
        for char in word.upper():
            if 'A' <= char <= 'Z':
                indices.append(ord(char) - 65)
        
        return [(1.0, indices)]

    def calculate_value(self, spelling: str, letter_values: Dict[str, float]) -> float:
        """Calculates value using current letter values."""
        # This is for the UI/Explorer, not the optimizer loop
        self.letter_values = letter_values
        val, _ = self.calculate_spelled_value(spelling)
        return val

    def calculate_spelled_value(self, spelling: str) -> Tuple[float, str]:
        """
        Calculate the "spelled value" using configurable operators.
        Returns (value, explanation)
        """
        components = self.parse_components(spelling)
        if not components:
            return 0.0, "Empty"

        current_value = self._word_product(components[0][0])
        explanation_parts = [f"{components[0][0]}={current_value:.{self.decimal_places}f}"]

        for i in range(1, len(components)):
            word, magnitude, separator = components[i-1]
            next_word, next_magnitude, _ = components[i]
            next_value = self._word_product(next_word)

            if separator == 'space':
                if self.space_operator == 'auto':
                    operator = 'multiply' if next_magnitude > magnitude else 'add'
                else:
                    operator = self.space_operator
            elif separator == 'hyphen':
                operator = self.hyphen_operator
            elif separator == 'multiply':
                operator = 'multiply'
            else:
                operator = 'add'

            if operator == 'multiply':
                current_value *= next_value
                sym = '×'
            elif operator == 'add':
                current_value += next_value
                sym = '+'
            elif operator in ('subtract', 'minus'):
                current_value -= next_value
                sym = '-'
            elif operator == 'divide':
                current_value = current_value / next_value if next_value != 0 else 0
                sym = '÷'
            else:
                current_value += next_value
                sym = '+'
            
            explanation_parts.append(f"{sym} {next_word}={next_value:.{self.decimal_places}f}")

        return current_value, " ".join(explanation_parts) + f" = {current_value:.{self.decimal_places}f}"

    def _word_product(self, word: str) -> float:
        letters = [c for c in word.upper() if c.isalpha()]
        product = 1.0
        for letter in letters:
            product *= self.letter_values.get(letter, 1.0)
        return product
