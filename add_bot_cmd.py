import asyncio
from telethon import TelegramClient, events, Button
from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.types import BotCommand, BotCommandScopeDefault
import socks

api_id = 26120312
api_hash = "a122106d78462db8ab24b1028f3b64b0"
proxy = (socks.HTTP, '135.245.192.7', 8000) 
bot_token = "7072992402:AAEmpzoAmup6NssYZtLylaVdjRjyR8ioBpw"

async def set_bot_commands(client):
    commands = [
        BotCommand(command='play', description='Play Game'),
    ]
    await client(SetBotCommandsRequest(
        scope=BotCommandScopeDefault(),
        lang_code='',
        commands=commands
    ))
    print("Bot commands have been set.")

async def main():
    # Create a TelegramClient instance inside main
    client = TelegramClient('session_name', api_id, api_hash, proxy=proxy)
    
    # Define an event handler for messages that match the pattern '/play'
    @client.on(events.NewMessage(pattern='/play'))
    async def handle_play(event):
        buttons = [Button.url('Click here to play', 'https://hamsterkombat.io/clicker')]
        await event.respond('Welcome! Click the button below to start:', buttons=buttons)

    try:
        # Start the TelegramClient with the bot token
        await client.start(bot_token=bot_token)
        print("Telegram client connected successfully.")
        await set_bot_commands(client)
        # Run the client until disconnected
        await client.run_until_disconnected()
    
    except KeyboardInterrupt:
        print("Bot stopped by user.")
    
    finally:
        # Disconnect the client on exit
        await client.disconnect()

# Run the main function using asyncio
if __name__ == '__main__':
    asyncio.run(main())
