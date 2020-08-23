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
rh_options_shortlist_json = "./rh_options_shortlist.json"
ObjectStructure_yaml = "./ObjectStructure.yaml"
rh_options_expiration_json = "./options_by_expiration.json"


def authenticate():
    try:

        with open(r'./AccountConfig.yaml') as file:
            config_dict = yaml.full_load(file)
        service = config_dict["service"]
        user = config_dict["user"]
        pwd = keyring.get_password(service, user)
        login = rh.login(user, pwd)
        print("\n")
        print("Login success")
        print(" ~-~-~-~-~-~  ")
    except:
        print("Login failed! ABORT!!")
        print(" ~-~-~-~-~-~-~-~-~  ")
        exit()


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

    Option_Extract_list = []
    Option_Skip_list = []
    # options_ticker_list = ["F", "ZYXW", "MU"] #to be used for testing one file
    df_option_chain = pd.DataFrame()
    options_ticker_list.sort()
    for options_ticker in options_ticker_list:
        try:
            df_option_chain_temp = pd.DataFrame(rh.options.find_options_by_expiration(options_ticker,
                                                                                      expirationDate=expiry_date)
                                                )

            if df_option_chain.empty:
                df_option_chain = df_option_chain_temp
            else:
                df_option_chain = pd.concat([df_option_chain, df_option_chain_temp], ignore_index=True, sort=False)
            Option_Extract_list.append(options_ticker)
            print("Extracted : " + str(options_ticker))
        except:
            Option_Skip_list.append(options_ticker)
            print("Skipped : " + str(options_ticker))

    df_option_chain.to_json(r'./options_by_expiration.json')
    print('Options written to file!')

    print("Extract List : ")
    print(*Option_Extract_list)
    print("Skip List : ")
    print(*Option_Skip_list)


def scan_options(expiry_date="2020-08-21", iv_from=0.01, iv_to=100.0):
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
    main_df["ask_size"] = pd.to_numeric(main_df["ask_size"], downcast="integer")
    main_df["bid_price"] = pd.to_numeric(main_df["bid_price"], downcast="float")
    main_df["bid_size"] = pd.to_numeric(main_df["bid_size"], downcast="integer")

    # Row Filters
    df_option_chain_filtered = main_df.loc[
        (main_df['state'] == "active") &
        (main_df['tradability'] == "tradable") &
        (main_df['expiration_date'] == expiry_date) &
        (main_df['implied_volatility'] >= float(iv_from)) &
        (main_df['implied_volatility'] <= float(iv_to)) &
        (main_df['volume'] > 999) &
        (main_df['open_interest'] > 999) &
        (main_df['bid_size'] > 9) &
        (main_df['ask_size'] > 9) &
        (main_df['bid_price'] > 0.01) &
        (main_df['ask_price'] > 0.01)
        ]

    df_option_chain_view = df_option_chain_filtered[get_option_schema()]
    # df_option_chain_view = main_df[get_option_schema()]

    # rename columns
    df_option_chain_view = df_option_chain_view.rename(
        columns={"chance_of_profit_long": "Buy Profit%", "chance_of_profit_short": "Sell Profit%"})

    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", None)
    pd.options.display.float_format = "{:.2f}".format

    print("*---------------------------------------------*")
    print("|  Options Scan Results for IV : " + str(iv_from) + " - " + str(iv_to) + "  |")
    print("*---------------------------------------------*")

    df_option_chain_sorted = df_option_chain_view.nlargest(100, 'implied_volatility')
    print(df_option_chain_sorted.sort_values(by=['implied_volatility', 'chain_symbol'], ascending=False))
    # print(df_option_chain_view)

    # Shortlist
    with open(rh_options_shortlist_json, 'r') as infile:
        options_ticker_shortlist = json.load(infile)

    df_sp500_plus = pd.DataFrame(options_ticker_shortlist, columns=["chain_symbol"])

    df_short_list_view = df_option_chain_view[df_option_chain_view.chain_symbol.isin(list(df_sp500_plus.chain_symbol))]
    df_short_list_sorted = df_short_list_view.nlargest(100, 'implied_volatility')
    print("\n\n")
    print("*--------------------------------------------------------*")
    print("|  SHORT LIST Options Scan Results for IV : " + str(iv_from) + " - " + str(iv_to) + "  |")
    print("*--------------------------------------------------------*")
    print(df_short_list_sorted.sort_values(by=['implied_volatility', 'chain_symbol'], ascending=False))


def scanner_main():
    authenticate()

    # master_stock_list_refresh()  # Generates RH stock ticker list and saves to rh_stocks json file
    # master_option_list_re#fresh() # Generates RH option ticker list and saves to rh_options json file

    # write_options_to_file(expiry_date='2020-08-28')  # Generates RH option data based on RH options ticker list
    #                                                 # and writes the data to options_by_expiration file

    scan_options(expiry_date='2020-08-28', iv_from=0.4, iv_to=100.0)


if __name__ == "__main__":
    scanner_main()
