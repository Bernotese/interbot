from decouple import config
from interactions import slash_command, slash_option, SlashContext, OptionType
from interactions import Client, Intents, listen
from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List
from interactions import Embed, StringSelectMenu

key = config('API_KEY')

bot = Client(intents=Intents.DEFAULT)

##################################
##         Datenbanken          ##
##################################

# "Players" ist die Datenbank für die Speicherung aller Spieler da. 
class Players(Document):
    discord_id: int # Discord UserID
    name: str # Anzeigename - wählbar vom User
    elo: int # Anzahl der Elopunkte [1-20]
    wins: int # Anzahl der gewonnen Spiele
    losses: int # Anzahl der verlorenen Spiele 

class Games(Document):
    members: List[str] # Alle "joined" Players
    team1: List[str] # Spieler in Team1
    team2: List[str] # Spieler in Team2
    winner: str # Wer hat gewonnen? team1/team2
    game_running: bool # 1 game running / 0 game over

##################################
##         Funktionen           ##
##################################

async def check_player_exits(discord_id):
    player = await Players.find_one({"discord_id": int(discord_id)})
    s_player = str(player)
    return s_player is not None

async def get_player_by_discord_id(discord_id):
    player = await Players.find_one({"discord_id": discord_id})
    return player

async def check_games_status():
    running_game = await Games.find_one({"game_running": True})
    print(running_game)
    return running_game is not None

async def get_active_game():
    game = await check_games_status()
    game.id

async def get_all_active_members_names():
    active_game = await Games.find_one({"game_running": True})
    members = active_game.members
    return members

##################################
##         Commands             ##
##################################

@slash_command(
        name="newplayer", 
        description="Add new player | <Name> <Elo>"
)
@slash_option(
    name="name",
    description="Display Name",
    required=True,
    opt_type=OptionType.STRING
)
@slash_option(
    name="elo_points",
    description="Elopoints",
    required=True,
    opt_type=OptionType.INTEGER,
    min_value=1,
    max_value=20
)
async def newpalyer(ctx: SlashContext, name: str, elo_points: int):
    # Erstellt einen neune Spieler (anlegen eines neuen Spielers)

    discord_id = ctx.author.id

    if await check_player_exits(discord_id):
        await ctx.send(f"Hi {name}, du wurdest bereits angelegt.", ephemeral=True)
    else:
        player = Players(discord_id=int(discord_id), name=name, elo=elo_points, wins=0, losses=0)
        await player.insert()
        await ctx.send(f"Hi {name}, du wurdest mit einer Start-Elo von {str(elo_points)} angelegt.", ephemeral=True)

@slash_command(
        name="newgame",
        description="star new game"
)
async def newgame(ctx: SlashContext):
    # Startet eine neue Runde
    if await check_games_status():
        await ctx.send(f"Beende erst das letzte Spiel.", ephemeral=True)
        return
    else:
        new_game = Games(members=[], team1=[], team2=[], winner="0", game_running=1)
        await new_game.insert()
        await ctx.send(f"Neues Spiel wurde erstellt.")

@slash_command(
        name="join",
        description="Join a new game"
)
async def joingame(ctx: SlashContext):
    # Join einer bestehenden runde
    discord_id = str(ctx.author.id)
    
    print(type(discord_id))

    current_game = await Games.find_one({"game_running": True})
    print(current_game)

    player = await check_player_exits(discord_id)
    print(player)

    if not player:
        await ctx.send("Lege dich erst an mit /newplayer", ephemeral=True)
        return
    else:
        if not current_game:
            await ctx.send("Erstelle erst ein neues Spiel", ephemeral=True)
            return
        if discord_id in current_game.members:
            await ctx.send("Du bist bereits beigetreten", ephemeral=True)
            return
        else:
            current_game.members.append(str(discord_id))
            print (type(current_game.members))
            print(current_game.members)
            await current_game.save()
            await ctx.send("Du bist dem Spiel beigetreten", ephemeral=True)

@slash_command(name="startgame", description="start the game")
async def startgame(ctx: SlashContext):
    game_members_ids = await get_all_active_members_names()
    game_members = []
    for discord_id in game_members_ids:
        player = await get_player_by_discord_id(int(discord_id))
        name = player.name
        elo = player.elo
        value = (name, elo)
        game_members.append(value)

    game_info = Embed(title="Neues Spiel")
    game_info.set_thumbnail("https://upload.wikimedia.org/wikipedia/commons/1/1a/Faker_2020_interview.jpg")
    game_info.description = f"Es wurden {str(len(game_members))} Teilnehmer gefunden."

    print(game_members)

    clear_names = []
    clear_elo = []
    for p in game_members:
        print(p)
        print(p[0])
        clear_names.append("".join(str(p[0]) + "\n"))
        clear_elo.append(str(p[1]).join("\n"))
        
    game_info.add_field(name="Spieler:", value=str(clear_names))
    game_info.add_field(name="Elo:", value=str(clear_elo))
    
    await ctx.send(embed=game_info)

    # components = [
    #     StringSelectMenu("Variation 1", "Variation 2", placeholder="Variation:", min_values=1, max_values=1),
    # ]

    # await ctx.send(embed=members, components=components)

    # Je nach auswahl Runde Starten mit den Verschiedenen Teams
    # Neuer Post mit dem Finalen Team
    # User in die jeweiligen Channel moven

@slash_command(name="test", description="test")
async def test(ctx: SlashContext):
    embed = Embed(title="Ich bin ein Embed")
    embed.description = "Hier können afaik 4000 Zeichen drin stehen"
    embed.set_thumbnail("https://upload.wikimedia.org/wikipedia/commons/1/1a/Faker_2020_interview.jpg")

    embed.add_field(name="field1", value="value1", inline=True)
    embed.add_field(name="field2", value="value2", inline=True)
    embed.add_field(name="field3", value="value3", inline=True)

    await ctx.send(embed=embed)

@listen()  # this decorator tells snek that it needs to listen for the corresponding event, and run this coroutine
async def on_ready():
    # This event is called when the bot is ready to respond to commands
    mongo_client = AsyncIOMotorClient("mongodb://10.0.0.40:27017/")  # Ersetze die Verbindungs-URL entsprechend deiner MongoDB-Instanz
    await init_beanie(database=mongo_client.intbot, document_models=[Games])
    await init_beanie(database=mongo_client.intbot, document_models=[Players])
    print("Ready")
    print(f"This bot is owned by {bot.owner}")


@listen()
async def on_message_create(event):
    # This event is called when a message is sent in a channel the bot can see
    print(f"message sent: {event.message.content}")

bot.start(str(key))