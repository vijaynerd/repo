import finance_calculator as fc
import pandas as pd
import datetime

def test(i):

    cashflow_data_hybrid=[]
    #[(Timestamp("2022-01-04 00:00:00"), -30000000), (Timestamp("2023-02-22 00:00:00"), 31647459)]

    cashflow_data_hybrid.append((pd.Timestamp(datetime.date(2022, 1, 4)),-30000000))
    cashflow_data_hybrid.append((pd.Timestamp(datetime.date(2023, 2, 22)),31647459))
    #nc = pd.DataFrame(cashflow_data_hybrid)
    hybrid_xirr = fc.get_xirr(cashflow_data_hybrid)
    fc.get_xirr
    
for i in range(10,31):
    print("day of investment",i)
    str()
    test(i)