import argparse
import json
from telethon import TelegramClient, events
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.tl.functions.account import UpdateProfileRequest
from PIL import Image
import random
import string
import asyncio
import socks

# Function to generate random name and unique part
def generate_random_name():
    adjectives = ['Red', 'Blue', 'Green', 'Yellow', 'Orange', 'Purple', 'Pink']
    nouns = ['Dog', 'Cat', 'Bird', 'Elephant', 'Lion', 'Tiger', 'Bear']
    
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    unique_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    
    return f'{adjective}{noun}', unique_part

# Function to generate random avatar
def generate_random_avatar(size=128):
    image = Image.new('RGB', (size, size), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    return image

# Function to create a bot
async def create_bot(client, bot_name):
    bot_token = None

    async def send_message_and_wait(event, message):
        await client.send_message('BotFather', message)
        response = await event.wait()
        return response.message

    @client.on(events.NewMessage(from_users='BotFather'))
    async def handler(event):
        nonlocal bot_token
        message = event.message.message

        if "Alright, a new bot. How are we going to call it? Please choose a name for your bot." in message:
            response_message = await send_message_and_wait(event, bot_name)
        elif "Good. Now let's choose a username for your bot." in message:
            bot_username = bot_name.lower().replace(" ", "_") + "_bot"
            response_message = await send_message_and_wait(event, bot_username)
        elif "Done! Congratulations on your new bot." in message:
            bot_token = message.split("Use this token to access the HTTP API: ")[1].split()[0]

    await client.send_message('BotFather', '/newbot')
    await client.run_until_disconnected()

    return bot_name, bot_token

# Function to set bot profile (name and photo)
async def set_bot_profile(client, bot_name):
    # Generate a random avatar
    avatar_image = generate_random_avatar()
    # Upload the avatar
    file = await client.upload_file(avatar_image)
    await client(UploadProfilePhotoRequest(file))

    # Update bot profile name
    await client(UpdateProfileRequest(first_name=bot_name))

# Function to delete all bots (example)
async def delete_all_bots(client):
    # Example: Fetch all bots and delete them
    bots = await client.get_participants('me', filter=lambda u: u.bot)
    for bot in bots:
        await client.delete_messages(bot.username, await client.get_messages(bot.username))

# Function to write Bot Token to file
def write_bot_token(bot_token):
    with open('bot_token.txt', 'w') as f:
        f.write(bot_token)
    print(f'Bot token written to bot_token.txt')

# Main function to manage the entire process
async def main(operation):
    # Read accounts information from file
    with open('accounts.json', 'r') as f:
        accounts = json.load(f)

    # Define the maximum number of bots allowed for each account
    MAX_BOTS_PER_ACCOUNT = 5
    proxy = (socks.HTTP, '135.245.192.7', 8000)

    for account in accounts:
        session_name = str(account['api_id']) #session name reuse api_id value
        async with TelegramClient(session_name, account['api_id'], account['api_hash'], proxy=proxy) as client:
            if operation == 'create':
                # Get the existing bots for the account
                result = await client(GetContactsRequest(0))
                existing_bots = [user for user in result.users if user.bot]

                # Check if the number of existing bots is less than the maximum allowed
                if len(existing_bots) < MAX_BOTS_PER_ACCOUNT:
                    # Create a new bot
                    bot_name, bot_token = await create_bot(client, generate_random_name()[0])  # Use only the name
                    if bot_token:
                        print(f'Bot created: {bot_name}')
                        await set_bot_profile(client, bot_name)  # Set bot profile
                        write_bot_token(bot_token)  # Write Bot Token to file
                else:
                    print(f'Account {account["api_id"]} already has {len(existing_bots)} bots, which is the maximum allowed.')

            elif operation == 'delete':
                # Delete all bots (example)
                await delete_all_bots(client)

# Run the main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create or delete Telegram bots')
    parser.add_argument('operation', choices=['create', 'delete'], help='Operation to perform: create or delete')
    args = parser.parse_args()
    asyncio.run(main(args.operation))

