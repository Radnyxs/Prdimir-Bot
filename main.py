from datetime import timedelta, datetime
import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

import random

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="prd ", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"\nJsme připraveni ke vzletu, pane {bot.user.name}!")

@bot.event
async def on_member_join(member):
    await member.create_dm(f"Ahoj {member.name.mention}, vítej na serveru!\nJestli budeš potřebovat s něčím pomoct, napiš majitelovi či komukoliv s rolí Otrok.\nPřeji příjemně strávený čas!\n\t- Prdimír, domácí robot od Radnyxe")

@bot.command()
async def knp(ctx, choice: str):
    choice = choice.lower()
    options = ["kámen", "nůžky", "papír"]

    if choice not in options:
        await ctx.send("neplýtvej mým časem pls")
        return

    bot_choice = random.choice(options)

    if choice == bot_choice:
        result = "remíza!!"
    elif (choice == "kámen" and bot_choice == "nůžky") or \
        (choice == "papír" and bot_choice == "kámen") or \
        (choice == "nůžky" and bot_choice == "papír"):
        result = f"{ctx.author.mention} porazil/a jsi mě, gg"
    else:
        result = "vyhrál jsem! :trophy:"

    await ctx.send(f"**{ctx.author.mention}**: {choice}\n**Prdimír**: {bot_choice}\n\n{result}")

@bot.command()
async def open(ctx, *, site: str):
    site = site.lower()

    links = {
        "youtube": "https://www.youtube.com",
        "yt": "https://www.youtube.com",
        "google": "https://www.google.com",
        "github": "https://www.github.com",
        "invite": "https://discord.com/invite/KWCjm4zrqG",
        "spotify": "https://open.spotify.com/",
        "pornhub": "https://pornhub.com",
        "ph": "https://pornhub.com"
    }

    if site in ("pornhub", "ph"):
        response_text = f"sus!! {links[site]}"
    elif site in links:
        response_text = links[site]
    else:
        search_url = f"https://www.google.com/search?q={site.replace(' ', '+')}"
        response_text = f"nenašel jsem zkratku, tak jsem ti ji vygooglil: {search_url}"

    # jestli v DMs -> do konzole
    if isinstance(ctx.channel, discord.DMChannel):
        čas = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        print(f"\n[{čas} - Prdimír]: {response_text}")
        await ctx.send(response_text)
    else:
        # jestli v serveru:
        await ctx.send(response_text)


@bot.command()
async def senddm(ctx, member: discord.User, *, text: str):
    allowed_users = [449847721386573825]

    if ctx.author.id not in allowed_users:
        await ctx.send("na tento příkaz nemáš oprávnění!! ❌")
        return

    try:
        # 1) pošle DM
        await member.send(text)

        try:
            local_time = ctx.message.created_at + timedelta(hours=2)
            čas = local_time.strftime("%d.%m.%Y %H:%M:%S")
        except Exception:
            čas = "Neznámý čas"

        print(f"\n[{čas}] - ✅ Zpráva odeslána uživateli {member.display_name} ({member.name} // ID: {member.id}): {text}")

        if not isinstance(ctx.channel, discord.DMChannel):
            try:
                await ctx.message.delete()
            except Exception:
                pass

        await ctx.send(f"✅ Zpráva odeslána uživateli {member.display_name} ||({member.name} // ID: {member.id})||")

    except discord.Forbidden:
        print(f"\n❌ CHYBA: Zpráva se neodeslala {member.display_name} ({member.name} // ID: {member.id}). Má zavřené DMs.")
        await ctx.send(f"❌ Zprávu se neodeslala uživateli {member.display_name} ||({member.name} // ID: {member.id}||. Má zavřené DMs.")
    except Exception as e:
        print(f"\n⚠️ NEČEKANÁ CHYBA V SENDDM: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        local_time = message.created_at + timedelta(hours=2)
        čas = local_time.strftime("%d.%m.%Y %H:%M:%S")

        msg_text = message.content
        if message.attachments:
            attachment_urls = " ".join([att.url for att in message.attachments])
            msg_text = f"{msg_text} [Příloha: {attachment_urls}]".strip()

        print(f"\n[{čas} - {message.author}]: {msg_text}")

    if not isinstance(message.channel, discord.DMChannel):
        content = message.content.lower()

        if any(word in content for word in ("kurva", "kurvo", "kurvy", "zkurvený", "zkurvenej", "zkurvená", "píča", "píče", "píčo", "piča", "piče", "pičo", "mrdka", "mrdko", "mrdky", "čůrák", "čůráku", "čurák", "čuráku")):
            await message.channel.send("hej!! slušně prosím <:didopycy:1560017961677226104>")

        if any(word in content for word in ("negr", "nigger", "nigga", "niggers", "negři", "negry", "negrové", "negrama", "negri")):
            await message.channel.send(f"{message.author.mention} seš nějak v pohodě dnes :-)")

        if content == "ahoj":
            await message.channel.send(f"ahoj {message.author.mention}")

        if content == "aoj":
            await message.channel.send(f"aoj {message.author.mention}")

        if content == "ečus":
            await message.channel.send(f"ečus {message.author.mention}")

        if content == "prd":
            responses = [
                "neprď mi tady",
                "karlos si usral?"
            ]
            await message.channel.send(random.choice(responses))

        if content in ("dobrou", "dobrou noc"):
            await message.channel.send(f"dobrouu hezky se vyspi {message.author.mention} <3")

        if content == "<@1560639270216138902>":
            await message.channel.send(f"co chceš {message.author.mention}??")

        if content == "who is bro":
            responses = [
                "https://upload.wikimedia.org/wikipedia/en/6/63/Graggle_Simpson.jpeg?utm_source=en.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail_unscaled",
                "graggle simpson",
                "https://imgs.search.brave.com/7k_NgItDxNEOl3ipQd1r2Y2znM1EKzGGcy2rD8Nx6UU/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9pbWFn/ZXMtd2l4bXAtZWQz/MGE4NmI4YzRjYTg4/Nzc3MzU5NGMyLndp/eG1wLmNvbS9mL2Y1/Y2E2ZjdiLWNjNGQt/NGY2ZC04ZWE1LWM2/MTM4ZmJkOGU3ZC9k/bW9xa21sLWU3ODBi/MWZhLWQ0YzEtNDcw/YS1hNDQ5LTZkNWY2/NzBmZTI0YS5wbmc_/dG9rZW49ZXlKMGVY/QWlPaUpLVjFRaUxD/SmhiR2NpT2lKSVV6/STFOaUo5LmV5Snpk/V0lpT2lKMWNtNDZZ/WEJ3T2pkbE1HUXhO/V1ZoTUdReU5tVXdJ/aXdpYVhOeklqb2lk/WEp1T21Gd2NEbzNa/VEJrTVRnNE9UZ3lN/alkwTXpjellUVm1N/R1EwTVRWbFlUQmtN/alpsTUNJc0ltOWlh/aUk2VzF0N0luQmhk/R2dpT2lJdlppOW1O/V05oTm1ZM1lpMWpZ/elJrTFRSbU5tUXRP/R1ZoTlMxak5qRXpP/R1ppWkRobE4yUXZa/RzF2Y1d0dGJDMWxO/emd3WWpGbVlTMWtO/R014TFRRM01HRXRZ/VFEwT1MwMlpEVm1O/amN3Wm1VeU5HRXVj/RzVuSW4xZFhTd2lZ/WFZrSWpwYkluVnli/anB6WlhKMmFXTmxP/bVpwYkdVdVpHOTNi/bXh2WVdRaVhYMC4x/Z18yY3lRalpPTHdk/SEo5UFZld21yb3pJ/Sjc4cnJNU1JfTmR6/RURpZmJF"
            ]
            await message.channel.send(random.choice(responses))

        if "honze" in content:
            await message.add_reaction("🐰")

    await bot.process_commands(message)

async def log_only(ctx, text):
    if isinstance(ctx.channel, discord.DMChannel):
        local_time = datetime.now()
        čas = local_time.strftime("%d.%m.%Y %H:%M:%S")
        print(f"\n[{čas} - Prdimír (Console Only)]: {text}")

@bot.event
async def on_message_delete(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        local_time = datetime.now()
        čas = local_time.strftime("%d.%m.%Y %H:%M:%S")

        msg_text = message.content or "[Bez textu]"
        if message.attachments:
            attachment_urls = " ".join([att.url for att in message.attachments])
            msg_text = f"{msg_text} [Příloha: {attachment_urls}]".strip()

        print(f"\n[{čas} - 🗑️ ZPRÁVA SMAZÁNA od {message.author}]: {msg_text}")

@bot.command()
async def test(ctx):
    print("\nDEBUG: test příkaz spuštěn v DMs nebo serveru!")

    if isinstance(ctx.channel, discord.DMChannel):
        await log_only(ctx, "funguje!")
    else:
        await ctx.send("funguje!")

@bot.event
async def on_command_error(ctx, error):
    print(f"\n⚠️ CHYBA PŘÍKAZU ({ctx.command}): {error}")

bot.run(token, log_handler = handler, log_level = logging.DEBUG)

