import pandas as pd
import pytest

from app import insights


@pytest.fixture
def sales_df():
    # مجموع دورهٔ اول ۱۸۰۰، دورهٔ دوم ۱۳۵۰ → افت ۲۵٪ (باید trend را فلگ کند)
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


def test_trend_insight_flags_significant_drop(sales_df):
    result = insights.generate_insights(sales_df)
    trend = [i for i in result if i["type"] == "trend"]
    assert trend, "باید یک بینش روند برای افت ۲۵٪ تولید شود"
    assert trend[0]["metric_col"] == "فروش"
    assert "افت" in trend[0]["narrative"]


def test_concentration_insight_flags_dominant_category():
    df = pd.DataFrame(
        {
            "کانال": ["اینستاگرام"] * 5 + ["حضوری", "دیجی‌کالا"],
            "درآمد": [200, 200, 200, 200, 200, 50, 50],
        }
    )
    result = insights.generate_insights(df)
    concentration = [i for i in result if i["type"] == "concentration"]
    assert concentration, "باید تمرکز بیش‌ازحد یک دسته فلگ شود"
    assert concentration[0]["group_col"] == "کانال"


def test_outlier_group_insight_flags_far_group_mean():
    categories = ["A", "B", "C", "D", "E", "F", "G", "H"]
    values = [100000.0] + [50.0 + i for i in range(7)]
    df = pd.DataFrame({"شعبه": categories, "امتیاز": values})
    result = insights.generate_insights(df)
    outlier = [i for i in result if i["type"] == "outlier_group"]
    assert outlier, "باید گروه دورافتاده فلگ شود"
    assert "A" in outlier[0]["narrative"]


def test_data_quality_insight_flags_high_missing_ratio():
    df = pd.DataFrame(
        {
            "یادداشت": [None, None, None, "ok", "ok"],
            "عدد": [1, 2, 3, 4, 5],
        }
    )
    result = insights.generate_insights(df)
    quality = [i for i in result if i["type"] == "data_quality"]
    assert quality, "باید ستون با ۶۰٪ مقدار خالی فلگ شود"
    assert quality[0]["metric_col"] == "یادداشت"


def test_generate_insights_caps_at_max_insights():
    result = insights.generate_insights(pd.DataFrame({
        "a": range(10),
        "b": range(10, 20),
        "c": range(20, 30),
        "d": range(30, 40),
        "e": range(40, 50),
    }))
    assert len(result) <= insights.MAX_INSIGHTS


def test_empty_dataframe_returns_no_insights():
    assert insights.generate_insights(pd.DataFrame()) == []
