import unicodedata
import discord
import cv2
import numpy as np
import emoji
import threading
import requests
import time
import os
import re

token = "your token"
images_per_class = 15 

def remove_diacritics(input_str):
    normalized_str = unicodedata.normalize('NFD', input_str)
    ascii_str = ''.join(c for c in normalized_str if unicodedata.category(c) != 'Mn')
    return ascii_str

def remove_emoji(text):
    text = emoji.demojize(text)
    
    # useful for handling nidoran genders
    text = re.sub(r':female_sign:', 'F', text)
    text = re.sub(r':male_sign:', 'M', text)
    
    return text

def extract_pokemon_data(text):
    # regex pattern to extract level, name, and IV
    pattern = r'Level (\d+) ([^(]+) \(([\d.]+)%\)[.!]*'
    
    # extracting level, name, and IV using rregex
    match = re.search(pattern, text)
    if match:
        level = match.group(1)
        name = match.group(2).strip()
        # remove emoji from the name
        name = re.sub(r'<:[^>]+>', '', name)
        iv = match.group(3)
        return {'level': level, 'name': name.strip(), 'IV': iv}
    else:
        return None

def save(imageURL, pokemonName):
    # load the image into memory
    original_image = cv2.imdecode(np.asarray(bytearray(requests.get(
        imageURL, stream=True).raw.read()), dtype=np.uint8), cv2.IMREAD_UNCHANGED)

    # save image if total image count for pokemon is less than 15
    if os.path.exists(f"pokemons/{pokemonName}") and len(os.listdir(f"pokemons/{pokemonName}")) < images_per_class:
        cv2.imwrite(
            f"pokemons/{pokemonName}/{round(time.time())}.jpg", original_image)

        print(
            f"Downloaded {pokemonName} ({len(os.listdir(f'pokemons/{pokemonName}'))}/{images_per_class})")

    # if pokemon name doesnt exist in dataset, save it
    elif not os.path.exists(f"pokemons/{pokemonName}"):
        os.makedirs(f"pokemons/{pokemonName}")
        cv2.imwrite(
            f"pokemons/{pokemonName}/{round(time.time())}.jpg", original_image)

        print(
            f"Downloaded {pokemonName} ({len(os.listdir(f'pokemons/{pokemonName}'))}/{images_per_class})")

    return 0

class Downloader(discord.Client):
    def __init__(self):
        super().__init__(self_bot=False, guild_subscription_options=discord.GuildSubscriptionOptions.off())

    async def on_ready(self):
        await self.change_presence(status=discord.Status.dnd)
        print('Logged on as', self.user)

    async def on_message(self, message):
        if not message.guild:
            return

        if message.author.id == 716390085896962058:
            if message.content.startswith("Congratulations") and "You caught a Level" in message.content:
                # retrieve the spawn message if found
                def filter(m): return m.author != None and m.author.id == message.author.id and m.channel.id == message.channel.id and len(
                    m.embeds) > 0 and "wild pokémon has appeared!" in m.embeds[0].title

                spawn = discord.utils.find(
                    filter, reversed(list(self.cached_messages)))
                
                pokemon_name = remove_emoji(remove_diacritics(extract_pokemon_data(message.content)['name']))

                if spawn != None:
                    # save the pokemon
                    threading.Thread(target=save, args=(
                        spawn.embeds[0].image.url, pokemon_name)).start()

client = Downloader()
client.run(token)
