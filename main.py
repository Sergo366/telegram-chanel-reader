import os
from telethon import TelegramClient

# Insert your api_id and api_hash here.
# Note: API_ID must be an integer, and API_HASH must be a string
API_ID = 00000000 # REPLACE WITH YOUR API_ID
API_HASH = '000000000000' # REPLACE WITH YOUR API_HASH

# Channel username or link to download posts from
CHANNEL_USERNAME = '@chanel_name' # REPLACE WITH TARGET CHANNEL (e.g., @telegram)

# Output file name for saving posts
OUTPUT_FILE = 'posts.txt'

# Session file name to save authorization, preventing code prompt on every run
SESSION_NAME = 'tg_session'

async def main():
    print("Connecting to Telegram...")
    # Create the client. On first run, it will ask for your phone number and Telegram code.
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        print(f"Successfully authorized! Fetching posts from {CHANNEL_USERNAME}...")
        
        try:
            channel = await client.get_entity(CHANNEL_USERNAME)
            messages_count = 0
            
            # Open file for writing. encoding='utf-8' is important for emojis and non-latin characters
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                # Iterate over all messages in the channel.
                # reverse=True means chronological order (oldest to newest)
                # Remove reverse=True to save from newest to oldest.
                async for message in client.iter_messages(channel, reverse=True):
                    # Check if the message has text content
                    if message.text:
                        f.write(message.text + '\n')
                        # Add a separator between posts for readability
                        f.write('\n' + '='*50 + '\n\n')
                        messages_count += 1
                        
                        if messages_count % 100 == 0:
                            print(f"Downloaded {messages_count} posts...")
                            
            print(f"Done! Successfully saved {messages_count} posts to {OUTPUT_FILE}.")
            
        except ValueError:
            print(f"Error: Channel {CHANNEL_USERNAME} not found or inaccessible.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
