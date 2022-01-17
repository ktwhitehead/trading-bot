import os
import json
import hmac
import hashlib
import time
import sys

class SouthXChange:
  name = "SouthXChange"

  def __init__(self, pair):
    self.api_key = os.getenv("SOUTHXCHANGE_API_KEY")
    self.api_secret = bytes(os.getenv("SOUTHXCHANGE_SECRET"), "utf-8")

    self.base_url = "https://www.southxchange.com/api/v4/"
    self.book_url = "book/" + pair
    self.balance_url = "listBalances/"
    self.order_url = "placeOrder/"

    #TODO: Should be pair1 and pair2, not just btc/scp
    self.btc_balance = None
    self.scp_balance = None

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
      self.btc_balance = [b for b in wallet if b["Currency"] == "BTC"][0]["Available"]
      self.scp_balance = [b for b in wallet if b["Currency"] == "SCP"][0]["Available"]

      print("SouthXChange BTC balance is: " + str(self.btc_balance))
      print("SouthXChange SCP balance is: " + str(self.scp_balance))

      return

  async def get_book(self, session):
    if self.btc_balance == None or self.scp_balance == None:
      await self.get_balance(session)
      pass

    async with session.get(self.base_url + self.book_url) as resp:
      book = await resp.json()
      # current_book_buy_price = "{:.9f}".format(book["BuyOrders"][0]["Price"])

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
      "listingCurrency": "SCP",
      "referenceCurrency": "BTC",
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
        sys.exit()

      print("SX: SUCCESSFULLY EXECUTED PURCHASE OF THE SELL PRICE!")
      return self

  async def sell_the_buy_price(self, amount, session):
    json_data = {
      "nonce": int(time.time() * 10),
      "key": self.api_key,
      "type": "sell",
      "listingCurrency": "SCP",
      "referenceCurrency": "BTC",
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
        sys.exit()

      print("SX: SUCCESSFULLY EXECUTED SELL OF THE BUY PRICE!")
      return self
