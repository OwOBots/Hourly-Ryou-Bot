import os
import random
import time
from dotenv import load_dotenv
import tweepy
import asyncio
import aiohttp
import aiofiles
from pygelbooru import Gelbooru
#import requests
import configparser
from PIL import Image
#import hydrus_api
#import hydrus_api.utils
# config.ini should be more intuitive than editing this file directly. however, this is a bit of a pain to read so moving the globals to the 
#functions is on my todo list for now 
config = configparser.ConfigParser()
config.read('config.ini')
tags = config['gelbooru']['tags'].split(',')
exclude_tags = config['gelbooru']['exclude_tags'].split(',')
time2post = config['timer']['time2post']
status = config['status']['tweet']
directory = config['directory']['path']
#hydrus_enabled = config['hydrus-api']['enabled']
#hydrus_url = config['hydrus-api']['url']
#hydrustags = config['hydrus-api']['tags'].split(',')

#REQUIRED_PERMISSIONS = (
#    hydrus_api.Permission.IMPORT_URLS,
#    hydrus_api.Permission.IMPORT_FILES,
#    hydrus_api.Permission.ADD_TAGS,
#    hydrus_api.Permission.SEARCH_FILES,
#    hydrus_api.Permission.MANAGE_PAGES,
#)



# load the .env file so we can use the api keys
load_dotenv()

# the reason for dotenv is because leaving it in the config.ini file is a bad idea for security reasons and leagacy reasons like this
gelbooru = Gelbooru(os.getenv("GELAPI"), os.getenv("UID")) 


# should be in config.ini but twitter doesn't like outher extensions other than this so suck it
imgExtension = ["png", "jpeg", "jpg", "gif"]

# let's grab the image
async def main():
    
    # hydrus is a bitch so right now we are just going to get a random post from gelbooru
    """
    Get a random post from Gelbooru or hydrus with the given tags excluding nudity.

    :return: URL of the post as a string.
    """
    """ if hydrus_enabled:
        api_key = hydrus_api.utils.cli_request_api_key("ryobot", REQUIRED_PERMISSIONS)
        client = hydrus_api.Client(api_key)

        # Define the tags and exclude_tags
        hydrus_tags = config['hydrus-api']['tags'].split(',')

        # Define the search options
        search_options = {
            "system_inbox": True,
            "system_archive": False,
            "system_unread": False,
            "system_not_new": False,
            "system_deleted": False,
            "system_pending": False,
            "system_has_note": False,
            "system_rating": None,
            "system_source": None,
            "limit": 300,
            "sort": "random",
            "tags_checkboxes": False,
            "simple": False,
            "no_page": True
        }

        # Search for files with the specified tags
        files = client.search_files(hydrus_tags)
        if not files:
            # If there are no files, return None
            return None

        # Save the file to disk
        filename = f"{files}.{files.headers['Content-Type'].split('/')[1]}"
        path = os.path.join(directory, filename)
        with open(path, 'wb') as f:
            for chunk in files.iter_content(chunk_size=1024):
                f.write(chunk)

        return path 
          else:
"""

  
    async with aiohttp.ClientSession() as session:
        results = await gelbooru.random_post(tags=tags, exclude_tags=exclude_tags)
        ryo = str(results)
        async with session.get(ryo) as response:
            filename = os.path.basename(ryo)
            path = os.path.join(directory, filename)
            async with aiofiles.open(path, 'wb') as f:
                await f.write(await response.read())

        return path

def chooseRandomImage():
    
    """
    Randomly choose an image file from the specified directory.

    Args:
        directory (str): The directory to search for image files. Defaults to current directory.

    Returns:
        str: The filename of the randomly chosen image.
    """

    allImages = []
    for img in os.listdir(directory):
        ext = img.split(".")[len(img.split(".")) - 1]
        if (ext in imgExtension):
            allImages.append(img)
    choice = random.randint(0, len(allImages) - 1)
    chosenImage = allImages[choice]
    return chosenImage


def compress_image(path, max_size=5):
    """
    Compresses an image file to reduce its file size to less than the specified maximum size.

    Args:
        path (str): The path to the image file to be compressed.
        max_size (int, optional): The maximum file size in MB. Defaults to 5.

    Returns:
        str: The path to the compressed image file.
    """
    # Twitter hates images < 5MB and Gifs < 15MB so we compress the image to less than 5MB
    compressed_path = path

    # If the file size is already less than the specified maximum, return the original file path
    if os.path.getsize(compressed_path) <= max_size * 1024 * 1024:
        return compressed_path

    quality = 80
    while os.path.getsize(compressed_path) > max_size * 1024 * 1024:
        quality -= 10
        ext = os.path.splitext(path)[1]
        if ext.lower() == ".png":
            compressed_path = f"{os.path.splitext(path)[0]}_compressed.png"
        else:
            compressed_path = f"{os.path.splitext(path)[0]}_compressed.jpg"
        try:
            with Image.open(path) as img:
                if img.mode == "RGBA":
                    # If the image has an alpha channel, save it as a PNG to preserve the transparency
                    img.save(compressed_path, optimize=True, quality=quality)
                else:
                    # Convert the image mode to RGB before saving it as a JPEG if necessary
                    img = img.convert("RGB")
                    img.save(compressed_path, optimize=True, quality=quality)
        except OSError as e:
            # Handle the error caused by attempting to save an RGBA image as a JPEG
            if "cannot write mode RGBA as JPEG" in str(e):
                with Image.open(path) as img:
                    img = img.convert("RGB")
                    img.save(compressed_path, optimize=True, quality=quality)
            else:
                # Handle other errors by re-raising them
                raise e


        # If the quality value gets too low or the file size cannot be reduced below the maximum, break the loop
        if quality < 10 or os.path.getsize(compressed_path) >= os.path.getsize(path):
            compressed_path = path
            break

    return compressed_path

#this starts the bot
def tweet():
    """
    Tweet function that posts an image to Twitter and waits for an hour before posting again,
    unless the compressed image file size is greater than 5MB, in which case it skips the tweet and
    continues to the next iteration.
    :return: None
    """
    
    # twitter api keys will be loaded from the .env file
    
    auth = tweepy.OAuth1UserHandler(
       os.getenv("TWITTER_APIKEY"),
       os.getenv("TWITTER_APISECRET"),
       os.getenv("ACCESS_TOKEN"),
       os.getenv("ACCESS_TOKENSECRET"),
       os.getenv("BEAR")
    )
    
    api = tweepy.API(auth)
    while True:
        
        try:
            # path lets us get a random image without restarting the bot
            path = asyncio.run(main())  # Get a random image from Gelbooru
            compressed_path = compress_image(path)  # Compress the image
            print("Compressed file path:", compressed_path)

            # If the compressed file is larger than 5MB, skip the tweet and continue to the next iteration
            if os.path.getsize(compressed_path) > 5 * 1024 * 1024:
            #DONT UNCOMMENT THIS IT WAS JUST FOR TESTING
            #if os.path.getsize("invalid_path") > 5 * 1024 * 1024:
                print(f"Skipping tweet because compressed file size is {os.path.getsize(compressed_path) / (1024 * 1024):.2f} MB")
                os.remove(compressed_path)  # Delete the compressed image file
                print("Deleted compressed file:", compressed_path)
                continue
            # if the image is gif, set the media category
            media_category = "tweet_gif" if compressed_path.endswith(".gif") else None
            
            
            media = api.media_upload(compressed_path, chunked=True ,media_category=media_category)
            status_text = None if status.strip() == '' else status  # Set status_text to None if status is blank
            post_result = api.update_status(status=status_text, media_ids=[media.media_id_string])
            #we delete the compressed image because it's no longer needed and storage is expensive
            os.remove(compressed_path)  # Delete the compressed image file
            print("Deleted compressed file:", compressed_path)
            print("Tweeted!")
            #TODO: how to fucking sync the bot so if i restart the bot it doesn't post again until the hour has passed
            print("Now sleeping for 1 hour...")
            time.sleep(int(time2post))  # int the time2post variable because it's a string and needs to be converted to an int because config.ini only accepts strings
        # Keep going if an error occurs
        except Exception as e:
            print("Error occurred:", e)
            print("Retrying in 30 seconds...")
            time.sleep(30)
            continue




if __name__ == "__main__":
    tweet()