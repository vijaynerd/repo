from sqlite3 import Timestamp
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
from pandas.plotting import scatter_matrix
import yfinance as yf
import finance_calculator as fc


def compound_interest(principal, rate, time):
 
    # Calculates compound interest
    Amount = principal * (pow((1 + rate / 100), time))
    CI = Amount - principal
    #print("Compound interest for years ",time," is", CI)
    return CI

cashflow_data = []
cashflow_data_sensex = []
total_balance = 0
sensex_balance = 0
arb_balance = 0

start = "2001-11-01"
end = '2023-2-08'
sensex_xirr = 20
arbitrage_xirr = 6
sip_amount = 0
sip_day = 5
#investments={pd.Timestamp('2020-03-16'):300000}
investments={}
sensex = yf.download('^BSESN',start,end)
sensex_ideal = sensex.copy()
sensex_advantage = sensex.copy()
arbitrage_ideal = sensex.copy()

sensex_sip = sensex.copy()
for ind in sensex_sip.index:
    sensex_sip['Open'][ind] = 0

sensex_sip_value = sensex_sip.copy()
inv_value = sensex_sip.copy()
arbitrage_sip = sensex_sip.copy()
arbitrage_sip_value = sensex_sip.copy()


inv_sensex = sensex.copy()
inv_arbitrage = sensex.copy()

len_sensex = len(sensex.index) -1

print(sensex_ideal.iat[0,0])
print(sensex_ideal.iat[len_sensex,0])

delta = (sensex_ideal.iat[len_sensex,0] - sensex_ideal.iat[0,0]) / len_sensex

i = 0

yr_month_old = ""
algo_recommendation_buy = 0
for ind in sensex_ideal.index:
    algo_sip = 0
    algo_recommendation_buy = 0
    start_ind = int(i / 365)
    if((start_ind + 1) * 365 > len_sensex):
        end_ind = len_sensex
    else:
        end_ind = (start_ind + 1) * 365
    days = ind - sensex_ideal.index[0]
    yrs = days.days / 365.25
    yr_month = str(ind.year) + str(ind.month)
    #sensex_sip['Open'][ind] = 999
    if i > 0:
        sensex_ideal['Open'][ind] =  sensex_ideal.iat[0,0] + compound_interest(sensex_ideal.iat[0,0],sensex_xirr,yrs)
        arbitrage_ideal['Open'][ind] =  arbitrage_ideal.iat[0,0] + compound_interest(arbitrage_ideal.iat[0,0],arbitrage_xirr,yrs)
    
    sensex_advantage['Open'][ind] = ((sensex['Open'][ind] - sensex_ideal['Open'][ind] ) / sensex_ideal['Open'][ind]) * 100
    
    if investments.get(ind) is not None:
        nonsip = investments[ind]
    else:
        nonsip = 0
        
    if (yr_month != yr_month_old and i > 0 and ind.day >= 5):
        sip = sip_amount
        yr_month_old = yr_month
        if sensex_advantage['Open'][ind] < -5:
            algo_recommendation_buy = int((0 - sensex_advantage['Open'][ind]) / 5 ) * 5
            if(algo_recommendation_buy > 0):
                print("Buy recommendation ",ind," swap arbitrage to sense %",algo_recommendation_buy)
                algo_sip = algo_recommendation_buy * 50000
    else:
        sip = 0
    
        
    total_inv = sip + nonsip + algo_sip
        
    if i > 0: 
        sensex_sip['Open'][ind] = sensex_sip.iat[i-1,0] + total_inv / sensex['Open'][ind]
        sensex_sip_value['Open'][ind] = sensex_sip['Open'][ind] * sensex['Open'][ind]
        arbitrage_sip['Open'][ind] = arbitrage_sip.iat[i-1,0] + total_inv / arbitrage_ideal['Open'][ind]
        arbitrage_sip_value['Open'][ind] = arbitrage_sip['Open'][ind] * arbitrage_ideal['Open'][ind]
        inv_value['Open'][ind] = inv_value.iat[i-1,0] + total_inv
        
    if (total_inv !=0):
        cashflow_data.append((ind,(0-total_inv)))
            
    
        
        #sensex_ideal['Open'][ind] =  sensex_ideal.iat[start_ind,0] + delta_s
    i = i + 1

infy = yf.download('INFY.NS',start,end)
wipro = yf.download('WIPRO.NS',start,end)
print(arbitrage_sip_value.iloc[-1][0] )

cashflow_data_sensex = cashflow_data.copy()
cashflow_data.append((pd.Timestamp(datetime.date(2023, 2, 22)),int(arbitrage_sip_value['Open'].iloc[-1])))
cashflow_data_sensex.append((pd.Timestamp(datetime.date(2023, 2, 22)),int(sensex_sip_value['Open'].iloc[-1])))

arb_xirr = fc.get_xirr(cashflow_data)
sip_sensex_xirr = fc.get_xirr(cashflow_data_sensex)

print("XIRR for arbitrage" , arb_xirr)
print("XIRR for Sensex" , sip_sensex_xirr)

#fig, axes = plt.subplots(nrows=2, ncols=1)

fig = plt.figure()
ax = fig.add_subplot(221)



sensex['Open'].plot(label = 'sensex', figsize = (15,7))
sensex_ideal['Open'].plot(label = 'sensex_ideal 12%')
arbitrage_ideal['Open'].plot(label = 'arbitrage 6%')
#sensex_sip_value['Open'].plot(label = 'Sensex sip 50000')
#inv_value['Open'].plot(label = 'Invested amount')
#infy['Open'].plot(label = "Infosys.NS")
#wipro['Open'].plot(label = 'Wipro.NS')
plt.title('Prices of sensex Analysis')
#print(sensex)
plt.legend()
#plt.show()

ax = fig.add_subplot(222)
sensex_sip_value['Open'].plot(label = 'Sensex sip ')
inv_value['Open'].plot(label = 'Invested amount')
arbitrage_sip_value['Open'].plot(label = 'Arbitrage sip')

#infy['Open'].plot(label = "Infosys.NS")
#wipro['Open'].plot(label = 'Wipro.NS')
plt.title('Sensex vs Arbitrage arb_xirr = '+'%.2f'%arb_xirr+'sensex_xirr = '+'%.2f'%sip_sensex_xirr)
#print(sensex)
plt.legend()
#plt.show()
#exit()


ax = fig.add_subplot(223)
sensex_advantage['Open'].plot(label = 'sensex', figsize = (15,7))
#infy['Open'].plot(label = "Infosys.NS")
#wipro['Open'].plot(label = 'Wipro.NS')
plt.title('Sensex advantage plot')
#print(sensex)
plt.legend()
plt.show()


exit(0)

sensex['Volume'].plot(label = 'sensex', figsize = (15,7))
infy['Volume'].plot(label = "Infosys")
wipro['Volume'].plot(label = 'Wipro')
plt.title('Volume of Stock traded')
plt.legend()
plt.show()

#Market Capitalisation
sensex['MarktCap'] = sensex['Open'] * sensex['Volume']
infy['MarktCap'] = infy['Open'] * infy['Volume']
wipro['MarktCap'] = wipro['Open'] * wipro['Volume']
sensex['MarktCap'].plot(label = 'sensex', figsize = (15,7))
infy['MarktCap'].plot(label = 'Infosys')
wipro['MarktCap'].plot(label = 'Wipro')
plt.title('Market Cap')
plt.legend()
plt.show()


sensex['MA50'] = sensex['Open'].rolling(50).mean()
sensex['MA200'] = sensex['Open'].rolling(200).mean()
sensex['Open'].plot(figsize = (15,7))
sensex['MA50'].plot()
sensex['MA200'].plot()
data = pd.concat([sensex['Open'],infy['Open'],wipro['Open']],axis = 1)
data.columns = ['sensexOpen','InfosysOpen','WiproOpen']
scatter_matrix(data, figsize = (8,8), hist_kwds= {'bins':250})


#Volatility
sensex['returns'] = (sensex['Close']/sensex['Close'].shift(1)) -1
infy['returns'] = (infy['Close']/infy['Close'].shift(1))-1
wipro['returns'] = (wipro['Close']/wipro['Close'].shift(1)) - 1
sensex['returns'].hist(bins = 100, label = 'sensex', alpha = 0.5, figsize = (15,7))
infy['returns'].hist(bins = 100, label = 'Infosysy', alpha = 0.5)
wipro['returns'].hist(bins = 100, label = 'Wipro', alpha = 0.5)
plt.legend()
plt.show()