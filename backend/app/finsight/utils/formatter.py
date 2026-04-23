def format_large_number(n: float) -> str:
    if n is None:
        return "N/A"
    
    abs_n = abs(n)
    sign = "-" if n < 0 else ""
    
    if abs_n >= 1_000_000_000_000:
        return f"{sign}{abs_n / 1_000_000_000_000:.2f}T"
    elif abs_n >= 1_000_000_000:
        return f"{sign}{abs_n / 1_000_000_000:.2f}B"
    elif abs_n >= 1_000_000:
        return f"{sign}{abs_n / 1_000_000:.2f}M"
    elif abs_n >= 1_000:
        return f"{sign}{abs_n / 1_000:.2f}K"
    else:
        return f"{sign}{abs_n:.2f}"

def format_price(n: float) -> str:
    if n is None:
        return "N/A"
    return f"${n:,.2f}"

def add_arrows(value: float) -> str:
    if value is None:
        return "N/A"
    if value > 0:
        return f"▲{value:.2f}%"
    elif value < 0:
        return f"▼{abs(value):.2f}%"
    return f"{value:.2f}%"
