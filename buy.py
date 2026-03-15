from hyperliquid.utils import constants
from util import setup, market_order, isAvailToBuy, decimalPrecision
from dotenv import load_dotenv

load_dotenv()

address, info, exchange, perp_equity = setup(base_url=constants.MAINNET_API_URL, skip_ws=True)


coin = 'BTC'

# get the capital of how much we can spend, 
# if capital < 12 dollars we dont trade since we don't have much money to buy BITCOIN

MIN_BUY_BTC = 12.0
max_decimal = 5
capital_percent = .9
isAvailToBuy(perp_equity, MIN_BUY_BTC)
if(isAvailToBuy):
     # changing leverage
    capital_to_buy = perp_equity * capital_percent
    
    sizeToBuy = decimalPrecision(max_decimal, perp_equity * capital_percent) 
    leverage = 3
    print(exchange.update_leverage(leverage, coin))

    signal = True #Long Every Wednesday
    print("We Long Every Wed 12am UTC")
    market_order(exchange, coin, signal, sizeToBuy)
    print("Trade Executed")