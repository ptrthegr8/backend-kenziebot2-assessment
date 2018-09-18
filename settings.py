from dotenv import load_dotenv
import os

load_dotenv("./.env")
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
BOT_ID = os.getenv('BOT_ID')
