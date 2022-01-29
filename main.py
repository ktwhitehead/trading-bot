import aiohttp
import asyncio
import time
import sys

from Exchanges.SouthXChange import SouthXChange
from Exchanges.TradeOgre import TradeOgre
from TwilioClient import TwilioClient
from dotenv import load_dotenv

MAX_TRANSACT_AMOUNT = 40
MIN_EARNINGS_AMOUNT = 0.0000232
# about $0.037 per share
MIN_EARNINGS_PER_AMOUNT = 0.000001

load_dotenv()

market1 = sys.argv[1]
market2 = sys.argv[2]
print("TRADING " + market1 + "/" + market2)

twilio = TwilioClient()

sx = SouthXChange(market1, market2, twilio)
to = TradeOgre(market1, market2, twilio)
exchanges = [to, sx]

async def make_money(buy_exchange, sell_exchange, calcs, session):
  amount = calcs["amount"]
  transactions = [
    asyncio.ensure_future(buy_exchange["exchange"].buy_the_sell_price(amount, session)),
    asyncio.ensure_future(sell_exchange["exchange"].sell_the_buy_price(amount, session))
  ]
  await asyncio.gather(*transactions)

  # give it a bit for the exchanges to catch up
  time.sleep(0.3)

  update_balances = [
    asyncio.ensure_future(buy_exchange["exchange"].get_balance(session)),
    asyncio.ensure_future(sell_exchange["exchange"].get_balance(session))
  ]
  await asyncio.gather(*update_balances)

  return

def determine_transaction_amount(buy_exchange, sell_exchange):
  print(buy_exchange["exchange"].name + "'s sell price is less than " + sell_exchange["exchange"].name + "'s buy price!")
  print("Sell Price: " + "{:.9f}".format(buy_exchange["current_book_sell_price"]))
  print("Buy Price: " + "{:.9f}".format(sell_exchange["current_book_buy_price"]))

  # Buy the sell on the buy exchange
  buy_amount = buy_exchange["current_book_sell_amount"]
  buy_price = buy_exchange["current_book_sell_price"]

  # Sell the buy on the sell exchange
  sell_amount = sell_exchange["current_book_buy_amount"]
  sell_price = sell_exchange["current_book_buy_price"]

  amount = min(buy_amount, sell_amount, MAX_TRANSACT_AMOUNT)

  print("About to transact...")
  print("Buy Amount: " + str(buy_amount))
  print("Sell Amount: " + str(sell_amount))
  print("Amount to transact: " + str(amount))

  print("Possible estimated earnings...")
  possible_earnings = (sell_price - buy_price) * amount
  print("{:.9f}".format(possible_earnings))

  print("Earnings per amount...")
  earnings_per_amount = possible_earnings / amount
  print("{:.9f}".format(earnings_per_amount))

  if (buy_price * amount) > buy_exchange["exchange"].market2_balance:
    print("OK NOT ENOUGH BALANCE, EXITING")
    twilio.send_text("Keaton, arb bot ran out of balance on " + buy_exchange["exchange"].name)
    sys.exit()

  return { "amount": amount, "possible_earnings": possible_earnings, "earnings_per_amount": earnings_per_amount }

def is_worth_transacting(calcs):
  amount = calcs["amount"]
  possible_earnings = calcs["possible_earnings"]
  earnings_per_amount = calcs["earnings_per_amount"]

  if (amount < 1):
    print("Amount to transact < 1")
    return False

  # if (possible_earnings < MIN_EARNINGS_AMOUNT):
  #   print("Not worth the exchange")
  #   return False

  if (earnings_per_amount < MIN_EARNINGS_PER_AMOUNT):
    print("Not worth the exchange")
    return False

  return True

async def main():
  async with aiohttp.ClientSession() as session:
    book_tasks = []
    for exchange in exchanges:
      book_tasks.append(asyncio.ensure_future(exchange.get_book(session)))

    book_prices = await asyncio.gather(*book_tasks)

    # #TODO: Need to make this work for any number of exchanges
    exc1 = book_prices[0]
    exc2 = book_prices[1]

    if exc1["current_book_sell_price"] < exc2["current_book_buy_price"]:
      calcs = determine_transaction_amount(exc1, exc2)

      if is_worth_transacting(calcs):
        await make_money(exc1, exc2, calcs, session)

    if exc2["current_book_sell_price"] < exc1["current_book_buy_price"]:
      calcs = determine_transaction_amount(exc2, exc1)

      if is_worth_transacting(calcs):
        await make_money(exc2, exc1, calcs, session)

    time.sleep(1.3)

while True:
  asyncio.run(main())
