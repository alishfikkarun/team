# Telegram Gift Bot

A Telegram bot that processes unique gifts, uploads them to S3, and creates webapp links for selling.

## Features

- Processes Telegram service messages containing `unique_gift`
- Extracts gift metadata (title, model, symbol, backdrop details)
- Downloads sticker files from Telegram
- Uploads files to AWS S3 with public URLs
- Stores gift data in SQLite database
- Generates WebApp URLs for gift display
- Prompts users for pricing information

## Environment Variables

Create a `.env` file or set the following environment variables:

```bash
# Required
BOT_TOKEN=your_telegram_bot_token
WEBAPP_URL=http://localhost:5000

# AWS S3 Configuration
S3_BUCKET=your_s3_bucket_name
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
