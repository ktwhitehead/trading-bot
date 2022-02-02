import psycopg
import os

class DBClient:
  def __init__(self):
    self.conn_string = os.getenv("DATABASE_CONNECTION")

  def insert_trade(self, values):
    with psycopg.connect(self.conn_string) as conn:
      conn.execute("insert into trades (pair, amount, buy_exchange, sell_exchange, buy_price, sell_price) values (%s, %s, %s, %s, %s, %s)", values)
      conn.commit()


