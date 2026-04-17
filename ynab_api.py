"""
ynab_api.py — Fetch monthly financial snapshot from YNAB API.
"""
from datetime import date
import requests
import streamlit as st

BASE_URL = "https://api.ynab.com/v1"


def _headers():
    token = st.secrets["ynab"]["api_token"]
    return {"Authorization": f"Bearer {token}"}


def _budget_id():
    return st.secrets["ynab"].get("budget_id", "last-used")


def fetch_finance_snapshot() -> dict:
    """
    Returns a dict with:
    - net_worth: sum of all on-budget account balances
    - monthly_income: total inflows this month
    - savings_rate_pct: (income - spending) / income * 100
    """
    result = {
        "net_worth": 0.0,
        "monthly_income": 0.0,
        "savings_rate_pct": 0.0,
    }

    try:
        budget_id = _budget_id()
        month_str = date.today().strftime("%Y-%m-01")

        # ── Net worth from accounts ────────────────────────────────────────
        acct_resp = requests.get(
            f"{BASE_URL}/budgets/{budget_id}/accounts",
            headers=_headers(), timeout=10
        )
        if acct_resp.status_code == 200:
            accounts = acct_resp.json()["data"]["accounts"]
            net_worth = sum(
                a["balance"] for a in accounts
                if not a["closed"] and not a["deleted"]
            )
            result["net_worth"] = round(net_worth / 1000, 2)

        # ── This month's transactions ──────────────────────────────────────
        txn_resp = requests.get(
            f"{BASE_URL}/budgets/{budget_id}/transactions",
            headers=_headers(),
            params={"since_date": month_str},
            timeout=10
        )
        if txn_resp.status_code == 200:
            transactions = txn_resp.json()["data"]["transactions"]

            monthly_income   = 0.0
            monthly_spending = 0.0

            for txn in transactions:
                if txn.get("deleted"):
                    continue
                amount = txn["amount"] / 1000

                if amount > 0:
                    monthly_income += amount
                else:
                    monthly_spending += abs(amount)

            result["monthly_income"] = round(monthly_income, 2)

            if monthly_income > 0:
                savings = (monthly_income - monthly_spending) / monthly_income * 100
                result["savings_rate_pct"] = round(max(savings, 0), 1)

    except Exception as e:
        st.warning(f"Could not fetch YNAB data: {e}")

    return result
