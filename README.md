# Telegram Channel Reader

A simple Python script using Telethon to download all text posts from any public Telegram channel and save them to a local text file.

## Features
- Fetches all text messages from a specified public Telegram channel.
- Saves messages in chronological order (oldest to newest).
- Skips media files, downloading only text.
- Automatically handles Telegram API limits and pagination.

## Prerequisites
- Python 3.7+
- Telegram API ID and API Hash (obtain from [my.telegram.org](https://my.telegram.org))

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Sergo366/telegram-chanel-reader.git
cd telegram-chanel-reader
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Before running the script, open `main.py` and configure the following variables:
- `API_ID`: Your API ID from my.telegram.org (integer)
- `API_HASH`: Your API Hash from my.telegram.org (string)
- `CHANNEL_USERNAME`: The target channel username or link (e.g., `@telegram`)

## Usage

Run the script:
```bash
python main.py
```

On the first run, you will be prompted to enter your phone number and a confirmation code sent to your Telegram app. This creates a `.session` file so you don't have to log in every time.

The downloaded posts will be saved in `posts.txt`.
