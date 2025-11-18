"""
Number to Words Converter
Converts integers to their English word representation.
"""

def number_to_words(n):
    """
    Convert an integer to its English word representation.
    
    Examples:
        1 -> "ONE"
        23 -> "TWENTY-THREE"
        -45 -> "NEGATIVE FORTY-FIVE"
        300 -> "THREE HUNDRED"
        1234 -> "ONE THOUSAND TWO HUNDRED THIRTY-FOUR"
    
    Args:
        n (int): The number to convert
        
    Returns:
        str: The English word representation
    """
    if n == 0:
        return "ZERO"
    
    # Handle negative numbers
    if n < 0:
        return "NEGATIVE " + number_to_words(-n)
    
    # Basic numbers
    ones = ["", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE"]
    teens = ["TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", 
             "SIXTEEN", "SEVENTEEN", "EIGHTEEN", "NINETEEN"]
    tens = ["", "", "TWENTY", "THIRTY", "FORTY", "FIFTY", "SIXTY", "SEVENTY", "EIGHTY", "NINETY"]
    
    def convert_below_thousand(num):
        """Convert numbers 0-999 to words"""
        if num == 0:
            return ""
        elif num < 10:
            return ones[num]
        elif num < 20:
            return teens[num - 10]
        elif num < 100:
            ten = num // 10
            one = num % 10
            if one == 0:
                return tens[ten]
            else:
                return tens[ten] + "-" + ones[one]
        else:  # 100-999
            hundred = num // 100
            remainder = num % 100
            result = ones[hundred] + " HUNDRED"
            if remainder > 0:
                result += " " + convert_below_thousand(remainder)
            return result
    
    # Handle large numbers
    if n < 1000:
        return convert_below_thousand(n)
    
    # Thousands
    if n < 1000000:
        thousands = n // 1000
        remainder = n % 1000
        result = convert_below_thousand(thousands) + " THOUSAND"
        if remainder > 0:
            result += " " + convert_below_thousand(remainder)
        return result
    
    # Millions
    if n < 1000000000:
        millions = n // 1000000
        remainder = n % 1000000
        result = convert_below_thousand(millions) + " MILLION"
        if remainder >= 1000:
            thousands = remainder // 1000
            result += " " + convert_below_thousand(thousands) + " THOUSAND"
            remainder = remainder % 1000
        if remainder > 0:
            result += " " + convert_below_thousand(remainder)
        return result
    
    # Billions
    billions = n // 1000000000
    remainder = n % 1000000000
    result = convert_below_thousand(billions) + " BILLION"
    if remainder >= 1000000:
        millions = remainder // 1000000
        result += " " + convert_below_thousand(millions) + " MILLION"
        remainder = remainder % 1000000
    if remainder >= 1000:
        thousands = remainder // 1000
        result += " " + convert_below_thousand(thousands) + " THOUSAND"
        remainder = remainder % 1000
    if remainder > 0:
        result += " " + convert_below_thousand(remainder)
    return result


if __name__ == "__main__":
    # Test cases
    test_numbers = [0, 1, 5, 10, 15, 20, 23, 100, 300, 1234, -45, -100]
    for num in test_numbers:
        print(f"{num:6d} -> {number_to_words(num)}")
