from turtle import clear
import discord
from discord.ext import commands
from discord.ext import tasks
import json
import time
import datetime
import os
import asyncio
import aiohttp
import urllib.request
from PIL import Image
import io

start = time.time() #When the bot started
prefix = "-"
intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.messages = True
bot = commands.Bot(command_prefix=prefix, case_insensitive=True, intents=intents)

def parse_duration(duration: int):
    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    duration = []
    if days > 0:
        if days > 1:
            duration.append('{} days'.format(days))
        else:
            duration.append('{} day'.format(days))
    if hours > 0:
        if hours > 1:
            duration.append('{} hours'.format(hours))
        else:
            duration.append('{} hour'.format(hours))
    if minutes > 0:
        if minutes > 1:
            duration.append('{} minutes'.format(minutes))
        else:
            duration.append('{} minute'.format(minutes))
    if seconds > 0:
        if seconds > 1:
            duration.append('{} seconds'.format(seconds))
        else:
            duration.append('{} second'.format(seconds))
    else:
        duration.append('-')

    return ', '.join(duration)

def convert_to_unix(time):
    time = time.replace("-", "/")
    result = datetime.datetime.strptime(time, "%Y/%m/%dT%H:%M:%SZ").timestamp()
    return int(round(result))

async def create_logs(reason, user: int, moderator: int, action):
    user = await bot.fetch_user(user)
    moderator = await bot.fetch_user(moderator)
    embed = discord.Embed(title=f"{action}", description=f"Offender: {user} {user.mention}\nReason: {reason}\nResponsible moderator: {moderator}", color=0x00fff8)
    embed.set_footer(text=f"{user.id}")
    embed.timestamp = datetime.datetime.now()
    channel = bot.get_channel(979335099143319562)
    await channel.send(embed=embed)

#Checks if the Husbando bots are online
#If not, bot gets marked as temporarely offline, after 5 minutes the channel gets locked and a message appears
#If the bot is back online, the message gets deleted and the channel opened up again
@tasks.loop(seconds=15)
async def check_status():
    msg = ""
    with open("bots.json") as f:
        data = json.load(f)
    guild = bot.get_guild(854733975197188108)
    bots = [857333365636202507, 887684485469073448, 872205461636648961, 886626811444871188]
    for x in bots:
        #user = await bot.fetch_user(x)
        user = guild.get_member(x)
        if user.status == discord.Status.online:
            if data[user.name]["status"] == 0:
                channel = bot.get_channel(data[user.name]["channel"])
                await channel.set_permissions(guild.default_role, send_messages=None)
                message = await channel.fetch_message(data[user.name]["message"])
                await message.delete()
                data[user.name]["message"] = 0
                data[user.name]["status"] = 1

            data[user.name]["down"] = round(time.time())
            msg += f"{user.name} is currently Online <a:Success:778267705643892757>\n\n"
        elif user.status == discord.Status.offline:
            if time.time() - data[user.name]["down"] < 30:
                print(round(time.time() - data[user.name]["down"]))
                msg += f"{user.name} is currently Offline <a:Loading:778267707715485696>\n\n"
            else:
                if data[user.name]["status"] == 1:
                    channel = bot.get_channel(data[user.name]["channel"])
                    await channel.set_permissions(guild.default_role, send_messages=False)
                    message = await channel.send(f"{user.name} is currently experiencing an Outage. Check <#892102362813055026> for further Informations")
                    data[user.name]["status"] = 0
                    data[user.name]["message"] = message.id
                down_time = parse_duration(round(time.time() - data[user.name]["down"]))
                msg += f"{user.name} is currently experiencing an Outage since {down_time} <a:Error:778267709904519209>\n\n"
                channel = bot.get_channel(data[user.name]["channel"])
    
    embed = discord.Embed(title="Status", description=msg, color=0x0062ff, timestamp=datetime.datetime.utcnow())
    channel = bot.get_channel(965523098885582848)
    message = await channel.fetch_message(965674314462552064)
    await message.edit(content=None, embed=embed)
    
    with open("bots.json", "w+") as f:
        json.dump(data, f, indent=4)

@tasks.loop(minutes=5)
async def subscriber_counter():
    guild = bot.get_guild(980034765501636608)
    channel_id = "YT_CHANNEL_ID"
    key = "YT_API_KEY"

    data = urllib.request.urlopen(f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_id}&key={key}").read()
    subs = json.loads(data)['items'][0]['statistics']['subscriberCount']
    channel_counter = bot.get_channel(980034765501636608)
    await channel_counter.edit(name=f"{subs} Subs")
       
#Simple Ping command
@bot.command()
async def ping(ctx):
    await ctx.send(f"{round(bot.latency*1000, 4)}ms")

#Command to see, how long the bot has been online
#Cooldown of 5 seconds
@bot.command()
@commands.cooldown(1, 5, commands.BucketType.member)
async def uptime(ctx):
    cur = time.time()
    diff = int(round(cur - start))
    await ctx.send(f'Uptime: {parse_duration(diff)}')

#Give and Remove someones Image Permissions in #artworks and so on
@bot.command()
@commands.has_any_role(974770032993267803, 939558108609523742, 895753360920178699)
async def imperms(ctx, user: discord.Member, *, reason=None):
    guild = ctx.guild
    user = ctx.guild.get_member(user.id)
    role = guild.get_role(958047463179169842)
    try:
        if role in user.roles:
            action = "Image Permissions Granted"
            await user.remove_roles(role)
            await ctx.send(f"{user.mention} has been Granted Image Permissions")
        else:
            action = "Image Permissions Denied"
            await user.add_roles(role)
            await ctx.send(f"Image Permissions have been denied for {user.mention}")
        await create_logs(reason, user.id, ctx.message.author.id, action)
    except Exception as e:
        print(e)
        
@bot.event
async def on_message(message):
    if message.attachments != []:
        im = 0
        log_channel = bot.get_channel(965623933871226890)
        for x in message.attachments:
            embed = discord.Embed(title=f"{message.author.name} posted an Image")
            embed.set_image(url=x)
            embed.set_footer(text=f"{message.channel.id}_{message.author.id}_{message.id}_{im}")
            await log_channel.send(embed=embed)
            im += 1
    await bot.process_commands(message)
        
@bot.event
async def on_ready():
    subscriber_counter.start()
    check_status.start()
    print(f"Logged in")

bot.run("BOT_TOKEN")
