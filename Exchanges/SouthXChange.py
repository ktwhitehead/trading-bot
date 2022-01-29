import os
import json
import hmac
import hashlib
import time
import sys

class SouthXChange:
  name = "SouthXChange"

  def __init__(self, market1, market2, twilio):
    self.api_key = os.getenv("SOUTHXCHANGE_API_KEY")
    self.api_secret = bytes(os.getenv("SOUTHXCHANGE_SECRET"), "utf-8")

    self.twilio = twilio

    pair = market1 + "/" + market2
    self.market1 = market1
    self.market2 = market2

    self.base_url = "https://www.southxchange.com/api/v4/"
    self.book_url = "book/" + pair
    self.balance_url = "listBalances/"
    self.order_url = "placeOrder/"

    self.market1_balance = None
    self.market2_balance = None

    self.current_book_buy_price = 0
    self.current_book_buy_amount = 0
    self.current_book_sell_price = 0
    self.current_book_sell_amount = 0
  
  async def get_balance(self, session):
    json_data = {
      "nonce": int(time.time() * 10),
      "key": self.api_key
    }
    hash = hmac.new(
      self.api_secret,
      json.dumps(json_data).encode("utf8"),
      hashlib.sha512
    ).hexdigest()
    headers = {"Hash": hash, "Content-Type": "application/json"}

    print("Getting SouthXChange balance...")
    async with session.post(self.base_url + self.balance_url, json=json_data, headers=headers) as resp:
      wallet = await resp.json()
      self.market1_balance = [b for b in wallet if b["Currency"] == self.market1][0]["Available"]
      self.market2_balance = [b for b in wallet if b["Currency"] == self.market2][0]["Available"]

      print("SouthXChange " + self.market1 + " balance is: " + "{:.9f}".format(self.market1_balance))
      print("SouthXChange " + self.market2 + " balance is: " + "{:.9f}".format(self.market2_balance))

      return

  async def get_book(self, session):
    if self.market1_balance == None or self.market2_balance == None:
      await self.get_balance(session)
      pass

    async with session.get(self.base_url + self.book_url) as resp:
      if resp.status != 200:
        print("SX: da fuk")
        self.twilio.send_text("SX ERROR: " + str(resp.status))
        print(resp)

      book = await resp.json()

      self.current_book_buy_price = float(book["BuyOrders"][0]["Price"])
      self.current_book_buy_amount = float(book["BuyOrders"][0]["Amount"])
      self.current_book_sell_price = float(book["SellOrders"][0]["Price"])
      self.current_book_sell_amount = float(book["SellOrders"][0]["Amount"])

      return {
        "exchange": self,
        "current_book_buy_price": self.current_book_buy_price,
        "current_book_buy_amount": self.current_book_buy_amount,
        "current_book_sell_price": self.current_book_sell_price,
        "current_book_sell_amount": self.current_book_sell_amount
      }

  async def buy_the_sell_price(self, amount, session):
    json_data = {
      "nonce": int(time.time() * 10),
      "key": self.api_key,
      "type": "buy",
      "listingCurrency": self.market1,
      "referenceCurrency": self.market2,
      "amount": amount,
      "limitPrice": self.current_book_sell_price
    }
    hash = hmac.new(
      self.api_secret,
      json.dumps(json_data).encode("utf8"),
      hashlib.sha512
    ).hexdigest()
    headers = {"Hash": hash, "Content-Type": "application/json"}

    async with session.post(self.base_url + self.order_url, json=json_data, headers=headers) as resp:
      result = await resp.json()

      if resp.status != 200:
        print("SX: KEATON FUK")
        print(result)
        self.twilio.send_text("SX ERROR: " + result)
        sys.exit()

      print("SX: SUCCESSFULLY EXECUTED PURCHASE OF THE SELL PRICE!")
      return self

  async def sell_the_buy_price(self, amount, session):
    json_data = {
      "nonce": int(time.time() * 10),
      "key": self.api_key,
      "type": "sell",
      "listingCurrency": self.market1,
      "referenceCurrency": self.market2,
      "amount": amount,
      "limitPrice": self.current_book_buy_price
    }
    hash = hmac.new(
      self.api_secret,
      json.dumps(json_data).encode("utf8"),
      hashlib.sha512
    ).hexdigest()
    headers = {"Hash": hash, "Content-Type": "application/json"}

    async with session.post(self.base_url + self.order_url, json=json_data, headers=headers) as resp:
      result = await resp.json()

      if resp.status != 200:
        print("SX: KEATON FUK")
        print(result)
        self.twilio.send_text("SX ERROR: " + result)
        sys.exit()

      print("SX: SUCCESSFULLY EXECUTED SELL OF THE BUY PRICE!")
      return self
