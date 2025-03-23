import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import math
import numpy_financial as npf
from datetime import timedelta
import locale

locale.setlocale(locale.LC_ALL, 'en_IN.UTF-8')  # Use 'en_IN' locale


# ---------- User Inputs ----------
lumpsum_investments = [
    # {"date": "2010-01-15", "amount": 100000},
    # {"date": "2012-06-10", "amount": 50000}
]

sip_amount = 10000
sip_day_of_month = 10

# ---------- Constants ----------
START_DATE = "2001-01-01"
END_DATE = "2025-01-01"
ARBITRAGE_ANNUAL_RETURN = 0.06  # 6% fixed annual return
IDEAL_SENSEX_RETURN = 0.12      # 14% ideal return
IDEAL_XIRR = 0.12               # 14% ideal return
SWAP_TO_SENSEX_THRESHOLD = 0   # in %
SWAP_TO_ARBITRAGE_THRESHOLD = 2
SWAP_TO_SENSEX_CAP = 0.10       # 10%
SWAP_TO_ARBITRAGE_CAP = 0.10    # 30%

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
current_date = pd.to_datetime("2005-01-01")
end_date = sensex_data.index[-1]

# Pre-calculate arbitrage growth factor
arbitrage_daily_rate = (1 + ARBITRAGE_ANNUAL_RETURN) ** (1 / 365)

invest_lump_next_sensex_date = 0
sip_done_today = False
current_month_year = None
loop_month_year = None
current_month_year_sipdone = False

# Initialize tracking list before the loop
portfolio_values_over_time = []
invested_over_time = []
swap_event_dates = []
swap_event_values = []
swap_event_types = []  # "To Sensex" or "To Arbitrage"

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
        print("Investment to arbitrage today: ", current_date, "arb balance " , arbitrage_balance, "sensex balance" , sensex_units * current_sensex_price , "total balance: " , arbitrage_balance + sensex_units * current_sensex_price, "amount invested:",sip_amount)

    else:
        sip_done_today = False

    if(sip_done_today == False):
        current_date += timedelta(days=1)
        continue
    advantage_xirr = 0
    current_xirr = 0
    # Within simulation loop:
    if current_date in sensex_data.index:
        current_sensex_price = sensex_data.loc[current_date, 'Sensex']
        current_portfolio_value = arbitrage_balance + sensex_units * current_sensex_price

        # Cash flows till now
        cash_flows_till_now = [cf for cf in cash_flows_hybrid if cf[0] <= current_date]

        # Add hypothetical liquidation on current date
        cash_flows_with_liquidation = cash_flows_till_now + [(current_date, current_portfolio_value)]

        # Compute current XIRR
        try:
            current_xirr = xirr(cash_flows_with_liquidation)
        except:
            current_xirr = 0  # Handle edge cases safely

        # Compute advantage relative to ideal
        advantage_xirr = ((current_xirr - IDEAL_XIRR) / IDEAL_XIRR) * 100

    ONE_YEAR_AGO = current_date - timedelta(days=365)

    # Filter cash flows from the last 1 year
    recent_cash_flows = [cf for cf in cash_flows_hybrid if ONE_YEAR_AGO <= cf[0] <= current_date]

    # Add hypothetical liquidation at current date
    current_portfolio_value = arbitrage_balance + sensex_units * sensex_data.loc[current_date, 'Sensex']
    recent_cash_flows += [(current_date, current_portfolio_value)]

    # Compute 1-year XIRR
    try:
        recent_xirr = xirr(recent_cash_flows)
        print("recent xirr: ", recent_xirr)
    except:
        recent_xirr = 0  # Handle no cash flows or invalid cases

    # # Advantage relative to ideal return
    # advantage_recent = ((recent_xirr - IDEAL_XIRR) / IDEAL_XIRR) * 100

    # Rebalancing Logic
    if current_date in sensex_data.index and sip_done_today:
        #print("rebalancing today: ", current_date, sensex_data.loc[current_date, 'Sensex_Advantage_%'],arbitrage_balance,sensex_units)
        advantage = sensex_data.loc[current_date, 'Sensex_Advantage_%']
        current_sensex_price = sensex_data.loc[current_date, 'Sensex']

        #if (advantage < SWAP_TO_SENSEX_THRESHOLD and arbitrage_balance > 0) or advantage_xirr < IDEAL_XIRR:
        if current_xirr < IDEAL_XIRR:
            # Move from Arbitrage to Sensex
            amount_to_swap = min(arbitrage_balance * SWAP_TO_SENSEX_CAP, arbitrage_balance)
            if amount_to_swap > 0:
                units = amount_to_swap / current_sensex_price
                sensex_units += units
                arbitrage_balance -= amount_to_swap
                swap_logs.append(f"{current_date.date()} | Swap {amount_to_swap:.2f} to Sensex | Advantage: {advantage:.2f}%")
                #print("rebalancing to sensex today: ", current_date, sensex_data.loc[current_date, 'Sensex_Advantage_%'],arbitrage_balance,sensex_units)
                print("Rebalance to Sensex today    : ", current_date, "arb balance " , arbitrage_balance, "sensex balance" , sensex_units * current_sensex_price , "total balance: " , arbitrage_balance + sensex_units * current_sensex_price, "amount swapped:",amount_to_swap)
                # Log swap events
                swap_event_dates.append(current_date)
                current_sensex_price = sensex_data.loc[current_date, 'Sensex']
                daily_portfolio_value = arbitrage_balance + sensex_units * current_sensex_price
                swap_event_values.append(daily_portfolio_value)
                swap_event_types.append("To Sensex")

        #elif (advantage > SWAP_TO_ARBITRAGE_THRESHOLD and sensex_units > 0) or advantage_xirr > IDEAL_XIRR:
        elif current_xirr > IDEAL_XIRR:
            # Move from Sensex to Arbitrage
            value_of_sensex = sensex_units * current_sensex_price
            amount_to_swap = min(value_of_sensex * SWAP_TO_ARBITRAGE_CAP, value_of_sensex)
            if amount_to_swap > 0:
                units_to_sell = amount_to_swap / current_sensex_price
                sensex_units -= units_to_sell
                arbitrage_balance += amount_to_swap
                swap_logs.append(f"{current_date.date()} | Swap {amount_to_swap:.2f} to Arbitrage | Advantage: {advantage:.2f}%")
                #print("rebalancing to arbitrage today: ", current_date, sensex_data.loc[current_date, 'Sensex_Advantage_%'],arbitrage_balance,sensex_units)
                print("Rebalance to arbitrage today    : ", current_date, "arb balance " , arbitrage_balance, "sensex balance" , sensex_units * current_sensex_price , "total balance: " , arbitrage_balance + sensex_units * current_sensex_price, "amount swapped:",amount_to_swap)
                # Log swap events
                swap_event_dates.append(current_date)
                current_sensex_price = sensex_data.loc[current_date, 'Sensex']
                daily_portfolio_value = arbitrage_balance + sensex_units * current_sensex_price
                swap_event_values.append(daily_portfolio_value)
                swap_event_types.append("To Arbitrage")

    # Inside the loop, after rebalancing logic
    if current_date in sensex_data.index:
        current_sensex_price = sensex_data.loc[current_date, 'Sensex']
        daily_portfolio_value = arbitrage_balance + sensex_units * current_sensex_price
        portfolio_values_over_time.append((current_date, daily_portfolio_value))

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
final_portfolio_value_formated = locale.currency(final_portfolio_value, symbol='₹', grouping=True)
print(f"Final Hybrid Portfolio Value: {final_portfolio_value_formated}")
final_sensex_only_value_formated = locale.currency(final_sensex_only_value, symbol='₹', grouping=True)
print(f"Final Sensex Portfolio Value: {final_sensex_only_value_formated}")
final_arbitrage_only_value_formated = locale.currency(final_arbitrage_only_value, symbol='₹', grouping=True)
print(f"Final Arbitrage Portfolio Value: {final_arbitrage_only_value_formated}")
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


# Extract data
plot_dates = [entry[0] for entry in portfolio_values_over_time]
plot_values = [entry[1] for entry in portfolio_values_over_time]
invested_dates = [entry[0] for entry in invested_over_time]
invested_values = [entry[1] for entry in invested_over_time]

# Plot
plt.figure(figsize=(14, 7))
plt.plot(plot_dates, plot_values, label="Hybrid Portfolio Value", color='blue')
plt.plot(invested_dates, invested_values, label="Total Invested", color='orange', linestyle='--')


# Track which event types have been labeled
labeled_event_types = set()

# Mark swap events
for i, event_date in enumerate(swap_event_dates):
    value = swap_event_values[i]
    event_type = swap_event_types[i]
    color = 'green' if event_type == "To Sensex" else 'red'
    marker = '^' if event_type == "To Sensex" else 'v'
    # Add label only once per event_type
    label = event_type if event_type not in labeled_event_types else ""
    plt.scatter(event_date, value, color=color, marker=marker, s=50, label=label)

# Labels & Styling
plt.title("Hybrid Investment Growth with Swaps & Total Invested")
plt.xlabel("Date")
plt.ylabel("Value (₹)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show(block=True)

# # Plot 3: Portfolio Value Growth (Simplified)
# dates = [cf[0] for cf in cash_flows_hybrid]
# invested = np.cumsum([-cf[1] for cf in cash_flows_hybrid if cf[1] < 0])

# plt.subplot(3, 1, 3)
# plt.plot(dates[:len(invested)], invested, label="Total Invested")
# plt.axhline(final_portfolio_value, color='purple', label="Final Hybrid Value")
# plt.title("Investment vs Portfolio Value")
# plt.legend()

# plt.tight_layout()
# plt.show(block=True)
