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


def getLatestPrice(ticker): # Get the latest stock price
    return web.get_quote_yahoo('{}'.format(ticker))['last'][0]

def getReturns(predicted_prices): # Calculate the projected return of each stock in predicted_prices
    Projected_Returns = {}
    for stock in predicted_prices:
        current_price = getLatestPrice(stock)
        future_price = predicted_prices[stock]
        Projected_Returns[stock] = (future_price - current_price)/current_price
    with open('ProjectedReturns.json', 'w') as saveFile:
        json.dump(Projected_Returns, saveFile)
    return Projected_Returns


try:
    with open('ProjectedReturns.json', 'r') as json_ProjectedReturns:
        Projected_Returns = json.load(json_ProjectedReturns)
    print('Projected Returns successfully loaded')
except:
    print('Creating dictionary of Projected Returns...')
    try:
        Projected_Returns = getReturns(Predicted_Prices)
        print('Projected Returns dictionary successfully created')
    except:
        print('Failed to create Projected Returns dictionary')


def filterByReturn(low, high): # Selects and sorts stocks with projected returns between low and high
    stocks = [s for s in Projected_Returns if Projected_Returns[s] > low and Projected_Returns[s] < high]
    return sorted(stocks, key=lambda x: Projected_Returns[x])

def displayBuyCandidates(low, high): # Displays predicted return, price, and EPS of filtered buy candidates
    stocks = filterByReturn(low, high)
    d = {}
    d['Return'] = [Projected_Returns[s] for s in stocks]
    d['Price'] = [Predicted_Prices[s] for s in stocks]
    d['EPS'] = [Earnings_Estimates[s] for s in stocks]
    result = pd.DataFrame(d, index=stocks)
    with pd.option_context('display.max_rows', None):
        print(result)
