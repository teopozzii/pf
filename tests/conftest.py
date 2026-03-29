import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_categories():
    return {
        "Medici": ["dentistico", "medical"],
        "Utenze": ["enel energia", "vodafone"],
        "Cibo": ["carrefour", "esselunga"],
    }


@pytest.fixture
def sample_headers():
    return {
        "loc_identif": "Data contabile",
        "category": "Categoria",
        "date": "Data valuta",
        "descript": "Descrizione",
        "detail": "Dettaglio",
        "value": "Importo",
    }


@pytest.fixture
def raw_statement_data():
    return pd.DataFrame([
        ["", "", "", "Data contabile", "Data valuta", "Descrizione", "Dettaglio", "Importo"],
        ["", "", "", "01/01/2024", "02/01/2024", "Pagamento CARREFOUR", "Acquisti", "-50.00"],
        ["", "", "", "05/01/2024", "05/01/2024", "ENEL ENERGIA", "Bollette", "-120.00"],
        ["", "", "", "10/01/2024", "10/01/2024", "Visita dentistico", "Medico", "-80.00"],
        ["", "", "", "15/01/2024", "15/01/2024", "RISTORANTE ROMA", "Cena", "-45.00"],
    ])


@pytest.fixture
def processed_statement_data():
    return pd.DataFrame({
        "Data contabile": pd.to_datetime(["2024-01-01", "2024-01-05", "2024-01-10", "2024-01-15"]),
        "Data valuta": pd.to_datetime(["2024-01-02", "2024-01-05", "2024-01-10", "2024-01-15"]),
        "Descrizione": [
            "Pagamento CARREFOUR",
            "ENEL ENERGIA",
            "Visita dentistico",
            "RISTORANTE ROMA",
        ],
        "Dettaglio": ["Acquisti", "Bollette", "Medico", "Cena"],
        "Importo": [-50.00, -120.00, -80.00, -45.00],
    })


@pytest.fixture
def categorized_statement_data(processed_statement_data):
    df = processed_statement_data.copy()
    df["Categoria"] = ["Cibo", "Utenze", "Medici", "Uncategorized"]
    return df
