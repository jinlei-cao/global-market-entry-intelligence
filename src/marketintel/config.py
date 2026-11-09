"""Research design: a disclosed illustrative market basket and indicator specification."""

from dataclasses import dataclass

@dataclass(frozen=True)
class Indicator:
    code: str
    label: str
    source: int
    direction: str
    weight: float
    max_age: int
    group: str
    transform: str = "none"


# IMPORTANT: These are optional comparison candidates, NOT a certified list of BRI members.
# World Bank ISO3/ISO2 country codes can be queried in the World Bank Indicators API.
COUNTRIES = {
    "IDN": "Indonesia", "VNM": "Viet Nam", "THA": "Thailand",
    "MYS": "Malaysia", "PHL": "Philippines", "KHM": "Cambodia",
    "BGD": "Bangladesh", "PAK": "Pakistan", "KAZ": "Kazakhstan",
    "UZB": "Uzbekistan", "GEO": "Georgia", "TUR": "Türkiye",
    "EGY": "Egypt", "MAR": "Morocco", "KEN": "Kenya",
    "ETH": "Ethiopia", "ZAF": "South Africa", "JOR": "Jordan",
}

INDICATORS = (
    Indicator("NY.GDP.MKTP.CD", "Market size: GDP (current US$)", 2, "higher", 0.23, 4, "Market", "log10"),
    Indicator("NY.GDP.MKTP.KD.ZG", "Real GDP growth (%)", 2, "higher", 0.12, 4, "Market"),
    Indicator("RQ.EST", "Regulatory quality (WGI estimate)", 3, "higher", 0.23, 4, "Governance"),
    Indicator("LP.LPI.OVRL.XQ", "Logistics Performance Index (survey)", 2, "higher", 0.25, 5, "Operations"),
    Indicator("IT.NET.USER.ZS", "Internet users (% of population)", 2, "higher", 0.17, 4, "Digital"),
)

DEFAULT_AS_OF = 2025
WEIGHTS = {i.code: i.weight for i in INDICATORS}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-10
