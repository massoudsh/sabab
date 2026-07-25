import pandas as pd
import pytest

from app import nlu


@pytest.fixture
def sales_df():
    return pd.DataFrame(
        {
            "تاریخ": [
                "1403-01-05", "1403-01-10", "1403-01-20",
                "1403-02-05", "1403-02-10", "1403-02-20",
            ],
            "کانال فروش": ["اینستاگرام", "دیجی‌کالا", "حضوری", "اینستاگرام", "دیجی‌کالا", "حضوری"],
            "فروش": [1000, 500, 300, 700, 550, 100],
        }
    )


def test_aggregate_intent(sales_df):
    intent = nlu.parse_question("مجموع فروش چقدر است؟", sales_df)
    assert intent.kind == "aggregate"
    assert intent.metric_col == "فروش"
    assert intent.func == "sum"


def test_mean_intent(sales_df):
    intent = nlu.parse_question("میانگین فروش چقدر است؟", sales_df)
    assert intent.func == "mean"


def test_groupby_intent(sales_df):
    intent = nlu.parse_question("فروش به تفکیک کانال فروش چقدر است؟", sales_df)
    assert intent.kind == "groupby"
    assert intent.group_col == "کانال فروش"
    assert intent.metric_col == "فروش"


def test_explain_change_intent(sales_df):
    intent = nlu.parse_question("چرا فروش افت کرد؟", sales_df)
    assert intent.kind == "explain_change"
    assert intent.metric_col == "فروش"
    assert intent.date_col == "تاریخ"
    assert intent.group_col == "کانال فروش"


def test_fallback_intent(sales_df):
    empty_df = pd.DataFrame({"چیزی": ["الف", "ب"]})
    intent = nlu.parse_question("امروز هوا چطوره؟", empty_df)
    assert intent.kind == "fallback"


def test_irrelevant_question_falls_back_even_with_single_numeric_column(sales_df):
    # نباید به‌صرف وجود یک ستون عددی، سؤال بی‌ربط را به آن نسبت بدهد
    intent = nlu.parse_question("امروز هوا چطوره؟", sales_df)
    assert intent.kind == "fallback"


def test_groupby_min_uses_sum_per_group_not_row_min(sales_df):
    # «کمترین فروش کدام کانال» یعنی کمترین مجموع فروش هر کانال، نه کوچک‌ترین تک‌رکورد
    intent = nlu.parse_question("کمترین فروش در کدام کانال فروش بوده؟", sales_df)
    assert intent.kind == "groupby"
    assert intent.func == "sum"
    assert intent.ascending is True
