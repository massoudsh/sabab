import pandas as pd
import pytest

from app import analytics


@pytest.fixture
def sales_df():
    return pd.DataFrame(
        {
            "تاریخ": [
                "1403-01-05", "1403-01-10", "1403-01-15",
                "1403-02-05", "1403-02-10", "1403-02-15",
            ],
            "محصول": ["الف", "ب", "ج", "الف", "ب", "ج"],
            "فروش": [1000, 500, 300, 700, 550, 100],
        }
    )


def test_detect_date_columns(sales_df):
    assert "تاریخ" in analytics.detect_date_columns(sales_df)


def test_numeric_columns(sales_df):
    assert analytics.numeric_columns(sales_df) == ["فروش"]


def test_aggregate_sum(sales_df):
    assert analytics.aggregate_column(sales_df, "فروش", "sum") == 3150.0


def test_aggregate_mean(sales_df):
    assert round(analytics.aggregate_column(sales_df, "فروش", "mean"), 2) == 525.0


def test_groupby_aggregate(sales_df):
    result = analytics.groupby_aggregate(sales_df, "فروش", "محصول", "sum")
    assert result.iloc[0]["محصول"] == "الف"
    assert result.iloc[0]["فروش"] == 1700


def test_explain_change(sales_df):
    result = analytics.explain_change(sales_df, "فروش", "محصول", "تاریخ")
    assert result["ok"] is True
    assert result["total_prev"] == 1800
    assert result["total_curr"] == 1350
    assert result["total_delta"] == -450
    assert "افت" in result["narrative"]


def test_trend_by_period(sales_df):
    result = analytics.trend_by_period(sales_df, "فروش", "تاریخ")
    assert len(result["labels"]) == 2
    assert result["series"][0]["data"] == [1800.0, 1350.0]
