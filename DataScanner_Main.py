import keyring as keyring
import robin_stocks as rh


def authenticate():
    service = "Robinhood"
    user = "arunkrish147@gmail.com"
    pwd = keyring.get_password(service, user)
    login = rh.login(user, pwd)
    print("Login success")
    print("**************")


def scanner_main():
    authenticate()

    for li in rh.find_options_by_specific_profitability("TSLA", strikePrice="1800", optionType="call",
                                                        typeProfit="chance_of_profit_short", profitFloor=0.8,
                                                        profitCeiling=1):
        print(li)


if __name__ == "__main__":
    scanner_main()
