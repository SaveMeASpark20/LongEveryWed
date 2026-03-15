from hyperliquid.utils import constants
from util import setup, market_close
from dotenv import load_dotenv

load_dotenv()


address, info, exchange, perp_equity = setup(base_url=constants.MAINNET_API_URL, skip_ws=True)


coin = 'BTC'
# sell after 12am tomorrow UTC
print("Closing BTC position (Thursday 00:00 UTC)")

market_close(exchange, coin)
