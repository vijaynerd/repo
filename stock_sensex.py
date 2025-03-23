import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import finance_calculator as fc  # Ensure this module has get_xirr function


'''This program simulates a **hybrid investment strategy** involving **monthly investments in Sensex (Indian stock index)** and **arbitrage mutual funds**, dynamically switching allocations between the two based on market conditions. Here's a high-level breakdown:

---

### **Key Objectives**
1. **Simulate investment growth** over 2001–2023 using:
   - Direct investments in Sensex.
   - Investments in an arbitrage fund (assumed fixed 6% return).
   - A **hybrid strategy** that reallocates between the two based on "market advantage."

2. **Compare performance** of these strategies using **XIRR (extended internal rate of return)**.

3. **Visualize performance** through plots of returns, investments, and rebalancing events.

---

### **Core Components**
#### 1. **Data Download and Preparation**
- Fetches historical **Sensex index data** using Yahoo Finance.
- Prepares idealized growth curves:
   - Sensex ideal growth at **14% XIRR**.
   - Arbitrage ideal growth at **6% XIRR**.
- Calculates **Sensex advantage**: actual Sensex vs idealized 14% growth, as a percentage.

---

#### 2. **Investment Simulation Loop (Daily)**
For each day in the dataset:
- Tracks total invested money, Sensex and arbitrage balances.
- On specified **SIP (Systematic Investment Plan) day**, evaluates Sensex’s performance:
   - If **Sensex underperforms ideal by >5%**, it recommends **switching funds from arbitrage to Sensex**.
   - If **Sensex overperforms ideal by >5%**, it recommends **switching funds from Sensex to arbitrage**.
   - **Swap amount** is capped at 10% (to Sensex) or 30% (to arbitrage) of the respective fund’s balance.
- Logs these recommendations and updates balances accordingly.

---

#### 3. **Cash Flow and Returns Calculation**
- Records all **investment outflows (deposits)** and final **inflows (portfolio values)**.
- Calculates **XIRR** for:
   - Arbitrage-only investment.
   - Sensex-only SIP.
   - Hybrid strategy.

---

#### 4. **Visualization**
Generates 3 plots:
1. **Sensex vs Ideal Growth** over time.
2. **Portfolio Value Comparison**: investment vs current balances.
3. **Sensex Advantage %**: deviation of real performance from ideal.

---

### **Summary of Output**
- Investment rebalancing logs.
- Cash flow details.
- XIRR for each strategy.
- Plots to visually compare strategy effectiveness.

---

### **Purpose / Use Case**
To evaluate how dynamically switching between stock index investments and safer arbitrage funds based on market performance could affect long-term returns compared to static investment strategies.

---

Let me know if you'd like a simplified analogy or deeper dive into a specific part like the rebalancing logic or XIRR calculation!'''

def compound_interest(principal, rate, time):
    """Calculates compound interest."""
    amount = principal * pow((1 + rate / 100), time)
    return amount - principal

def hybrid_investment(inv_day):
    pd.set_option('mode.chained_assignment', None)

    # Initialize variables
    cashflow_data = []
    cashflow_data_sensex = []
    cashflow_data_hybrid = []
    sensex_balance = 0
    arb_balance = 0

    # Configuration
    start = "2001-01-25"
    end = '2023-02-08'
    sensex_xirr = 14
    arbitrage_xirr = 6
    sip_amount = 10000
    sip_day = inv_day
    investments = {pd.Timestamp('2001-05-30'): 30000000}

    # Download Sensex data
    sensex = yf.download('^BSESN', start=start, end=end)
    sensex.index = pd.to_datetime(sensex.index)
    sensex.columns = sensex.columns.droplevel(1)  # Drop 'Ticker' level

    # Clone DataFrames for calculations
    sensex_ideal = sensex.copy()
    sensex_advantage = sensex.copy()
    arbitrage_ideal = sensex.copy()

    # Initialize SIP-related DataFrames with zero 'Open' values
    sensex_sip = sensex.copy()
    sensex_sip['Open'] = 0
    sensex_sip_value = sensex_sip.copy()
    inv_value = sensex_sip.copy()
    arbitrage_sip = sensex_sip.copy()
    arbitrage_sip_value = sensex_sip.copy()
    sensex_balance_value = sensex_sip.copy()
    arb_balance_value = sensex_sip.copy()
    total_balance_value = sensex_sip.copy()

    len_sensex = len(sensex.index) - 1
    delta = (sensex_ideal.iat[len_sensex, 0] - sensex_ideal.iat[0, 0]) / len_sensex

    i = 0
    yr_month_old = ""

    for ind in sensex.index:
        algo_sip = 0
        algo_recommendation_buy = 0
        start_ind = int(i / 365)
        end_ind = min((start_ind + 1) * 365, len_sensex)

        days = ind - sensex_ideal.index[0]
        yrs = days.days / 365.25
        yr_month = f"{ind.year}{ind.month}"

        if i > 0:
            sensex_ideal.loc[ind, 'Open'] = sensex_ideal.iat[0, 0] + compound_interest(sensex_ideal.iat[0, 0], sensex_xirr, yrs)
            arbitrage_ideal.loc[ind, 'Open'] = arbitrage_ideal.iat[0, 0] + compound_interest(arbitrage_ideal.iat[0, 0], arbitrage_xirr, yrs)

        sensex_advantage.loc[ind, 'Open'] = ((sensex.loc[ind, 'Open'] - sensex_ideal.loc[ind, 'Open']) / sensex_ideal.loc[ind, 'Open']) * 100

        nonsip = investments.get(ind, 0)

        arb_balance += nonsip / arbitrage_ideal.loc[ind, 'Open']

        if yr_month != yr_month_old and i > 0 and ind.day >= sip_day:
            sip = sip_amount
            yr_month_old = yr_month
            print("sensex advantage", ind, sensex_advantage.loc[ind, 'Open'], 
                  "arb_balance", arb_balance, "sensex balance", sensex_balance)
            
            # print(f"ind: {ind}, type: {type(ind)}")
            # print(f"Index contains ind? {ind in sensex_advantage.index}")

            # print(f"ind: {ind}, type: {type(ind)}")
            # print(f"sensex_advantage.columns: {sensex_advantage.columns}")
            # print(f"sensex_advantage.index.dtype: {sensex_advantage.index.dtype}")
            # print(f"sensex_advantage.loc[ind]:\n{sensex_advantage.loc[ind]}")
            # print(f"sensex_advantage.loc[ind, 'Open']: {sensex_advantage.loc[ind, 'Open']}")
            try:
                val = sensex_advantage.loc[ind, 'Open']
                if isinstance(val, pd.Series):
                    if val < -5:
                        swap_sensex_pct = min(10, int((-sensex_advantage.loc[ind, 'Open']) / 5) * 5)
                        if swap_sensex_pct > 0 and arb_balance > 10:
                            print("Swap recommendation", ind, "swap arbitrage to sensex %", swap_sensex_pct)
                            swap_amount = swap_sensex_pct * arb_balance * arbitrage_ideal.loc[ind, 'Open'] / 100
                            arb_balance -= swap_amount / arbitrage_ideal.loc[ind, 'Open']
                            sensex_balance += swap_amount / sensex_ideal.loc[ind, 'Open']
                            print("Updated balances - sensex:", sensex_balance * sensex_ideal.loc[ind, 'Open'],
                                "arbitrage:", arb_balance * arbitrage_ideal.loc[ind, 'Open'])
            except KeyError:
                print(f"KeyError: {ind} not found in sensex_advantage")
            except Exception as e:
                print(f"Unexpected error at index {ind}: {e}")

            if sensex_advantage.at[ind, 'Open'] < -5:
                swap_sensex_pct = min(10, int((-sensex_advantage.loc[ind, 'Open']) / 5) * 5)
                if swap_sensex_pct > 0 and arb_balance > 10:
                    print("Swap recommendation", ind, "swap arbitrage to sensex %", swap_sensex_pct)
                    swap_amount = swap_sensex_pct * arb_balance * arbitrage_ideal.loc[ind, 'Open'] / 100
                    arb_balance -= swap_amount / arbitrage_ideal.loc[ind, 'Open']
                    sensex_balance += swap_amount / sensex_ideal.loc[ind, 'Open']
                    print("Updated balances - sensex:", sensex_balance * sensex_ideal.loc[ind, 'Open'],
                          "arbitrage:", arb_balance * arbitrage_ideal.loc[ind, 'Open'])

            if sensex_advantage.at[ind, 'Open'] > 5:
                swap_arb_pct = min(30, int(sensex_advantage.loc[ind, 'Open'] / 5) * 5)
                if swap_arb_pct > 0 and sensex_balance > 10:
                    print("Swap recommendation", ind, "swap sensex to arbitrage %", swap_arb_pct)
                    swap_amount = swap_arb_pct * sensex_balance * sensex_ideal.loc[ind, 'Open'] / 100
                    sensex_balance -= swap_amount / sensex_ideal.loc[ind, 'Open']
                    arb_balance += swap_amount / arbitrage_ideal.loc[ind, 'Open']
                    print("Updated balances - sensex:", sensex_balance * sensex_ideal.loc[ind, 'Open'],
                          "arbitrage:", arb_balance * arbitrage_ideal.loc[ind, 'Open'])
        else:
            sip = 0

        total_inv = sip + nonsip + algo_sip

        if i > 0:
            sensex_sip.loc[ind, 'Open'] = sensex_sip.iloc[i - 1, 0] + total_inv / sensex.loc[ind, 'Open']
            sensex_sip_value.loc[ind, 'Open'] = sensex_sip.loc[ind, 'Open'] * sensex.loc[ind, 'Open']
            arbitrage_sip.loc[ind, 'Open'] = arbitrage_sip.iloc[i - 1, 0] + total_inv / arbitrage_ideal.loc[ind, 'Open']
            arbitrage_sip_value.loc[ind, 'Open'] = arbitrage_sip.loc[ind, 'Open'] * arbitrage_ideal.loc[ind, 'Open']
            inv_value.loc[ind, 'Open'] = inv_value.iloc[i - 1, 0] + total_inv
            sensex_balance_value.loc[ind, 'Open'] = sensex_balance * sensex_ideal.loc[ind, 'Open']
            arb_balance_value.loc[ind, 'Open'] = arb_balance * arbitrage_ideal.loc[ind, 'Open']
            total_balance_value.loc[ind, 'Open'] = sensex_balance_value.loc[ind, 'Open'] + arb_balance_value.loc[ind, 'Open']

        if total_inv != 0:
            cashflow_data.append((ind, -total_inv))

        i += 1

    # Append final value on 2023-02-22
    end_date = pd.Timestamp(datetime.date(2023, 2, 22))
    cashflow_data.append((end_date, int(arbitrage_sip_value['Open'].iloc[-1])))
    cashflow_data_sensex = cashflow_data.copy()
    cashflow_data_sensex[-1] = (end_date, int(sensex_sip_value['Open'].iloc[-1]))
    cashflow_data_hybrid = cashflow_data.copy()
    #cashflow_data_hybrid[-1] = (end_date, int(sensex_balance_value['Open'].iloc[-1]) + int(arb_balance_value['Open'].iloc[-1])))
    cashflow_data_hybrid[-1] = (end_date, int(sensex_balance_value['Open'].iloc[-1]) + int(arb_balance_value['Open'].iloc[-1]))

    # Print cashflows
    print(cashflow_data)
    print(cashflow_data_sensex)

    # Calculate XIRR
    arb_xirr = fc.get_xirr(cashflow_data)
    sip_sensex_xirr = fc.get_xirr(cashflow_data_sensex)
    hybrid_xirr = fc.get_xirr(cashflow_data_hybrid)

    print("XIRR for Arbitrage Savings:", arb_xirr)
    print("XIRR for Sensex SIP:", sip_sensex_xirr)
    print("XIRR for Hybrid Strategy:", hybrid_xirr)

    # Plotting
    fig = plt.figure(figsize=(15, 10))

    ax1 = fig.add_subplot(221)
    sensex['Open'].plot(label='Sensex')
    sensex_ideal['Open'].plot(label=f'Sensex Ideal ({sensex_xirr}%)')
    arbitrage_ideal['Open'].plot(label=f'Arbitrage Ideal ({arbitrage_xirr}%)')
    plt.title('Sensex vs Ideal Growth')
    plt.legend()

    ax2 = fig.add_subplot(222)
    inv_value['Open'].plot(label='Invested Amount')
    sensex_balance_value['Open'].plot(label='Sensex Balance Value')
    arb_balance_value['Open'].plot(label='Arbitrage Balance Value')
    plt.title(f'Portfolio Value Comparison\nArbitrage XIRR: {arb_xirr:.2f}% | Sensex XIRR: {sip_sensex_xirr:.2f}%')
    plt.legend()

    ax3 = fig.add_subplot(223)
    sensex_advantage['Open'].plot(label='Sensex Advantage %')
    plt.title('Sensex Advantage Over Ideal')
    plt.legend()

    plt.tight_layout()
    plt.show()

# Run hybrid investment strategy for day 5
for i in range(5, 6):
    print("Day of investment:", i)
    hybrid_investment(i)
