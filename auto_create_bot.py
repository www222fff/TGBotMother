import argparse
import json
import csv
import os
from telethon import TelegramClient, events
from telethon.tl.functions.photos import UploadProfilePhotoRequest
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.contacts import GetContactsRequest
from PIL import Image
from io import BytesIO  # Import BytesIO from the io module
import random
import string
import asyncio
import socks

api_id = 26120312
api_hash = "a122106d78462db8ab24b1028f3b64b0"
MAX_BOTS_PER_ACCOUNT = 5
proxy = (socks.HTTP, '135.245.192.7', 8000)

async def create_bot(client, bot):
    bot_token = None
    # Event to signal completion of bot_token retrieval
    token_retrieved = asyncio.Event()

    async def send_message_and_wait(message):
        delay_seconds = random.randint(3, 10)
        await asyncio.sleep(delay_seconds)
        await client.send_message('BotFather', message)
        return None

    async def handler(event):
        nonlocal bot_token, token_retrieved
        message = event.message.message

        if "Alright, a new bot. How are we going to call it? Please choose a name for your bot." in message:
            response_message = await send_message_and_wait(bot['name'])
        elif "Good. Now let's choose a username for your bot." in message:
            response_message = await send_message_and_wait(bot['username'])
        elif "Sorry, too many attempts." in message:
            token_retrieved.set()
            bot_token = bot['username'] + '_invalid'
            return bot_token
        elif "Done! Congratulations on your new bot." in message:
            try:
                # Find the line with the token
                lines = message.splitlines()
                for line in lines:
                    if line.startswith("Use this token to access the HTTP API:"):
                        bot_token = lines[lines.index(line) + 1].strip()
                        token_retrieved.set()  # Signal that bot_token has been retrieved
                        print("Bot Token:", bot_token)
                        return bot_token  # Exit handler function and return token
            except IndexError:
                print("Error: Failed to extract bot token from message:", message)

    # Register the handler function for BotFather messages
    client.add_event_handler(
        handler, events.NewMessage(
            from_users='BotFather'))
    await send_message_and_wait('/newbot')

    # Wait for the handler function to set the event indicating bot_token
    await token_retrieved.wait()

    print(f"create {bot_token} success")
    return bot_token


async def set_bot_profile(client, bot):
    avatar_dir = './photos'
    avatar_image = bot['photo']
    avatar_path = os.path.join(avatar_dir, avatar_image)

    if not os.path.exists(avatar_path):
        print(f"Error: File {avatar_path} does not exist.")
        return

    try:
        bot_entity = await client.get_entity(bot['username'])
        photo = await client.upload_file(avatar_path, part_size_kb=512)
        result = await client(UploadProfilePhotoRequest(bot_entity, file=photo))
        print(f"Profile photo set for {bot['username']}")
    except Exception as e:
        print(f"Error uploading profile photo for {bot['username']}: {e}")

def write_bot_token(username, bots):
    with open('output.csv', 'a') as file:
        file.write(f"Account: {username}\n")
        for bot in bots:
            file.write(f"Bot Token: {bot}\n")
        file.write("\n")

async def list_my_bots(client):
    bots = []
    try:
        # Fetch the list of bots using BotFather's /mybots command
        await client.send_message('BotFather', '/mybots')
        response = await client.get_messages('BotFather', limit=1)

        if response and response[0].text.startswith(
                "Choose a bot from the list below:"):
            # Extract buttons from the reply markup
            reply_markup = response[0].reply_markup
            if reply_markup:
                for row in reply_markup.rows:
                    for button in row.buttons:
                        if button.text.startswith('@'):
                            bot_username = button.text.strip('@')
                            bots.append(bot_username)
                            print(f'Found bot: {bot_username}')

            print(f'Listed {len(bots)} bots')
        else:
            print('Failed to list bots: BotFather did not respond correctly')
    except Exception as e:
        print(f'Error listing bots: {e}')
    return bots


async def delete_bot(client, bot_username):
    try:
        # Send delete command to BotFather for the specific bot
        await client.send_message('BotFather', f'/deletebot')
        response = await client.get_messages('BotFather', limit=1)
        if response and f"Choose a bot to delete." in response[0].text:
            await client.send_message('BotFather', f'@{bot_username}')
            await client.send_message('BotFather', 'Yes, I am totally sure.')
            print(f'Bot {bot_username} successfully deleted')
        else:
            print(f'Error: Bot {bot_username} not found or cannot be deleted')
    except Exception as e:
        print(f'Error deleting bot {bot_username}: {e}')


async def delete_all_bots(client):
    bot_usernames = await list_my_bots(client)
    for bot_username in bot_usernames:
        await delete_bot(client, bot_username)

async def operate_bots_for_account(phone, bots, operation):
    session_name = os.path.join('sessions', f"{phone}.session")
    async with TelegramClient(session_name, api_id, api_hash, proxy=proxy) as client:
        await client.start()
        if operation == 'create':
            bot_tokens = []
            for bot in bots:
                # Check if the number of existing bots is less than the maximum
                bot_token = await create_bot(client, bot)
                if bot_token:
                    bot_tokens.append(bot_token)
                    await set_bot_profile(client, bot)  # Set bot profile
            print(f"Account {phone} created all bots done.")
            write_bot_token(phone, bot_tokens)  # Write Bot Token to file

        elif operation == 'delete':
            await delete_all_bots(client)

        await client.disconnect()

async def main(operation):
    with open('output.csv', 'w') as f:
        pass  # This will clear the file

    accounts = {}
    with open('input.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            phone = row['phone']
            bot = {
                'username': row['bot_username'],
                'name': row['bot_name'],
                'photo': row['bot_photo'],
            }

            # Check if the phone number is already a key in the dictionary
            if phone in accounts:
                accounts[phone].append(bot)
            else:
                accounts[phone] = [bot]

    tasks = [operate_bots_for_account(phone, bots, operation) for phone, bots in accounts.items()]
    await asyncio.gather(*tasks)


# Run the main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Create or delete Telegram bots')
    parser.add_argument(
        'operation',
        choices=[
            'create',
            'delete'],
        help='Operation to perform: create or delete')
    args = parser.parse_args()
    asyncio.run(main(args.operation))
