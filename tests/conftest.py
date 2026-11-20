import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pytest  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


@pytest.fixture
def profile():
    return {
        "name": "Mara Beispiel",
        "headline": "Gründerin & Strategin für nachhaltige Lieferketten",
        "company": "Beispiel Logistik GmbH",
        "location": "Essen, Deutschland",
        "email": "mara@example.com",
        "phone": "+49 201 000000",
        "website": "example.com",
        "linkedin_url": "https://www.linkedin.com/in/mara-beispiel/",
    }


@pytest.fixture
def brand():
    return {
        "name": "Beispiel Logistik",
        "colors": {"primary": "#0F766E", "secondary": "#F59E0B", "background": "#FFFFFF", "text": "#111827"},
        "fonts": {"heading": "Sora", "body": "Inter"},
    }
