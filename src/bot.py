import discord, os
from discord.ext import commands, ipc

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ipc = ipc.Server(self, secret_key=os.environ['bot_client_secret'])

    async def on_ready(self):
        """Called upon the READY event"""
        print("Bot is ready.")

    async def on_ipc_ready(self):
        """Called upon the IPC Server being ready"""
        print("Ipc server is ready.")

    async def on_ipc_error(self, endpoint, error):
        """Called upon an error being raised within an IPC route"""
        print(endpoint, "raised", error)

my_bot = MyBot(command_prefix="$", intents=discord.Intents.default())

@my_bot.command()
async def hello(ctx): 
    await ctx.send("Hello there!")

my_bot.ipc.start()
my_bot.run(os.environ['bot_token'])