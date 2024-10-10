import math
import time
import json
import logging
import requests
from colorama import Fore
import discord, time
from discord.ext import tasks
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from discord.ext.commands import has_permissions, CheckFailure

intents = discord.Intents(messages=True)
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="+", intents=intents)

with open("config.json") as conf:
    config = json.load(conf)
    channels = config["channels"]
    bot_token = config["token"]

global owd_bans, ostaff_bans
global session

session = requests.Session()
owd_bans = None
ostaff_bans = None

session.headers.update({
    "Accept": "application/json",
    "Origin": "https://plancke.io",
    "Referer": "https://plancke.io/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
})

#Startup
@bot.event
async def on_ready():
    checkloop.start()
    print(r"""

  ____                _______             _             
 |  _ \              |__   __|           | |            
 | |_) | __ _ _ __      | |_ __ __ _  ___| | _____ _ __ 
 |  _ < / _` | '_ \     | | '__/ _` |/ __| |/ / _ \ '__|
 | |_) | (_| | | | |    | | | | (_| | (__|   <  __/ |   
 |____/ \__,_|_| |_|    |_|_|  \__,_|\___|_|\_\___|_|   
                                                        
            """)
    print(f"{Fore.LIGHTGREEN_EX}Hypixel ban tracker has been started.{Fore.RESET}")
    print(f"{Fore.LIGHTGREEN_EX}Bot Prefix: +{Fore.RESET}")
    await bot.change_presence(activity=discord.Game(name=f"+cmd to get started! | {len(bot.guilds)} Servers"))
    
async def send(*, message):
    for channel_id in channels:
        try:
            channel = await bot.fetch_channel(channel_id)
            await channel.send(message)
        except Exception as e:
            print("ERROR:", e, "| Channel ID:", channel_id, "-", channel)
            continue

async def newChannel(channel_id):
    channels.append(channel_id)
    config = {
        "token": bot_token,
        "channels": channels
    }
    with open("config.json", "w") as f:
        f.write(json.dumps(config, indent=4))
        f.close()

async def delChannel(channel_id):
    channels.remove(channel_id)
    config = {
        "token": bot_token,
        "channels": channels
    }
    with open("config.json", "w") as f:
        f.write(json.dumps(config, indent=4))
        f.close()
        
@bot.command()
async def cmd(ctx):
    try:
        embed = discord.Embed(
            title="Hypixel Ban Tracker",
            description="**+cmd** - Show this help command.\n**+addchannel** - Add channel to the list.\n**+removechannel** - Remove channel from the list.\n**+ping** - Pong!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        print(e)

@bot.command()
async def ping(ctx):
    try:
        embed = discord.Embed(
            title="Hypixel Ban Tracker",
            description=f"Pong! {round (bot.latency * 1000)} ms",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        print(e)
        
@bot.command()
async def addchannel(ctx, channel: int):
    try:
        await newChannel(channel)
        embed = discord.Embed(
            title="Hypixel Ban Tracker",
            description=f"Added <#{channel}> to the list! (please make sure to give the bot permission to send chat message on the channel.)",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        print(e)

@addchannel.error
async def addchannel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Hypixel Ban Tracker",
            description="Usage: +addchannel [channel id]",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Hypixel Ban Tracker",
            description="You don't have permission to use this command! (administrator)",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

@bot.command()
async def removechannel(ctx, channel: int):
    try:
        await delChannel(channel)
        embed = discord.Embed(
            title="Hypixel Ban Tracker",
            description=f"Removed <#{channel}> from the list.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    except Exception as e:
        print(e)
        
@removechannel.error
async def removechannel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            title="Hypixel Ban Tracker",
            description="Usage: +removechannel [channel id]",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    if isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="Hypixel Ban Tracker",
            description="You don't have permission to use this command! (administrator)",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        raise(error)

@tasks.loop(seconds=12)
async def updaterpc():
    await bot.change_presence(activity=discord.Game(name=f"+cmd to get started! | {len(bot.guilds)} Servers"))
        
# The actual checker
@tasks.loop(seconds=0.2)
async def checkloop():
    global owd_bans, ostaff_bans, session
    resp = session.get("https://api.plancke.io/hypixel/v1/punishmentStats")
    #print(resp.text)
    wd_bans = resp.json().get("record").get("watchdog_total")
    staff_bans = resp.json().get("record").get("staff_total")
    if owd_bans != None and ostaff_bans != None:
        wban_dif = wd_bans - owd_bans
        sban_dif = staff_bans - ostaff_bans

        if wban_dif > 0:
            #embed = discord.Embed(
                #color=discord.Color.from_rgb(247, 57, 24),
                #description=f"<t:{math.floor(time.time())}:R>",
            #).set_author(name=f"Watchdog banned {wban_dif} player{'s' if wban_dif > 1 else ''}!")
            #await bot.change_presence(activity=discord.Game(name=f"Watchdog: {wban_dif} player{'s' if wban_dif > 1 else ''}!"))
            await send(message=f":dog: Watchdog banned **{wban_dif}** player{'s' if wban_dif > 1 else ''}! <t:{math.floor(time.time())}:R>")

        if sban_dif > 0:
            #embed = discord.Embed(
                #color=discord.Color.from_rgb(247, 229, 24),
                #description=f"<t:{math.floor(time.time())}:R>",
            #).set_author(name=f"Staff banned {sban_dif} player{'s' if sban_dif > 1 else ''}!")
            #await bot.change_presence(activity=discord.Game(name=f"Staff: {sban_dif} player{'s' if sban_dif > 1 else ''}!"))
            await send(message=f":man_detective: Staff banned **{sban_dif}** player{'s' if sban_dif > 1 else ''}! <t:{math.floor(time.time())}:R>")

    owd_bans = wd_bans
    ostaff_bans = staff_bans


bot.run(bot_token)
