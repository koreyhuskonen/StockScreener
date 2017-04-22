import quandl
import json
import pandas as pd
import pandas_datareader as pdr
import pandas_datareader.data as web

quandl.ApiConfig.api_key = ''

try:
    with open('sf0-tickers.json', 'r') as json_tickers:
        parsed_tickers = json.load(json_tickers) # parsed_tickers is a Python dictionary containing unnecessary stock data

    tickers = [] # Collect just the stock tickers
    for stock in parsed_tickers:
        tickers.append(stock['Ticker'])
    print('Stock tickers sucessfully loaded')
except:
    print('Failed to load stock tickers')


def getEPS(ticker): # EPS = earnings per share, returns a DataFrame with percent changes in annual EPS of an individual stock
    return quandl.get('SF0/{}_EPSUSD_MRY'.format(ticker)).tail(5) # Only take last 5 years

def getEarningsFromDF(eps_df):
    return eps_df['Value'].tolist()

def getAvgEPSChange(eps_df):
    eps_list = getEarningsFromDF(eps_df)
    total = 0;
    num_entries = len(eps_list)
    for i in range(1, num_entries):
        total += (eps_list[i] - eps_list[i-1])/eps_list[i-1];
    return total/(num_entries-1)

def checkStableGrowth(eps_df): # Takes a stock DataFrame as an input
    eps_list = eps_df['Value'].tolist()
    for yearly_eps in eps_list:
        if yearly_eps <= 0: # Check whether the company has lost money recently
            return False
    for i in range(1,len(eps_list)):
        percent_change = (eps_list[i] - eps_list[i-1])/eps_list[i-1]
        if percent_change <= 0: # Check whether earnings have decreased or remained flat recently
            return False
    return True

def filterGrowthProspects(growth_prospects):
    return {stock: growth_prospects[stock] for stock in growth_prospects if growth_prospects[stock] > 0}

def findGrowthProspects(): # Filters stocks and then links ticker symbols with average change in annual EPS
    Growth_Prospects = {}
    for t in tickers:
        eps_data = getEPS(t) # eps_data is now a DataFrame containing annual EPS
        if checkStableGrowth(eps_data):
            Growth_Prospects[t] = getAvgEPSChange(eps_data) # Link stock tickers with average change in annual EPS
    Growth_Prospects = filterGrowthProspects(Growth_Prospects)
    with open('GrowthProspects.json', 'w') as saveFile:
        json.dump(Growth_Prospects, saveFile)
    return Growth_Prospects


try:
    with open('GrowthProspects.json', 'r') as json_GrowthProspects:
        Growth_Prospects = json.load(json_GrowthProspects)
    print('Growth Prospects successfully loaded')
except:
    print('Creating dictionary of Growth Prospects...')
    try:
        Growth_Prospects = findGrowthProspects()
        print('Growth Prospects dictionary successfully created')
    except:
        print('Failed to create Growth Prospects dictionary')


def getDateFromTimestamp(timestamp):
    return str(timestamp)[:7]

def getDatesFromDF(dataframe):
    return [getDateFromTimestamp(i) for i in dataframe.index]

def getHistoricalPrices(ticker):
    try:
        return pdr.get_data_yahoo('{}'.format(ticker))['Adj Close'] # Returns data series of stock prices
    except:
        return pdr.get_data_yahoo('{}'.format(ticker[:-1] + '-' + ticker[-1]))['Adj Close']

def getPricesForDates(historical_prices, dates): # Get average stock prices for the months in dates
    average_prices = []
    for date in dates:
        try:
            average_prices.append(historical_prices[date].mean())
        except:
            average_prices.append(0)
    return average_prices

def findAvgPE(ticker):
    eps_data = getEPS(ticker)
    earnings = getEarningsFromDF(eps_data) # List of yearly EPS
    dates = getDatesFromDF(eps_data)
    historical_prices = getHistoricalPrices(ticker)
    prices = getPricesForDates(historical_prices, dates) # List of monthly price averages
    valid_data_points = [p for p in prices if p != 0] # Find how many valid price entries we have
    return sum([prices[i]/earnings[i] for i in range(len(earnings))])/len(valid_data_points)

def getLastEPS(ticker):
    return getEPS(ticker)['Value'][-1]

def getForwardEarnings(growth_prospects): # Predict EPS in 5 years, needs dictionary with average EPS change
    Earnings_Estimates = {}
    for stock in growth_prospects:
        avgEPSChange = growth_prospects[stock]
        Earnings_Estimates[stock] = (avgEPSChange+1)**5 * getLastEPS(stock)
    with open('EarningsEstimates.json', 'w') as saveFile:
        json.dump(Earnings_Estimates, saveFile)
    return Earnings_Estimates


try:
    with open('EarningsEstimates.json', 'r') as json_EarningsEstimates:
        Earnings_Estimates = json.load(json_EarningsEstimates)
    print('Earnings Estimates successfully loaded')
except:
    print('Creating dictionary of Earnings Estimates...')
    try:
        Earnings_Estimates = getForwardEarnings(Growth_Prospects)
        print('Earnings Estimates dictionary successfully created')
    except:
        print('Failed to create Earnings Estimates dictionary')


def predictPrices(earnings_estimates):
    Predicted_Prices = {}
    for stock in earnings_estimates:
        try:
            forwardEPS = earnings_estimates[stock]
            Predicted_Prices[stock] = findAvgPE(stock) * forwardEPS
        except:
            pass
    with open('PredictedPrices.json', 'w') as saveFile:
        json.dump(Predicted_Prices, saveFile)
    return Predicted_Prices


try:
    with open('PredictedPrices.json', 'r') as json_PredictedPrices:
        Predicted_Prices = json.load(json_PredictedPrices)
    print('Predicted Prices successfully loaded')
except:
    print('Creating dictionary of Predicted Prices...')
    try:
        Predicted_Prices = predictPrices(Earnings_Estimates)
        print('Predicted Prices dictionary successfully created')
    except:
        print('Failed to create Predicted Prices dictionary')


def getLatestPrice(ticker):
    return web.get_quote_yahoo('{}'.format(ticker))['last'][0]




# from time import sleep
# import sys
#
# for i in range(21):
#     sys.stdout.write('\r')
#     # the exact output you're looking for:
#     sys.stdout.write("[%-20s] %d%%" % ('='*i, 5*i))
#     sys.stdout.flush()
#     sleep(0.25)
