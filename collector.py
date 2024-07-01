import os
import re
import cv2
import time
import emoji
import discord
import requests
import threading
import unicodedata
import numpy as np
from discord_webhook import DiscordWebhook, DiscordEmbed

WB_URL = "Discord Log Webhook URL"
token = "Discord Account Token"
images_per_class = 90 # Number OF Images Per Pokemon Class

total_pokemon_count = 0


def discord_log(pokemon, count, total, url):
    webhook = DiscordWebhook(
        url=WB_URL,
        username="Pokemon Collector",
        avatar_url="https://i.imgur.com/4M34hi2.png",
    )

    embed = DiscordEmbed(
        title="Pokemon Data Collector",
        description=f"Pokemon Data Collected : {pokemon} \nPokemon Count : {count}\n\nTotal Collection : {total}",
        color=242424,
    )

    if url:
        embed.set_image(url=url)

    webhook.add_embed(embed)
    response = webhook.execute()


def remove_diacritics(input_str):
    normalized_str = unicodedata.normalize("NFD", input_str)
    ascii_str = "".join(c for c in normalized_str if unicodedata.category(c) != "Mn")
    return ascii_str


def remove_emoji(text):
    text = emoji.demojize(text)
    text = re.sub(r':female_sign:', 'F', text)
    text = re.sub(r':male_sign:', 'M', text)
    text = text.replace("<", "")
    return text


def extract_pokemon_name(text):
    pattern_with_iv = r"Level (\d+) (.+?):(male|female|unknown) \(([\d.]+)%\)"
    pattern_without_iv = r"Level (\d+) (.+?):(male|female|unknown)"

    match = re.search(pattern_with_iv, text) or re.search(pattern_without_iv, text)
    if match:
        name = match.group(2).strip()
        return name
    return None


def save(imageURL, pokemonName):
    global total_pokemon_count

    original_image = cv2.imdecode(
        np.asarray(
            bytearray(requests.get(imageURL, stream=True).raw.read()), dtype=np.uint8
        ),
        cv2.IMREAD_UNCHANGED,
    )

    if (
        os.path.exists(f"pokemons/{pokemonName}")
        and len(os.listdir(f"pokemons/{pokemonName}")) < images_per_class
    ):
        cv2.imwrite(f"pokemons/{pokemonName}/{round(time.time())}.jpg", original_image)

        print(
            f"+ Downloaded {pokemonName} ({len(os.listdir(f'pokemons/{pokemonName}'))}/{images_per_class})"
        )

        count = len(os.listdir(f"pokemons/{pokemonName}"))
        total_pokemon_count += 1
        discord_log(pokemonName, count=count, total=total_pokemon_count, url=imageURL)

    elif not os.path.exists(f"pokemons/{pokemonName}"):
        os.makedirs(f"pokemons/{pokemonName}")
        cv2.imwrite(f"pokemons/{pokemonName}/{round(time.time())}.jpg", original_image)

        print(
            f"+ Downloaded {pokemonName} ({len(os.listdir(f'pokemons/{pokemonName}'))}/{images_per_class})"
        )

        count = len(os.listdir(f"pokemons/{pokemonName}"))
        total_pokemon_count += 1
        discord_log(pokemonName, count=count, total=total_pokemon_count, url=imageURL)

    return 0


class Downloader(discord.Client):
    def __init__(self):
        super().__init__(self_bot=False)

    async def on_ready(self):
        print("+ Logged In As : ", self.user)

    async def on_message(self, message):
        if not message.guild:
            return

        if message.author.id == 716390085896962058:
            if (
                message.content.startswith("Congratulations")
                and "You caught a Level" in message.content
            ):

                def filter(m):
                    return (
                        m.author != None
                        and m.author.id == message.author.id
                        and m.channel.id == message.channel.id
                        and len(m.embeds) > 0
                        and "wild pokémon has appeared!" in m.embeds[0].title
                    )

                spawn = discord.utils.find(filter, reversed(list(self.cached_messages)))

                if spawn == None:
                    return

                pokemon_name = extract_pokemon_name(message.content)

                if pokemon_name:
                    pokemon_name = remove_emoji(remove_diacritics(pokemon_name))

                    threading.Thread(
                        target=save, args=(spawn.embeds[0].image.url, pokemon_name)
                    ).start()

                else:
                    print("+ Unable To Extract Pokemon Data")

                    webhook = DiscordWebhook(
                        url=WB_URL,
                        username="Pokemon Collector",
                        avatar_url="https://i.imgur.com/4M34hi2.png",
                    )

                    embed = DiscordEmbed(
                        title="ERROR",
                        description=f"Unable To Extract Pokemon Data From : \n\n{message.content}",
                        color=242424,
                    )

                    webhook.add_embed(embed)
                    response = webhook.execute()
                    

client = Downloader()
client.run(token)