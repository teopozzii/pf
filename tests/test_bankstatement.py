import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from utils.bankstatement import BankStatement


class TestCategorizeExpenses:
    def test_categorize_expenses_keyword_matching(self, sample_categories, sample_headers):
        bs = BankStatement(owner="papà", categories=sample_categories)
        bs.headers = sample_headers
        
        df = pd.DataFrame({
            "Descrizione": [
                "Pagamento CARREFOUR",
                "BOLLETTA ENEL ENERGIA",
                "VISITA dentistico",
            ],
            "Importo": [-50.0, -120.0, -80.0]
        })
        bs.data = df
        
        result = bs.categorize_expenses()
        
        assert result["Categoria"].iloc[0] == "Cibo"
        assert result["Categoria"].iloc[1] == "Utenze"
        assert result["Categoria"].iloc[2] == "Medici"

    def test_categorize_expenses_returns_uncategorized(self, sample_categories, sample_headers):
        bs = BankStatement(owner="papà", categories=sample_categories)
        bs.headers = sample_headers
        
        df = pd.DataFrame({
            "Descrizione": ["Sconosciuto XYZ123", "Altro senza categoria"],
            "Importo": [-50.0, -30.0]
        })
        bs.data = df
        
        result = bs.categorize_expenses()
        
        assert all(result["Categoria"] == "Uncategorized")

    def test_categorize_expenses_case_insensitive(self, sample_categories, sample_headers):
        bs = BankStatement(owner="papà", categories=sample_categories)
        bs.headers = sample_headers
        
        df = pd.DataFrame({
            "Descrizione": ["CARREFOUR", "carrefour", "CaRrEfOuR"],
            "Importo": [-50.0, -30.0, -20.0]
        })
        bs.data = df
        
        result = bs.categorize_expenses()
        
        assert all(result["Categoria"] == "Cibo")


class TestProcessStatement:
    def test_process_statement_header_detection(self, sample_headers):
        bs = BankStatement(owner="papà")
        bs.headers = sample_headers
        
        raw_df = pd.DataFrame([
            ["", "", "", "Data contabile", "Data valuta", "Descrizione", "Importo"],
            ["", "", "", "01/01/2024", "02/01/2024", "Pagamento", "-50.00"],
        ])
        
        result = bs.process_statement(raw_df)
        
        assert result is not None
        assert "Descrizione" in result.columns

    def test_process_statement_raises_on_unidentifiable(self, sample_headers):
        bs = BankStatement(owner="papà")
        bs.headers = sample_headers
        
        raw_df = pd.DataFrame([
            ["Col1", "Col2", "Col3"],
            ["Val1", "Val2", "Val3"],
        ])
        
        with pytest.raises(ValueError, match="Unidentifiable"):
            bs.process_statement(raw_df)

    def test_process_statement_date_parsing(self, sample_headers):
        bs = BankStatement(owner="papà")
        bs.headers = sample_headers
        
        raw_df = pd.DataFrame([
            ["", "", "", "Data contabile", "Data valuta", "Descrizione", "Importo"],
            ["", "", "", "01/01/2024", "02/01/2024", "Pagamento", "-50.00"],
        ])
        
        result = bs.process_statement(raw_df)
        
        assert pd.api.types.is_datetime64_any_dtype(result["Data valuta"])

    def test_process_statement_numeric_conversion(self, sample_headers):
        bs = BankStatement(owner="papà")
        bs.headers = sample_headers
        
        raw_df = pd.DataFrame([
            ["", "", "", "Data contabile", "Data valuta", "Descrizione", "Importo"],
            ["", "", "", "01/01/2024", "02/01/2024", "Pagamento", "-50,00"],
            ["", "", "", "01/01/2024", "02/01/2024", "Altro", "100,50"],
        ])
        
        result = bs.process_statement(raw_df)
        
        assert pd.api.types.is_numeric_dtype(result["Importo"])
        assert result["Importo"].iloc[0] == -50.00
        assert result["Importo"].iloc[1] == 100.50
