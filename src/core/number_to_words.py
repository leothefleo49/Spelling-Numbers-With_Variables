"""Robust integer to words converter supporting large magnitudes."""

ONES = [
    "",
    "ONE",
    "TWO",
    "THREE",
    "FOUR",
    "FIVE",
    "SIX",
    "SEVEN",
    "EIGHT",
    "NINE",
]

TEENS = [
    "TEN",
    "ELEVEN",
    "TWELVE",
    "THIRTEEN",
    "FOURTEEN",
    "FIFTEEN",
    "SIXTEEN",
    "SEVENTEEN",
    "EIGHTEEN",
    "NINETEEN",
]

TENS = [
    "",
    "",
    "TWENTY",
    "THIRTY",
    "FORTY",
    "FIFTY",
    "SIXTY",
    "SEVENTY",
    "EIGHTY",
    "NINETY",
]

SCALES = [
    (10**12, "TRILLION"),
    (10**9, "BILLION"),
    (10**6, "MILLION"),
    (10**3, "THOUSAND"),
]


def _convert_below_thousand(num: int) -> str:
    """Convert a number < 1000 into words."""
    if num == 0:
        return ""
    if num < 10:
        return ONES[num]
    if num < 20:
        return TEENS[num - 10]
    if num < 100:
        ten = num // 10
        one = num % 10
        return TENS[ten] if one == 0 else f"{TENS[ten]}-{ONES[one]}"

    hundred = num // 100
    remainder = num % 100
    words = f"{ONES[hundred]} HUNDRED"
    if remainder:
        words += f" {_convert_below_thousand(remainder)}"
    return words


def number_to_words(n: int) -> str:
    """Convert any integer (|n| < 10^15) into its English words."""
    if n == 0:
        return "ZERO"
    if n < 0:
        return "NEGATIVE " + number_to_words(-n)

    words = []
    remaining = n
    for scale_value, scale_name in SCALES:
        if remaining >= scale_value:
            chunk = remaining // scale_value
            words.append(_convert_below_thousand(chunk))
            words.append(scale_name)
            remaining %= scale_value

    if remaining:
        words.append(_convert_below_thousand(remaining))

    # Filter any empty segments and join with single spaces
    return " ".join(filter(None, words))
