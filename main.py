from datetime import timedelta, datetime
import discord
from discord.ext import commands
import logging

from discord.ext.commands import BadArgument
from dotenv import load_dotenv
import os
import aiohttp
from google import genai
import asyncio

import random

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="prd ", intents=intents, help_command=None)

user_message_history = {}

@bot.event
async def on_ready():
    print(f"\nJsme připraveni ke vzletu, pane {bot.user.name}!")

@bot.event
async def on_member_join(member):
    await member.send(f"Ahoj {member.mention}, vítej na serveru!\nJestli budeš potřebovat s něčím pomoct, napiš majitelovi či komukoliv s rolí Otrok.\nPřeji příjemně strávený čas!\n\t- Prdimír, domácí robot od Radnyxe")

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
        result = f"{ctx.author.name} porazil/a jsi mě, gg"
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
            local_time = ctx.message.created_at + timedelta(hours=1)
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
        await ctx.send(f"❌ Zprávu se neodeslala uživateli {member.display_name} ||({member.name} // ID: {member.id})||. Má zavřené DMs.")
    except Exception as e:
        print(f"\n⚠️ NEČEKANÁ CHYBA V SENDDM: {e}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        local_time = message.created_at + timedelta(hours=1)
        čas = local_time.strftime("%d.%m.%Y %H:%M:%S")

        msg_text = message.content
        if message.attachments:
            attachment_urls = " ".join([att.url for att in message.attachments])
            msg_text = f"{msg_text} [Příloha: {attachment_urls}]".strip()

        print(f"\n[{čas} - {message.author}]: {msg_text}")

    if not isinstance(message.channel, discord.DMChannel):
        now = datetime.now()
        user_id = message.author.id
        if user_id not in user_message_history:
            user_message_history[user_id] = []

        user_message_history[user_id].append(now)
        user_message_history[user_id] = [
            t for t in user_message_history[user_id] if (now - t).total_seconds() < 5 # čas
        ]

        if len(user_message_history[user_id]) >= 5: # počet zpráv
            user_message_history[user_id] = []  # reset počítání

            try:
                await message.author.timeout(timedelta(minutes=5), reason="spam")
                await message.channel.send(f"{message.author.mention} drž hubu")
                print(f"\n[TIMEOUT] {message.author} dostal/a 5minutový timeout za spam.")
            except discord.Forbidden:
                await message.channel.send("❌ Nemám oprávnění dát tomuto uživateli timeout!\nMusím mít vyšší roli než on/a")
            except Exception as e:
                print(f"⚠️ Chyba při udělování timeoutu: {e}")

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

        if content == "něco bych zajedl":
            await message.channel.send("ubrousku, prostři se")

        if content == "prd":
            responses = [
                "neprď mi tady",
                "karlos si usral?",
                "na záchodě ze mě vždycky vypadávají dlouhý klobásy",
                "smrdíš jak moje podpaží, když zapomenu na deodorant",
                "https://www.google.com/search?q=caitvi+twitter",
                "Těpi mi prodal fentanyl za 620Kč",
                "šplouch",
                "nemám toaleťák, neprď tady",
                "zkontroluj si spoďáry"
            ]
            await message.channel.send(random.choice(responses))

        if content == "jsem chudej" or content == "jsem chudá" or content == "jsem chudý" or content == "nemám peníze":
            await message.channel.send(f"Chápu tě, {message.author.name}. Tady je seznam stránek, na které **URČITĚ** nechoď, protože jsou **ILEGÁLNÍ**:\n`stránky jsou bezpečné, ale radši používej nějaký AdBlock`"
                                       f"\n\nHry: <https://steamrip.com/>, <https://gamebounty.world/>"
                                       f"\n\nFilmy/Seriály: <https://svetserialu.to/>, <https://popcornmovies.ac/>"
                                       f"\n\nStahování videí: <https://cobalt.meowing.de/>")

        if content in ("dobrou", "dobrou noc"):
            responses = [
                f"dobrouu hezky se vyspi {message.author.mention} <3",
                "Buonanotte signor/a <3"
            ]
            await message.channel.send(random.choice(responses))

        if content == "<@1560639270216138902>":
            responses = [
                f"co chceš {message.author.mention}??",
                "nemám čas na tvoje picovinky",
                "hee hee",
                "h",
                "kéž bych měl nějakou alt gf :(",
                "no povídej",
                "očekáváš nějakou odpověď? jsem bot káre, musíš mi dát příkaz"
            ]
            await message.channel.send(random.choice(responses))

        if content == "who is bro":
            responses = [
                "https://upload.wikimedia.org/wikipedia/en/6/63/Graggle_Simpson.jpeg?utm_source=en.wikipedia.org&utm_campaign=imageinfo&utm_content=thumbnail_unscaled",
                "https://cdn-v2.meme.com/memes/barf-simmons-barf-symptons/barf-simmons-barf-symptons-barf-symptons-cover.webp"
            ]
            await message.channel.send(random.choice(responses))

        if "honze" in content:
            await message.add_reaction("🐰")

        if content == "jsem černej" or content == "jsem černoch" or content == "jsem negr" or content == "jsem černá" or content == "mám tmavou barvu pleti" or content == "jsem z Afriky" or content == "jsem Afričan":
            try:
                doba_mute = timedelta(minutes=2)
                await message.author.timeout(doba_mute, reason = "ohrožování publika")
            except:
                await message.channel.send(f"❌ nemůžu uživatele {message.author.name} poslat na trestnou lavici!!")

    await bot.process_commands(message)

@bot.command()
async def prvek(ctx, *, dotaz: str):
    chemicke_prvky = {
        "H": "Vodík",
        "He": "Helium",
        "Li": "Lithium",
        "Be": "Beryllium",
        "B": "Bor",
        "C": "Uhlík",
        "N": "Dusík",
        "O": "Kyslík",
        "F": "Fluor",
        "Ne": "Neon",
        "Na": "Sodík",
        "Mg": "Hořčík",
        "Al": "Hliník",
        "Si": "Křemík",
        "P": "Fosfor",
        "S": "Síra",
        "Cl": "Chlor",
        "Ar": "Argon",
        "K": "Draslík",
        "Ca": "Vápník",
        "Fe": "Železo",
        "Cu": "Měď",
        "Zn": "Zinek",
        "Ag": "Stříbro",
        "Au": "Zlato",
        "Hg": "Rtuť",
        "Pb": "Olovo",
        "At": "Astat"
    }
    vstup = dotaz.strip().lower()

    # 1. Hledání podle ZNAČKY
    for znacka, nazev in chemicke_prvky.items():
        if znacka.lower() == vstup:
            await ctx.send(f"🧪 chemická značka **{znacka}** patří prvku: **{nazev}**")
            return

    # 2. Hledání podle NÁZVU
    for znacka, nazev in chemicke_prvky.items():
        if nazev.lower() == vstup:
            await ctx.send(f"🧪 prvek **{nazev}** má chemickou značku: **{znacka}**")
            return

    await ctx.send(f"❌ Prvek ani značku **{dotaz}** v mé databázi zatím nemám!")

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

@bot.command()
async def sayin(ctx, channel: discord.TextChannel, *, text: str):
    allowed_users = [449847721386573825]

    if ctx.author.id not in allowed_users:
        await ctx.send("na tento příkaz nemáš oprávnění!! ❌")
        return

    try:
        await channel.send(text)
        čas = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        server_name = channel.guild.name
        print(f"\n[{čas} - ✅ Odesláno do '{server_name}' #{channel.name} ({channel.id})] od {ctx.author.name}: {text}")
        await ctx.send(f"✅ Odesláno do {channel.mention}!")
    except discord.Forbidden:
        await ctx.send(f"❌ Nemám oprávnění v {channel.mention}!!")
    except Exception as e:
        print(f"\n⚠️ CHYBA V SAYIN: {e}")
        await ctx.send(f"⚠️ Nastala chyba: {e}")

@bot.command()
async def help(ctx):
    await ctx.send('**Příkazy (prefix "prd")**'
                   '\n`knp [volba]` - klasická hra 🪨, ✂️, 📄'
                   '\n`open [název stránky]` - vyhledám za tebe stránku a pošlu odkaz!'
                   '\n`prvek [značka]` - řeknu ti, co se za chemickou značkou schovává za prvek'
                   '\n`počasí [město]` - jak se teď žije?'
                   '\n`ruskaruleta` - 1/6 šance, že ti slimenu prdel...teda jestli mám práva'
                   '\n`gambling` - obří minihra života...tohle je jen pomocný příkaz na mnoho dalších'
                   
                   '\n\n**Příkazy s omezeným přístupem**'
                   '\n`kick [@uzivatel] [důvod]` - kickneš danou osobu'
                   '\n`ban [@uzivatel] [důvod]` - dáš ban dané osobě'
                   '\n`timeout [@uzivatel] [minuty] [důvod]` - dáš timeout dané osobě'
                   '\n`sayin [kanál] [zpráva]` - pošlu do nějakého kanálu zprávu'
                   '\n`senddm [uživatel] [zpráva]` - pošlu někomu zprávu do DMs')


@bot.command()
async def počasí(ctx, *, mesto: str):
    if not WEATHER_API_KEY:
        await ctx.send("❌ Chybí konfigurace WEATHER_API_KEY v .env souboru!")
        return

    # units=metric vrací teplotu v °C, lang=cz vrací český popis
    url = f"http://api.openweathermap.org/data/2.5/weather?q={mesto}&appid={WEATHER_API_KEY}&units=metric&lang=cz"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()

                # vytažení dat z odpovědi
                nazev_mesta = data["name"]
                teplota = round(data["main"]["temp"], 1)
                pocitova_temp = round(data["main"]["feels_like"], 1)
                vlhkost = data["main"]["humidity"]
                popis = data["weather"][0]["description"].capitalize()
                rychlost_vetru = data["wind"]["speed"]

                embed = discord.Embed(
                    title=f"🌤️ Počasí: {nazev_mesta}",
                    color=discord.Color.blue()
                )
                embed.add_field(name="Teplota", value=f"**{teplota} °C** (pocitově {pocitova_temp} °C)", inline=False)
                embed.add_field(name="Stav", value=f"{popis}", inline=True)
                embed.add_field(name="Vlhkost", value=f"{vlhkost} %", inline=True)
                embed.add_field(name="Vítr", value=f"{rychlost_vetru} m/s", inline=True)

                await ctx.send(embed=embed)

            elif response.status == 404:
                await ctx.send(f"❌ Město **{mesto}** se nepodařilo najít!")
            else:
                error_text = await response.text()
                await ctx.send(f"⚠️ API vrátilo chybu! Status: `{response.status}` | Odpověď: `{error_text}`")

@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def ruskaruleta(ctx):
    # šance na výstřel (např. 1 z 6)
    ziva_rana = random.randint(1, 6)
    naboj = 1  # když padne tato jednička, uživatel prohrál

    if ziva_rana == naboj:
        try:
            doba_mute = timedelta(minutes=1)
            await ctx.author.timeout(doba_mute, reason="Prohrál/a ruskou ruletu s Prdimírem")

            await ctx.send(
                f"💥 **AU!** Byl tam náboj! {ctx.author.mention} se musí probrat! 🩸")
        except discord.Forbidden:
            await ctx.send(
                f"💥 **STŘELA!** {ctx.author.mention} by schytal/a kulku, ale nemám svolení mu/ji střelit do hlavy! 🛡️")
    else:
        await ctx.send(f"💨 *cvak* přežil/a jsi! v komoře nic nebylo, máš štěstí, {ctx.author.mention}. ☕")


@ruskaruleta.error
async def ruleta_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ v klidu more, zbraň se ještě chladí! zkus to za {round(error.retry_after, 1)} sekund.")

@bot.command()
async def kick(ctx, member: discord.Member, *, reason: str = "bez důvodu"):
    if not ctx.author.guild_permissions.kick_members:
        await ctx.send("❌🙈 epik fejl! na kickování nemáš práva!")
        return

    try:
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} byl/a vyhozen/a ze serveru.\n🗒️ důvod: {reason}")
    except discord.Forbidden:
        await ctx.send("⚠️ nastala chybička! asi má vyšší roli než ty nebo já")
    except Exception as e:
        await ctx.send(f"nastala chyba: {e}")

@bot.command()
async def ban(ctx, member: discord.Member, *, reason: str = "bez důvodu"):
    if not ctx.author.guild_permissions.ban_members:
        await ctx.send("❌🙈 epik fejl! na banování nemáš práva!")
        return
    try:
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} dostal/a ban ze serveru.\n🗒️ důvod: {reason}")
    except discord.Forbidden:
        await ctx.send("⚠️ nastala chybička! asi má vyšší roli než ty nebo já")
    except Exception as e:
        await ctx.send(f"nastala chyba: {e}")

@bot.command()
async def timeout(ctx, member: discord.Member, minutes: int, *, reason: str = "bez důvodu"):
    if not ctx.author.guild_permissions.moderate_members:
        await ctx.send("❌🙈 epik fejl! na timeouty nemáš práva!")
        return
    try:
        doba = timedelta(minutes=minutes)
        await member.timeout(doba, reason=reason)
        await ctx.send(f"**{member.mention}** dostal/a timeout na **{minutes} minut**.\n🗒️ důvod: {reason}")
    except discord.Forbidden:
        await ctx.send("⚠️ nastala chybička! asi má vyšší roli než ty nebo já")
    except Exception as e:
        await ctx.send(f"nastala chyba: {e}")

@kick.error
@ban.error
@timeout.error
async def mod_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ chybí argumenty! použití:\n`prd kick @uzivatel [důvod]`\n`prd ban @uzivatel [důvod]`\n`prd timeout @uzivatel [minuty] [důvod]`")
    elif isinstance(error, BadArgument):
        await ctx.send(f"❌ nepodařilo se najít uživatele!! označ ho prosím zavináčem (@uzivatel).")

@bot.event
async def setup_hook():
    await bot.load_extension("gambling")

bot.run(token, log_handler = handler, log_level = logging.DEBUG)
