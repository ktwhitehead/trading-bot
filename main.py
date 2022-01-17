import aiohttp
import asyncio
import time
import sys

from Exchanges.SouthXChange import SouthXChange
from Exchanges.TradeOgre import TradeOgre
from dotenv import load_dotenv

load_dotenv()

market1 = sys.argv[1]
market2 = sys.argv[2]

print("TRADING " + market1 + "/" + market2)

sx = SouthXChange(market1, market2)
to = TradeOgre(market1, market2)

exchanges = [to, sx]

async def make_money(buy_exchange, sell_exchange, amount, session):
  transactions = [
    asyncio.ensure_future(buy_exchange["exchange"].buy_the_sell_price(amount, session)),
    asyncio.ensure_future(sell_exchange["exchange"].sell_the_buy_price(amount, session))
  ]
  await asyncio.gather(*transactions)

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

  sell_price = sell_exchange["current_book_buy_price"]

  buy_amount = buy_exchange["current_book_buy_amount"]
  buy_price = buy_exchange["current_book_buy_price"]
  sell_amount = sell_exchange["current_book_sell_amount"]
  amount = min(buy_amount, sell_amount, 10)

  print("Buy Amount: " + str(buy_amount))
  print("Sell Amount: " + str(sell_amount))
  print("Amount to transact: " + str(amount))

  print("Possible estimated earnings...")
  print("{:.9f}".format((sell_price - buy_price) * min(buy_amount, sell_amount)))

  if (buy_price * amount) > buy_exchange["exchange"].btc_balance:
    print("OK NOT ENOUGH BALANCE, EXITING")
    sys.exit()

  return amount

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

      amount = determine_transaction_amount(exc1, exc2)

      if (amount < 1):
        print("Amount to transact < 1")
        return

      await make_money(exc1, exc2, amount, session)

    if exc2["current_book_sell_price"] < exc1["current_book_buy_price"]:
      amount = determine_transaction_amount(exc2, exc1)

      if (amount < 1):
        print("Amount to transact < 1")
        return

      await make_money(exc2, exc1, amount, session)

    time.sleep(1)

while True:
  asyncio.run(main())
