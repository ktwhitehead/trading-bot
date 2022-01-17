import os
import aiohttp
import sys

PAIR_MAP = {
  "SCP/BTC": "BTC-SCP"
}

class TradeOgre:
  name = "TradeOgre"

  def __init__(self, pair):
    self.api_key = os.getenv("TRADEOGRE_API_KEY")
    self.api_secret = os.getenv("TRADEOGRE_API_SECRET")

    self.base_url = "https://tradeogre.com/api/v1/"
    self.book_url = "orders/" + PAIR_MAP[pair]
    self.balance_url = "account/balances"
    self.sell_url = "order/sell"
    self.buy_url = "order/buy"

    self.btc_balance = None
    self.scp_balance = None

    self.current_book_buy_price = 0
    self.current_book_buy_amount = 0
    self.current_book_sell_price = 0
    self.current_book_sell_amount = 0

  async def get_balance(self, session):
    print("Getting TradeOgre balance...")
    basic = aiohttp.BasicAuth(self.api_key, self.api_secret, encoding="utf-8")
    async with session.get(self.base_url + self.balance_url, auth=basic) as resp:
      wallet = await resp.json(content_type="text/html")
      self.btc_balance = wallet["balances"]["BTC"]
      self.scp_balance = wallet["balances"]["SCP"]

      print("TradeOgre BTC balance is: " + str(self.btc_balance))
      print("TradeOgre SCP balance is: " + str(self.scp_balance))
      return

  async def get_book(self, session):
    if self.btc_balance == None or self.scp_balance == None:
      await self.get_balance(session)
      pass

    async with session.get(self.base_url + self.book_url) as resp:
      book = await resp.json(content_type="text/html")
      self.current_book_buy_price = float(list(book["buy"].items())[-1][0])
      self.current_book_buy_amount = float(list(book["buy"].items())[-1][1])
      self.current_book_sell_price = float(list(book["sell"].items())[0][0])
      self.current_book_sell_amount = float(list(book["sell"].items())[0][1])

      return {
        "exchange": self,
        "current_book_buy_price": self.current_book_buy_price,
        "current_book_buy_amount": self.current_book_buy_amount,
        "current_book_sell_price": self.current_book_sell_price,
        "current_book_sell_amount": self.current_book_sell_amount
      }

  async def buy_the_sell_price(self, amount, session):
    basic = aiohttp.BasicAuth(self.api_key, self.api_secret, encoding="utf-8")
    data = {
      "market": (None, "BTC-SCP"),
      "quantity": (None, str(amount)),
      "price": (None, str("{:.9f}".format(self.current_book_sell_price))),
    }

    async with session.post(self.base_url + self.buy_url, data=data, auth=basic) as resp:
      result = await resp.json(content_type="text/html")

      if result["success"] == False:
        print("KEATON FUUUUUUUK IDK, error is...")
        print(result["error"])
        sys.exit()

      if resp.status != 200:
        print("TO: KEATON FUK")
        print(result)
        sys.exit()

      print("TO: SUCCESSFULLY EXECUTED PURCHASE OF THE SELL PRICE!")
      return self

  async def sell_the_buy_price(self, amount, session):
    basic = aiohttp.BasicAuth(self.api_key, self.api_secret, encoding="utf-8")
    data = {
      "market": (None, "BTC-SCP"),
      "quantity": (None, str(amount)),
      "price": (None, str("{:.9f}".format(self.current_book_buy_price)))
    }
    async with session.post(self.base_url + self.sell_url, data=data, auth=basic) as resp:
      result = await resp.json(content_type="text/html")

      if result['success'] == False:
        print("KEATON FUUUUUUUK IDK, error is...")
        print(result["error"])
        sys.exit()

      if resp.status != 200:
        print("TO: KEATON FUK")
        print(result)
        sys.exit()

      print("TO: SUCCESSFULLY EXECUTED SELL OF THE BUY PRICE!")
      return self