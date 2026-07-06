import yfinance as yf
import pandas as pd

def get_stock_info(ticker):
    stock=yf.Ticker(ticker)
    info=stock.info
    return {
        "ticker":ticker.upper(),
        "name":info.get("longName","N/A"),
        "current_price":info.get("currentPrice",info.get("regularMarketPrice","N/A")),
        "market_cap":info.get("marketCap","N/A"),
        "pe_ratio":info.get("trailingPE","N/A"),
        "beta":info.get("beta","N/A"),
        "volume":info.get("volume","N/A")
    }

def get_price_history(ticker,period="1y"):
    return yf.Ticker(ticker).history(period=period).reset_index()

def get_option_expirations(ticker):
    return list(yf.Ticker(ticker).options)

def get_option_chain(ticker,expiration):
    c=yf.Ticker(ticker).option_chain(expiration)
    return c.calls,c.puts
