from typing import List, Any, Union

import keyring as keyring
import robin_stocks as rh
import yaml as yaml


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
    return option_query


def print_option_info(opt_list=None):
    with open(r'./ObjectStructure.yaml') as file:
        option_search_dict = yaml.full_load(file)
    print_list = option_search_dict['OptionSearch']
    for dict_entry in opt_list:
        str_dict_entry = ""
        for li in print_list:
            str_dict_entry = str_dict_entry + " " + li + " : " + str(dict_entry[li])
        #            #print(li, " : ", dict_entry[li])
        print(str_dict_entry)
        print("")


def scanner_main():
    authenticate()

    #    #returns list of dictionaries [{},{},...]
    option_query_list = find_options_by_profitability("TSLA")
    print_option_info(option_query_list)


if __name__ == "__main__":
    scanner_main()
