import os 
import hl
import strategy
from settings import params
from typing import List
from datetime import datetime, timezone
from dotenv import load_dotenv
import asyncio
import websockets
import json
import math

load_dotenv()

# last_price = None

def dl_prices_ts(coin: str, interval: str) -> List[tuple[int, str]]:
    """
    Download the price data for a trading pair

    Fetch candlestick data from the exchange API
    and converts it to a simple list of timestamp, price

    """

    candles = hl.dl_last_candles(coin, interval)
    
    #t = timestamp
    #c = closing

    prices = [(candle['t'], candle['c']) for candle in candles]
     
    return prices


def create_strategy(exchange) -> strategy.BasicTakerStrat:
    """
    1. extracts config from global params
    2. Creates the prediction model
    3. Initializes the lag calculator
    4. Download historical price data
    5. Warms up the lag calculator with historical data
    6. Constructs the complete strategy instances
    """

    coin = params['sym']
    # interval = params['interval']

    trade_sz = 0.0002

    # prices = dl_prices_ts(coin, interval)
    # for _, price in prices:
    #     lag.on_tick(float(price))

    return strategy.BasicTakerStrat(exchange, coin)


async def trade_periodically(strat) -> None:
    print("trade periodically")

    """
    Async task that continously  and executes trades, it gets the time and waiting time for execution

    ---comment out ---
    Timing example for '1h' interval:
    - Current time: 10:37:45
    - Next execution: 11:00:00
    - Wait time: 22 minutes, 15 seconds
    """

    global last_price
    try :
        # no_mins = interval_mins(interval)
        # period_mins = max(1, no_mins)
        # print('after period mins')
        # while True:

        #     #Calculate how many minutes has pass  since the last interval boundary
        #     print('while')
        #     now = datetime.now(timezone.utc)
        #     mins_past = now.minute  % period_mins

        #     #Calculate until the next interval boundary in seconds
        #     # Formula: (remaining minutes in period * 60) - current seconds - micorseconds
        #     seconds_until_next = (
        #             (period_mins - mins_past) * 60 
        #             - (now.second) 
        #             - (now.microsecond / 1_000_000.0)
        #     )
        #     seconds_until_next = max(0, seconds_until_next)
        #     print(seconds_until_next)

        #     #with tiny buffer
        #     await asyncio.sleep(seconds_until_next + 0.0001)

            execution_time = datetime.now(timezone.utc)
            if last_price is not None:
                tick = strat.on_tick(last_price)
                if tick:
                    print(f"--- [Sync Every 12:00:00] {execution_time.strftime('%H:%M:%S')} |"
                    f"Price: {last_price}")
            else:
                #No price data available yet
                print(
                    f"--- [Sync Every 12:00:00] {execution_time.strftime('%H:%M:%S')} | "
                    f"Price {last_price} ---"
                )
    
    except Exception as e:
        print("❌ trade_periodically crashed:", e)
        raise

async def connect_and_listen(strat) -> None:
    """
    Connect to Websocket feed and listen for real-time price updates
    Async create_task periodically for getting the time of waiting to execute
    """

    global last_price

    timer_task = asyncio.create_task(trade_periodically(strat))
    try:
        # Connect to WebSocket with keepalive ping
        async with websockets.connect(hl.URL, ping_interval=20) as ws:
            print(f"Connected to {strat.coin} stream")

            #subscribe to trade updates for the specified coin
            await ws.send(json.dumps({
                "method": "subscribe",
                "subscription": {"type": "trades", "coin": strat.coin}
            }))        

            async for message in ws:
                data = json.loads(message)
                trade_data = data.get("data")

                if isinstance(trade_data, list):
                    last_trade = trade_data[-1]
                    last_price = float(last_trade['px'])
                    # Price is stored; periodic task will use it for trading

    finally:
        #Clean up: cancel the periodic trading task when Websocket disconnects
        #This prevents multiple timer tasks for accumulating on reconnects
        timer_task.cancel()

def get_last_price(coin: str, interval: str = "1m") -> float:
    """
    Get the most recent market price of a coin.
    """
    candles = hl.dl_last_candles(coin, interval)
    if not candles:
        raise Exception("No candle data returned")
    # Use the closing price of the last candle
    return float(candles[-1]['c'])

def truncate(value, decimals):
    factor = 10 ** decimals
    return math.floor(value * factor) / factor

async def trade_now(strat, info, address ) -> None:
    """
    Executes a trade using the provided strategy and account info.

    Args:
        strat: Your BasicTakerStrat instance
        info: Hyperliquid Info client returned from hl.init()
    """
    
    candles = hl.dl_last_candles(strat.coin, '1m')
    if not candles:
        print("No price data available")
        return
    last_price = float(candles[-1]["c"])

    user_state = info.user_state(address)

    available_usd = float(user_state["marginSummary"]["totalRawUsd"]) \
              - float(user_state["marginSummary"]["totalMarginUsed"])

    pct_to_use = 0.8
    funds_to_trade =available_usd * pct_to_use

    raw_qty = funds_to_trade / last_price
    qty = truncate(raw_qty, 3)
    print("qty", qty)

    order = strat.strategy(1.0, qty)
    print(f"Trading {qty:.6f} {strat.coin} for ${funds_to_trade:.2f}")

    strat.execute(order)


        

async def main() -> None:
    """
    Main application entry point.

    This function:
    1. Loads credentials from environment variables 
    2. Initialize the exchange connection
    """

    secret_key = os.environ["HL_SECRET"]
    wallet = os.environ["HL_WALLET"]

    backoff = 1
    # interval = params['interval']
    
    address, info, exchange = hl.init(secret_key, wallet)
    print(info)

    strat = create_strategy(exchange)
    # if interval not in hl.TIME_INTERVALS:
    #     raise Exception(f"Invalid time interval: {interval}")

    #Connection loop auto reconnect, also trading happening
    
    # while True:
    #     try:
    #         #connect and listening and trading
    #         await connect_and_listen(strat)
    #         backoff = 1 # Reset backoff on clen exit
    #     except (websockets.ConnectionClosed, OSError) as e:
    #         print(f"Disconnected: {e}. Reconnection in {backoff}s...") 
    #         await asyncio.sleep(backoff)

    #         backoff = min(backoff * 2, 30) # Cap at 30 seconds

    
    await trade_now(strat, info, address)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGracefully shutting down...")
