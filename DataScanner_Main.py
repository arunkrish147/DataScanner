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
ObjectStructure_yaml = "./ObjectStructure.yaml"
rh_options_expiration_json = "./options_by_expiration.json"


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


def get_option_schema(df_opt_query=None):
    with open(ObjectStructure_yaml, 'r') as file:
        option_search_dict = yaml.full_load(file)
    return option_search_dict['OptionSchema']  # returns list

    # pd.set_option("max_columns", None)
    # print(df_opt_query[print_list])
    # print(df_opt_query.size)

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


def write_options_to_file(expiry_date):
    with open(rh_options_json, 'r') as infile:
        options_ticker_list = json.load(infile)

    df_option_chain = pd.DataFrame(rh.options.find_options_by_expiration(options_ticker_list,
                                                                         expirationDate=expiry_date)
                                   )
    df_option_chain.to_json(r'./options_by_expiration.json')
    print('Options written to file!')


def scan_options(expiry_date, iv):
    with open('./options_by_expiration.json', 'r') as infile:
        dic_test = json.load(infile)

    main_df = pd.DataFrame()
    for key, value in dic_test.items():
        df_temp = pd.DataFrame(value.values(), columns=[key])
        main_df = pd.concat([main_df, df_temp], axis=1).reindex(df_temp.index)

    # typecasting

    main_df["volume"] = pd.to_numeric(main_df["volume"], downcast="integer")
    main_df["open_interest"] = pd.to_numeric(main_df["open_interest"], downcast="integer")

    main_df["strike_price"] = pd.to_numeric(main_df["strike_price"], downcast="float")
    main_df["chance_of_profit_long"] = pd.to_numeric(main_df["chance_of_profit_long"], downcast="float")
    main_df["chance_of_profit_short"] = pd.to_numeric(main_df["chance_of_profit_short"], downcast="float")
    main_df["implied_volatility"] = pd.to_numeric(main_df["implied_volatility"], downcast="float")
    main_df["delta"] = pd.to_numeric(main_df["delta"], downcast="float")
    main_df["theta"] = pd.to_numeric(main_df["theta"], downcast="float")

    main_df["ask_price"] = pd.to_numeric(main_df["ask_price"], downcast="float")
    main_df["ask_size"] = pd.to_numeric(main_df["ask_size"], downcast="float")
    main_df["bid_price"] = pd.to_numeric(main_df["bid_price"], downcast="float")
    main_df["bid_size"] = pd.to_numeric(main_df["bid_size"], downcast="float")

    # Row Filters
    df_option_chain_filtered = main_df.loc[
        (main_df['state'] == "active") &
        (main_df['tradability'] == "tradable") &
        (main_df['expiration_date'] == expiry_date) &
        (main_df['implied_volatility'] >= float(iv)) &
        (main_df['volume'] > 999) &
        (main_df['bid_size'] > 9) &
        (main_df['ask_size'] > 9)
        ]

    df_option_chain_view = df_option_chain_filtered[get_option_schema()]

    # rename columns
    df_option_chain_view = df_option_chain_view.rename(
        columns={"chance_of_profit_long": "Call Profit%", "chance_of_profit_short": "Put Profit%",
                 "implied_volatility": "IV"})

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", None)
    pd.options.display.float_format = "{:.2f}".format

    print(" ")
    print(" OPTIONS SCAN RESULTS")
    print("---------------------")

    print(df_option_chain_view.nlargest(100, 'IV'))


def scanner_main():
    # authenticate()

    # master_stock_list_refresh()  # Generates RH stock ticker list and saves to rh_stocks json file
    # master_option_list_refresh() # Generates RH option ticker list and saves to rh_options json file

    # write_options_to_file(expiry_date='2020-08-21')   # Generates RH option data based on RH options ticker list
    #                                                   # and writes the data to options_by_expiration file

    scan_options(expiry_date='2020-08-21', iv=0.7)


if __name__ == "__main__":
    scanner_main()
