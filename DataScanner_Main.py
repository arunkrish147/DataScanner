from typing import List, Any, Union

import keyring as keyring
import robin_stocks as rh
import yaml as yaml
import json
import warnings

import pandas as pd
import numpy as np

company_list_csv = "./companylist.csv"
rh_stocks_json = "./rh_stocks.json"
rh_options_json = "./rh_options.json"


def authenticate():
    with open(r'./AccountConfig.yaml') as file:
        config_dict = yaml.full_load(file)
    service = config_dict["service"]
    user = config_dict["user"]
    pwd = keyring.get_password(service, user)
    login = rh.login(user, pwd)
    print("Login success")
    print("**************")


def find_options_by_profitability(ticker="AAPL", profitFloor=0.00, profitCeil=1.00):
    option_query = rh.find_options_by_specific_profitability(ticker, strikePrice="1800", optionType="call",
                                                             typeProfit="chance_of_profit_short", profitFloor=0.8,
                                                             profitCeiling=1.0)
    return pd.DataFrame(option_query)


def print_option_info(df_opt_query=None):
    with open(r'./ObjectStructure.yaml') as file:
        option_search_dict = yaml.full_load(file)
    print_list = option_search_dict['OptionSchema']
    pd.set_option("max_columns", None)
    print(df_opt_query[print_list])
    print(df_opt_query.size)

    # get_fundamentals()
    # get_popularity()
    # get_quotes()
    # get_ratings()
    # get_top_movers()
    # get_top_movers_sp500()
    # find_instrument_data()


# scans company_list csv dump from NASDAQ and generates list of symbols available for trade in Robinhood
def master_stock_list_refresh():
    warnings.filterwarnings("ignore")
    df_tickers = pd.read_csv(company_list_csv)[["Symbol"]]  # double square brackets returns DF instead of Series
    rh_list = rh.stocks.get_instruments_by_symbols(df_tickers["Symbol"].tolist(), info='symbol')

    with open(rh_stocks_json, 'w') as outfile:
        json.dump(rh_list, outfile)
    print("RH Ticker List updated!")


def master_option_list_refresh():
    with open(rh_stocks_json, 'r') as infile:
        stock_tickers_list = json.load(infile)

    # stock_tickers_list = ['AAPL', 'INPX']
    option_tickers_list = []
    for ti in stock_tickers_list:
        try:
            lis = rh.options.find_options_by_expiration(ti, "2020-08-15")
            option_tickers_list.append(str(ti))

        except:
            print("Passing : " + str(ti))

    with open(rh_options_json, 'w') as outfile:
        json.dump(option_tickers_list, outfile)

    print("RH Options List updated!")


def scan_options(expiry_date, iv):
    with open(rh_options_json, 'r') as infile:
        options_ticker_list = json.load(infile)

    options_ticker_list = ['AAPL', 'TSLA']
    for ti in options_ticker_list:
        try:
            option_chain = rh.options.find_options_by_expiration(ti,expirationDate=expiry_date)


def scanner_main():
    authenticate()

    # master_stock_list_refresh()  # Generates RH stock ticker list and saves to rh_stocks json file
    # master_option_list_refresh() # Generates RH option ticker list and saves to rh_options json file

    scan_options(expiry='20200821', iv=0.6)


if __name__ == "__main__":
    scanner_main()
