import os
import json
import hmac
import hashlib
import time
import sys
import collections

class CoinEx:
  name = "CoinEx"

  def __init__(self, market1, market2, twilio):
    self.api_key = os.getenv("COINEX_API_KEY")
    self.api_secret = os.getenv("COINEX_API_SECRET")

    self.twilio = twilio

    self.pair = market1 + market2
    self.market1 = market1
    self.market2 = market2

    self.base_url = "https://api.coinex.com/v1/"
    self.book_url = "market/ticker"
    self.balance_url = "balance/info"
    self.order_url = "order/limit"

    self.market1_balance = None
    self.market2_balance = None

    self.current_book_buy_price = 0
    self.current_book_buy_amount = 0
    self.current_book_sell_price = 0
    self.current_book_sell_amount = 0
  
  async def get_balance(self, session):
    tonce = int(time.time()*1000)
    json_data = {
      "access_id": self.api_key,
      "tonce": tonce
    }
    auth = "access_id=" + str(self.api_key) + "&tonce=" + str(tonce) + "&secret_key=" + str(self.api_secret)
    hash = hashlib.md5(auth.encode()).hexdigest().upper()
    headers = {
      "Authorization": hash,
      "Content-Type": "application/json; charset=utf-8",
      "Accept": "application/json",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36"
    }

    print("Getting CoinEx balance..." + self.base_url + self.balance_url)
    async with session.get(self.base_url + self.balance_url, json=json_data, headers=headers) as resp:
      wallet = await resp.json()
      self.market1_balance = float(wallet["data"][self.market1]["available"])
      self.market2_balance = float(wallet["data"][self.market2]["available"])

      print("CoinEx " + self.market1 + " balance is: " + "{:.9f}".format(self.market1_balance))
      print("CoinEx " + self.market2 + " balance is: " + "{:.9f}".format(self.market2_balance))

      return

  async def get_book(self, session):
    if self.market1_balance == None or self.market2_balance == None:
      await self.get_balance(session)
      pass

    headers = {
      "Content-Type": "application/json; charset=utf-8",
      "Accept": "application/json",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36"
    }
    async with session.get(self.base_url + self.book_url, params={ "market": self.pair }, headers=headers) as resp:
      if resp.status != 200:
        print("CoinEx: da fuk")
        self.twilio.send_text("CoinEx ERROR: " + str(resp.status))
        print(resp)

      book = await resp.json()

      self.current_book_buy_price = float(book["data"]["ticker"]["buy"])
      self.current_book_buy_amount = float(book["data"]["ticker"]["buy_amount"])
      self.current_book_sell_price = float(book["data"]["ticker"]["sell"])
      self.current_book_sell_amount = float(book["data"]["ticker"]["sell_amount"])

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
