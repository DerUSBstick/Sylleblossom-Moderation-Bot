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

#Important Code for 1 Year Anniversary

@tasks.loop(seconds=30)
async def publish_polls():
    os.system('cls')
    print(f"Publishing Polls {round(time.time())}")
    with open("anniversary.json") as f:
        data = json.load(f)
    with open("anniversary_polls.json") as f:
        polls_data = json.load(f)
    channel = bot.get_channel(886599665989079070)
    emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
    for x in data["options"]:
        print(f"Checking Poll ID {x} for Publishing")
        if data["questions"][f"{x}"]["published"] != 1 and data["questions"][f"{x}"]["start"] != 0 and data["questions"][f"{x}"]["start"] < time.time():
            print(f"Publishing Poll ID {x}")
            question = data["questions"][f"{x}"]["question"]
            answers = [data["questions"][f"{x}"]["a"], data["questions"][f"{x}"]["b"], data["questions"][f"{x}"]["c"], data["questions"][f"{x}"]["d"]]
            embed = discord.Embed(title=question, description=f"{emojis[0]} {answers[0]}\n{emojis[1]} {answers[1]}\n{emojis[2]} {answers[2]}\n{emojis[3]} {answers[3]}", color=0x33d69f)
            message = await channel.send(embed=embed)
            for y in emojis:
                await message.add_reaction(y)
            data["questions"][f"{x}"]["published"] = 1
            data["questions"][f"{x}"]["end"] = round(time.time()) + 120
            #Writing Evaluation Data
            polls_data["polls"].append(x)
            polls_data[f"{x}"] = {
                "question": f"{question}",
                "reactions": [],
                "channel_id": message.channel.id,
                "message_id": message.id
            }
            i = 0
            for y in emojis:
                polls_data[f"{x}"]["reactions"].append(y)
                polls_data[f"{x}"][f"{y}"] = {
                    "answer": f"{answers[i]}",
                    "reaction_emoji": f"{y}",
                    "users": []
                }
                i += 1
    with open("anniversary.json", "w+") as f:
        json.dump(data, f, indent=4)
    with open("anniversary_polls.json", "w+") as f:
        json.dump(polls_data, f, indent=4)
    print("\n")
    await check_polls()


async def check_polls():
    print(f"Checking Polls {round(time.time())}")
    with open("anniversary.json") as f:
        data = json.load(f)
    with open("anniversary_polls.json") as f:
        polls = json.load(f)
    for x in polls["polls"]:
        print(f"Checking Poll ID {x}")
        if data["questions"][f"{x}"]["end"] != 0 and data["questions"][f"{x}"]["end"] < time.time() and data["questions"][f"{x}"]["evaluated"] == 0:
            print(f"Proceeding Poll ID {x}")
            #Check Polls
            data["questions"][f"{x}"]["evaluated"] = 1
            channel = bot.get_channel(polls[f"{x}"]["channel_id"])
            poll_message = await channel.fetch_message(polls[f"{x}"]["message_id"])
            votes = []
            polls[f"{x}"]["reactions"] = []
            for reaction in poll_message.reactions:
                answer = polls[f"{x}"][f"{reaction.emoji}"]["answer"]
                polls[f"{x}"]["reactions"].append(f"{reaction}")
                polls[f"{x}"][f"{reaction.emoji}"] = {
                    "answer": f"{answer}",
                    "reaction_emoji": f"{reaction.emoji}",
                    "users": []
                }
                reactors = await reaction.users().flatten()
                for y in reactors:
                    if y.id != 939568841325944852:
                        polls[f"{x}"][f"{reaction.emoji}"]["users"].append(y.id)
                        print(y, reaction.emoji)
                if len(polls[f"{x}"][f"{reaction.emoji}"]["users"]) == 0:
                    polls[f"{x}"][f"{reaction.emoji}"]["users"] = 0
                    votes.append(0)
                else:
                    votes.append(len(polls[f"{x}"][f"{reaction.emoji}"]["users"]))
            polls[f"{x}"]["votes"] = sorted(votes, reverse=True)
    with open("anniversary_polls.json", "w+") as f:
        json.dump(polls, f, indent=4)
    with open("anniversary.json", "w+") as f:
        json.dump(data, f, indent=4)
    print("\n")
#End of Important Code



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
