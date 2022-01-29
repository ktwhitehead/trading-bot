import os
from twilio.rest import Client

class TwilioClient:
  def __init__(self):
    self.service_id = os.getenv("TWILIO_MESSAGING_SERVICE_ID")
    self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    self.auth_token = os.getenv("TWILIO_API_KEY")
    self.recipient_number = os.getenv("TWILIO_RECIPIENT_NUMBER")

    self.client = Client(self.account_sid, self.auth_token)

  def send_text(self, message):
    print("KEATON SENDING SMS")
    self.client.messages.create(  
      messaging_service_sid=self.service_id,
      body=message,
      to=self.recipient_number
    )

