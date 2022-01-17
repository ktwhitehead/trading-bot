import aiohttp
import asyncio
import time

from Exchanges.SouthXChange import SouthXChange
from Exchanges.TradeOgre import TradeOgre
from dotenv import load_dotenv

load_dotenv()

#TODO: pair should be runtime argument
pair = "SCP/BTC"

sx = SouthXChange(pair)
to = TradeOgre(pair)

exchanges = [to, sx]

async def make_money(ex1, ex2, amount, session):
  transactions = [
    asyncio.ensure_future(ex1["exchange"].buy_the_sell_price(amount, session)),
    asyncio.ensure_future(ex2["exchange"].sell_the_buy_price(amount, session))
  ]
  result = await asyncio.gather(*transactions)

  return result

async def main():
  async with aiohttp.ClientSession() as session:
    book_tasks = []
    for exchange in exchanges:
      book_tasks.append(asyncio.ensure_future(exchange.get_book(session)))

    book_prices = await asyncio.gather(*book_tasks)

    # #TODO: Need to make this work for any number of exchanges
    exc1 = book_prices[0]
    exc2 = book_prices[1]

    #exc1 should = TO
    #exc2 should be SX
    if exc1["current_book_sell_price"] < exc2["current_book_buy_price"]:
      print("------------------------------------------------------------------------ 1")
      print(exc1["exchange"].name + "'s sell price is less than " + exc2["exchange"].name + "'s buy price!")
      print("Sell Price: " + str(exc1["current_book_sell_price"]))
      print("Buy Price: " + str(exc2["current_book_buy_price"]))

      #TODO: validate balances before making purchase
      buy_amount = exc1["current_book_buy_amount"]
      sell_amount = exc2["current_book_sell_amount"]
      amount = min(buy_amount, sell_amount)
      
      print("Buy Amount: " + str(buy_amount))
      print("Sell Amount: " + str(sell_amount))
      print("Amount to transact: " + str(amount))
      await make_money(exc1, exc2, amount, session)

    if exc2["current_book_sell_price"] < exc1["current_book_buy_price"]:
      print("------------------------------------------------------------------------ 2")
      print(exc2["exchange"].name + "'s sell price is less than " + exc1["exchange"].name + "'s buy price!")
      print("Sell Price: " + str(exc2["current_book_sell_price"]))
      print("Buy Price: " + str(exc1["current_book_buy_price"]))

      # validate balances before making purchase
      buy_amount = exc2["current_book_buy_amount"]
      sell_amount = exc1["current_book_sell_amount"]
      amount = min(buy_amount, sell_amount)
      
      print("Buy Amount: " + str(buy_amount))
      print("Sell Amount: " + str(sell_amount))
      print("Amount to transact: " + str(amount))
      await make_money(exc2, exc1, amount, session)

    time.sleep(2)

while True:
  asyncio.run(main())
