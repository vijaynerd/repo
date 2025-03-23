import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import math
import numpy_financial as npf

# ---------- User Inputs ----------
lumpsum_investments = [
    {"date": "2010-01-15", "amount": 100000},
    {"date": "2012-06-10", "amount": 50000}
]

sip_amount = 10000
sip_day_of_month = 10

# ---------- Constants ----------
START_DATE = "2006-01-01"
END_DATE = "2025-01-01"
ARBITRAGE_ANNUAL_RETURN = 0.06  # 6% fixed annual return
IDEAL_SENSEX_RETURN = 0.12      # 14% ideal return
SWAP_TO_SENSEX_THRESHOLD = -5   # in %
SWAP_TO_ARBITRAGE_THRESHOLD = 5
SWAP_TO_SENSEX_CAP = 0.10       # 10%
SWAP_TO_ARBITRAGE_CAP = 0.30    # 30%

# ---------- Download Sensex Data ----------
sensex_data = yf.download("^BSESN", start=START_DATE, end=END_DATE)
sensex_data.columns = sensex_data.columns.droplevel(1)  # Drop 'Ticker' level

sensex_data = sensex_data[['Close']].rename(columns={'Close': 'Sensex'})
sensex_data = sensex_data.ffill().reset_index()
sensex_data['Date'] = pd.to_datetime(sensex_data['Date'])
sensex_data.set_index('Date', inplace=True)

# ---------- Ideal Growth Curves ----------
initial_sensex = sensex_data.iloc[0]['Sensex']
days_since_start = (sensex_data.index - sensex_data.index[0]).days.values
ideal_sensex = initial_sensex * np.power(1 + IDEAL_SENSEX_RETURN, days_since_start / 365)
sensex_data['Ideal_Sensex'] = ideal_sensex
sensex_data['Sensex_Advantage_%'] = ((sensex_data['Sensex'] - sensex_data['Ideal_Sensex']) / sensex_data['Ideal_Sensex']) * 100

# ---------- Investment Simulation ----------
# Initialize balances and logs
arbitrage_balance = 0
sensex_units = 0
sensex_only_units = 0
total_invested = 0
cash_flows_hybrid = []
cash_flows_sensex_only = []
cash_flows_arbitrage_only = []
sip_dates = []
swap_logs = []

# Helper for XIRR
def xirr(cash_flows):
    if not cash_flows:
        return 0.0
    def npv(rate):
        return sum(cf / (1 + rate) ** ((d - cash_flows[0][0]).days / 365) for d, cf in cash_flows)

    rate = 0.1
    for _ in range(100):
        f = npv(rate)
        f_deriv = sum(-((d - cash_flows[0][0]).days / 365) * cf / (1 + rate) ** (((d - cash_flows[0][0]).days / 365) + 1) for d, cf in cash_flows)
        rate -= f / f_deriv
        if abs(f) < 1e-6:
            break
    return rate

# Prepare date ranges
current_date = pd.to_datetime("2010-01-01")
end_date = sensex_data.index[-1]

# Pre-calculate arbitrage growth factor
arbitrage_daily_rate = (1 + ARBITRAGE_ANNUAL_RETURN) ** (1 / 365)

invest_lump_next_sensex_date = 0
sip_done_today = False
current_month_year = None
loop_month_year = None
current_month_year_sipdone = False
# Daily simulation loop
while current_date <= end_date:
    # Grow arbitrage fund daily
    current_month_year = current_date.strftime("%Y-%m")
    if loop_month_year != current_month_year:
        loop_month_year = current_month_year
        current_month_year_sipdone = False
    arbitrage_balance *= arbitrage_daily_rate
    #print(current_date.date(), arbitrage_balance)

    # Check for lumpsum on this date
    for lump in lumpsum_investments:
        lump_date = pd.to_datetime(lump["date"])
        if lump_date == current_date:
            invest_lump_next_sensex_date = lump["amount"]

    if current_date not in sensex_data.index:
        current_date += timedelta(days=1)
        continue

    if invest_lump_next_sensex_date != 0:
        arbitrage_balance += invest_lump_next_sensex_date
        total_invested += invest_lump_next_sensex_date
        cash_flows_hybrid.append((current_date, - invest_lump_next_sensex_date))
        cash_flows_arbitrage_only.append((current_date, - invest_lump_next_sensex_date))
        cash_flows_sensex_only.append((current_date, - invest_lump_next_sensex_date))
        invest_lump_next_sensex_date = 0

    # Check for SIP date
    if current_date.day >= sip_day_of_month and current_month_year_sipdone == False:
        current_month_year_sipdone = True
        # Add SIP to arbitrage
        sip_done_today = True
        arbitrage_balance += sip_amount
        total_invested += sip_amount
        cash_flows_hybrid.append((current_date, -sip_amount))
        cash_flows_arbitrage_only.append((current_date, -sip_amount))
        cash_flows_sensex_only.append((current_date, -sip_amount))
        sip_dates.append(current_date)
        current_sensex_price = sensex_data.loc[current_date, 'Sensex']
        units = sip_amount / current_sensex_price
        sensex_only_units += units

    else:
        sip_done_today = False

    # Rebalancing Logic
    if current_date in sensex_data.index and sip_done_today:
        #print("rebalancing today: ", current_date, sensex_data.loc[current_date, 'Sensex_Advantage_%'],arbitrage_balance,sensex_units)
        advantage = sensex_data.loc[current_date, 'Sensex_Advantage_%']
        current_sensex_price = sensex_data.loc[current_date, 'Sensex']

        if advantage < SWAP_TO_SENSEX_THRESHOLD and arbitrage_balance > 0:
            # Move from Arbitrage to Sensex
            amount_to_swap = min(arbitrage_balance * SWAP_TO_SENSEX_CAP, arbitrage_balance)
            if amount_to_swap > 0:
                units = amount_to_swap / current_sensex_price
                sensex_units += units
                arbitrage_balance -= amount_to_swap
                swap_logs.append(f"{current_date.date()} | Swap {amount_to_swap:.2f} to Sensex | Advantage: {advantage:.2f}%")
                print("rebalancing to sensex today: ", current_date, sensex_data.loc[current_date, 'Sensex_Advantage_%'],arbitrage_balance,sensex_units)

        elif advantage > SWAP_TO_ARBITRAGE_THRESHOLD and sensex_units > 0:
            # Move from Sensex to Arbitrage
            value_of_sensex = sensex_units * current_sensex_price
            amount_to_swap = min(value_of_sensex * SWAP_TO_ARBITRAGE_CAP, value_of_sensex)
            if amount_to_swap > 0:
                units_to_sell = amount_to_swap / current_sensex_price
                sensex_units -= units_to_sell
                arbitrage_balance += amount_to_swap
                swap_logs.append(f"{current_date.date()} | Swap {amount_to_swap:.2f} to Arbitrage | Advantage: {advantage:.2f}%")
                print("rebalancing to arbitrage today: ", current_date, sensex_data.loc[current_date, 'Sensex_Advantage_%'],arbitrage_balance,sensex_units)

    current_date += timedelta(days=1)

# Final Portfolio Values
final_sensex_price = sensex_data.iloc[-1]['Sensex']
final_sensex_value = sensex_units * final_sensex_price
final_sensex_only_value = sensex_only_units * final_sensex_price
final_arbitrage_value = arbitrage_balance
final_portfolio_value = final_arbitrage_value + final_sensex_value

# Record inflows for XIRR
final_date = sensex_data.index[-1]
cash_flows_hybrid.append((final_date, final_portfolio_value))
#cash_flows_arbitrage_only.append((final_date, arbitrage_balance))

# Initialize total final value
total_final_value = 0.0

for date, amount in cash_flows_arbitrage_only:
    if amount < 0:  # SIP investment
        years_invested = (final_date - pd.to_datetime(date)).days / 365
        future_value = -amount * ((1 + ARBITRAGE_ANNUAL_RETURN) ** years_invested)
        total_final_value += future_value

final_arbitrage_only_value = total_final_value
cash_flows_arbitrage_only.append((final_date, total_final_value))
cash_flows_sensex_only.append((final_date, final_sensex_only_value))

# Calculate XIRRs
xirr_hybrid = xirr(cash_flows_hybrid) * 100
xirr_arbitrage_only = xirr(cash_flows_arbitrage_only) * 100
xirr_sensex_only = xirr(cash_flows_sensex_only) * 100

# ---------- Results Summary ----------
print("----- Investment Summary -----")
print(f"Total Invested: ₹{total_invested:,.2f}")
print(f"Final Hybrid Portfolio Value: ₹{final_portfolio_value:,.2f}")
print(f"Final Sensex Portfolio Value: ₹{final_sensex_only_value:,.2f}")
print(f"Final Arbitrage Portfolio Value: ₹{final_arbitrage_only_value:,.2f}")
print(f"XIRR - Hybrid Strategy: {xirr_hybrid:.2f}%")
print(f"XIRR - Arbitrage Only: {xirr_arbitrage_only:.2f}%")
print(f"XIRR - Sensex Only (Ideal): {xirr_sensex_only:.2f}%")
print("\n----- Swap Logs -----")
for log in swap_logs[-10:]:  # Show last 10 swaps
    print(log)

# ---------- Visualization ----------
plt.figure(figsize=(14, 8))

# Plot 1: Sensex vs Ideal
plt.subplot(3, 1, 1)
plt.plot(sensex_data.index, sensex_data['Sensex'], label='Actual Sensex')
plt.plot(sensex_data.index, sensex_data['Ideal_Sensex'], label='Ideal Sensex (14%)', linestyle='--')
plt.title("Sensex vs Ideal Growth")
plt.legend()

# Plot 2: Sensex Advantage %
plt.subplot(3, 1, 2)
plt.plot(sensex_data.index, sensex_data['Sensex_Advantage_%'])
plt.axhline(SWAP_TO_SENSEX_THRESHOLD, color='green', linestyle='--')
plt.axhline(SWAP_TO_ARBITRAGE_THRESHOLD, color='red', linestyle='--')
plt.title("Sensex Advantage (%) Over Time")

# Plot 3: Portfolio Value Growth (Simplified)
dates = [cf[0] for cf in cash_flows_hybrid]
invested = np.cumsum([-cf[1] for cf in cash_flows_hybrid if cf[1] < 0])
plt.subplot(3, 1, 3)
plt.plot(dates[:len(invested)], invested, label="Total Invested")
plt.axhline(final_portfolio_value, color='purple', label="Final Hybrid Value")
plt.title("Investment vs Portfolio Value")
plt.legend()

plt.tight_layout()
plt.show(block=True)
