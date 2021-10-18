#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import requests
import math
from scipy import stats
import xlsxwriter
from secrets import IEX_CLOUD_API_TOKEN
from statistics import mean


# In[2]:


stocks = pd.read_csv('sp_500_stocks.csv')
stocks


# In[3]:


symbol = "AAPL"
api_url = f"https://sandbox.iexapis.com/stable/stock/{symbol}/stats/?token={IEX_CLOUD_API_TOKEN}"    
data = requests.get(api_url).json()
data


# In[4]:


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
symbol_groups = list(chunks(stocks['Ticker'], 100))
#print(symbol_groups)
symbol_strings = list()
for i in range(0, len(symbol_groups)):
    symbol_strings.append(','.join(symbol_groups[i]))
    print(symbol_strings[i])
    
my_columns = ["Ticker", "Price", "One-Year Price Return", "Number of Shares to Buy"]


# In[5]:


final_dataframe = pd.DataFrame(columns = my_columns)

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=stats,quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(
            pd.Series(
                [
                symbol,
                data[symbol]['quote']['latestPrice'],
                data[symbol]['stats']['year1ChangePercent'],
                'N/A'],
            index = my_columns),
        ignore_index=True)
final_dataframe


# In[6]:


final_dataframe.sort_values("One-Year Price Return", ascending=False, inplace=True)
final_dataframe = final_dataframe[:50]
final_dataframe.reset_index(inplace=True)
final_dataframe


# In[7]:


def portfolio_input():
    global portfolio_size
    portfolio_size = input("Enter the size of your portfolio: ")
    
    try:
        float(portfolio_size)
    except ValueError:
        print("THat is not a number! \nPlease try again: ")
        portfolio_size = input("Enter the size of your portfolio: ")

portfolio_input()


# In[8]:


position_size = float(portfolio_size)/len(final_dataframe.index)
print(position_size)


# In[9]:


for i in range(0, len(final_dataframe)):
    final_dataframe.loc[i, "Number of Shares to Buy"] = math.floor(position_size/final_dataframe.loc[i, "Price"])

final_dataframe


# In[10]:


print("""
Building HQM - high quality momentum - Strategy
1-month price returns
3-month price returns
6-month price returns
1-year price returns
""")


# In[11]:


hqm_columns = [
                'Ticker', 
                'Price', 
                'Number of Shares to Buy', 
                'One-Year Price Return', 
                'One-Year Return Percentile',
                'Six-Month Price Return',
                'Six-Month Return Percentile',
                'Three-Month Price Return',
                'Three-Month Return Percentile',
                'One-Month Price Return',
                'One-Month Return Percentile',
                'HQM Score'
                ]


# In[12]:


hqm_dataframe = pd.DataFrame(columns=hqm_columns)
hqm_dataframe


# In[13]:


for symbol_string in symbol_strings:
   batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=stats,quote&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
   data = requests.get(batch_api_call_url).json()
   for symbol in symbol_string.split(','):
       hqm_dataframe = hqm_dataframe.append(
                                       pd.Series([symbol, 
                                                  data[symbol]['quote']['latestPrice'],
                                                  'N/A',
                                                  data[symbol]['stats']['year1ChangePercent'],
                                                  'N/A',
                                                  data[symbol]['stats']['month6ChangePercent'],
                                                  'N/A',
                                                  data[symbol]['stats']['month3ChangePercent'],
                                                  'N/A',
                                                  data[symbol]['stats']['month1ChangePercent'],
                                                  'N/A',
                                                  'N/A'
                                                  ], 
                                                 index = hqm_columns), 
                                       ignore_index = True)

hqm_dataframe


# In[14]:


time_periods = [
                'One-Year',
                'Six-Month',
                'Three-Month',
                'One-Month'
                ]


# In[15]:


for row in hqm_dataframe.index:
    for time_period in time_periods:
    
        change_col = f'{time_period} Price Return'
        percentile_col = f'{time_period} Return Percentile'
        if hqm_dataframe.loc[row, change_col] == None:
            hqm_dataframe.loc[row, change_col] = 0.0

for row in hqm_dataframe.index:
    for time_period in time_periods:
        hqm_dataframe.loc[row, f'{time_period} Return Percentile'] = stats.percentileofscore(hqm_dataframe[f'{time_period} Price Return'], hqm_dataframe.loc[row, f'{time_period} Price Return']) / 100

# Print each percentile score to make sure it was calculated properly
for time_period in time_periods:
    print(hqm_dataframe[f'{time_period} Return Percentile'])

#Print the entire DataFrame    
hqm_dataframe


# In[16]:


for row in hqm_dataframe.index:
    momentum_percentiles = []
    for time_period in time_periods:
        momentum_percentiles.append(hqm_dataframe.loc[row, f'{time_period} Return Percentile'])
    print(momentum_percentiles)
    hqm_dataframe.loc[row, 'HQM Score'] = mean(momentum_percentiles)
    print(hqm_dataframe.loc[row, 'HQM Score'])


# In[17]:


hqm_dataframe


# In[18]:


hqm_dataframe.sort_values('HQM Score', ascending=False, inplace=True)
hqm_dataframe


# In[19]:


hqm_dataframe = hqm_dataframe[:50]
hqm_dataframe.reset_index(drop=True, inplace=True)
hqm_dataframe


# In[20]:


portfolio_input()


# In[21]:


position_size = float(portfolio_size)/len(hqm_dataframe.index)
for row in hqm_dataframe.index:
    hqm_dataframe.loc[row, 'Number of Shares to Buy'] = math.floor(position_size/hqm_dataframe.loc[row, 'Price'])
    """ 
    or
    hqm_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / hqm_dataframe['Price'][i])
    """
hqm_dataframe


# In[22]:


writer = pd.ExcelWriter('momentum_strategy.xlsx', engine='xlsxwriter')
hqm_dataframe.to_excel(writer, sheet_name='Momentum Strategy', index = False)

background_color = '#0a0a23'
font_color = '#ffffff'

string_template = writer.book.add_format(
        {
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

dollar_template = writer.book.add_format(
        {
            'num_format':'$0.00',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

integer_template = writer.book.add_format(
        {
            'num_format':'0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )

percent_template = writer.book.add_format(
        {
            'num_format':'0.0%',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )


# In[23]:


column_formats = { 
                    'A': ['Ticker', string_template],
                    'B': ['Price', dollar_template],
                    'C': ['Number of Shares to Buy', integer_template],
                    'D': ['One-Year Price Return', percent_template],
                    'E': ['One-Year Return Percentile', percent_template],
                    'F': ['Six-Month Price Return', percent_template],
                    'G': ['Six-Month Return Percentile', percent_template],
                    'H': ['Three-Month Price Return', percent_template],
                    'I': ['Three-Month Return Percentile', percent_template],
                    'J': ['One-Month Price Return', percent_template],
                    'K': ['One-Month Return Percentile', percent_template],
                    'L': ['HQM Score', integer_template]
                    }

for column in column_formats.keys():
    writer.sheets['Momentum Strategy'].set_column(f'{column}:{column}', 20, column_formats[column][1])
    writer.sheets['Momentum Strategy'].write(f'{column}1', column_formats[column][0], string_template)


# In[24]:


writer.save()


# In[ ]:




