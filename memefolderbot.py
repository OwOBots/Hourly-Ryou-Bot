import os
import random
import time
from dotenv import load_dotenv
import tweepy
import asyncio
import aiohttp
import aiofiles
from pygelbooru import Gelbooru
import requests
import configparser
from PIL import Image
import hydrus_api
import hydrus_api.utils
import datetime
import sys
# config.ini should be more intuitive than editing this file directly. however, config.ini is a going to be a mess if
# we keep adding shit so it's better to ""feature lock"" this for the moment
# config.ini should be minimal and readable and should be easy to edit and maintain.
# it should be in the same directory as this script and should be a .ini file that can be edited in a text editor
# if not, errors will occur and the script will not run
# (duh)

# check if config.ini exists and if not, call the user a dumbass and exit
if not os.path.exists('config.ini'):
    # lmao pycharm thinks dumbass is a typo
    # i need to hide traceback from the user only on this error and not on the entire script itself
    sys.tracebacklimit = 0
    # print is unnecessary but funny to me so i'm going to keep it here
    print('Dont delete config.ini Dumbass')
    raise FileNotFoundError('config.ini')
else:
    config = configparser.ConfigParser()
    config.read('config.ini')
    # path to an image directory to use for importing images from Gelbooru or hydrus with the given tags excluding
    # nudity
    directory = config['directory']['path']

# required permissions for hydrus https://gitlab.com/cryzed/hydrus-api I don't think this is the best way to do this.
# We should move this to config.ini and use it but config.ini is going to be bloated if I do that, so I'll leave it
# as is here for now
REQUIRED_PERMISSIONS = (
    hydrus_api.Permission.IMPORT_URLS,
    hydrus_api.Permission.IMPORT_FILES,
    hydrus_api.Permission.ADD_TAGS,
    hydrus_api.Permission.SEARCH_FILES,
    hydrus_api.Permission.MANAGE_PAGES,
)

# load the .env file, so we can use the api keys
load_dotenv()


# Why did i make this async? maybe it can be done synchronously? I'm not sure and im not going to do that
# because it works fine atm, but it's probably not the best way to do this. so  just leave it future me
async def main():
    """
    Get a random post from Gelbooru or hydrus with the given tags excluding nudity.

    :return: URL of the post as a string.
    """
    # config.ini setup
    hydrus_enabled = True if config['hydrus-api']['enabled'].lower() == 'true' else False
    if hydrus_enabled:
        # I would like to save the api key to the .env file, so we don't have to make a new file for one third-party
        # api but im afraid of overwriting .env file with just the hydrus api key and removing the twitter keys,
        # so I'm going to save the api key to a file and load it from there instead
        # the hydrus api key should be local to your computer if you're running this on a computer
        # so its nbd to send the api key in a git repo  BUT if you're running hydrus on a server you'll need to
        # keep the api key secret (duh).
        # fun fact: hydrus api key is only needed for downloading images from a client the problem is that
        # the avg user uses hydrus locally and this is halfway to useless too them however, hydrus server exists, so
        # if a user uses a "public" server they'll need to have a hydrus api key.
        if not os.path.exists('hydrus_api_key.secret'):
            api_key = hydrus_api.utils.cli_request_api_key("ryobot", REQUIRED_PERMISSIONS)
            # save api key to file locally
            with open('hydrus_api_key.secret', 'w') as f:
                f.write(api_key)
            # create a client with the api key we just saved
            reading_key = open('hydrus_api_key.secret', 'r')
            # convert the api key to a string
            local_api_key = reading_key.read()
            client = hydrus_api.Client(local_api_key)
        else:
            # load api key from file
            reading_key = open('hydrus_api_key.secret', 'r')
            local_api_key = reading_key.read()
            client = hydrus_api.Client(local_api_key)

        # Define the tags and exclude_tags
        hydrustags = config['booru']['tags'].split(',')

        # Search for files with the specified tags

        files = client.search_files(tags=hydrustags, return_file_ids=True)
        if not files:
            # No files found with the specified tags
            return None
        # randomly select a file from the list of files found with the specified tags
        # fun fact: this took way to long to figure out
        file_id = random.choice(files['file_ids'])
        img = client.get_file(file_id=file_id)

        # Save the file to disk
        filename = f"{img}.{img.headers['Content-Type'].split('/')[1]}"
        path = os.path.join(directory, filename)
        with open(path, 'wb') as f:
            for chunk in img.iter_content(chunk_size=1024):
                f.write(chunk)

        return path
    else:

        # config.ini exists use that instead of hard coding tags+urls
        booru_url = config['booru']['url']
        tags = config['booru']['tags'].split(',')
        exclude_tags = config['booru']['exclude_tags'].split(',')

    # let's grab the image
    if booru_url is None or booru_url == "":
        # gelbooru is the default api so let's assume the user uses it. if not
        # then go use the generic api
        gelbooru = Gelbooru(os.getenv("GELAPI"), os.getenv("UID"))
        async with aiohttp.ClientSession() as session:
            results = await gelbooru.random_post(tags=tags, exclude_tags=exclude_tags)
            ryo = str(results)
            async with session.get(ryo) as response:
                filename = os.path.basename(ryo)
                path = os.path.join(directory, filename)
                async with aiofiles.open(path, 'wb') as f:
                    await f.write(await response.read())

                return path

    else:
        # generic booru api key because there's more than one booru out there
        # if the user has a custom api key then use that
        # most boorus don't use api keys so leaving it blank is fine
        genbooru = Gelbooru(os.getenv("BOORUAPI"), os.getenv("BOORUUID"), api=booru_url)
        async with aiohttp.ClientSession() as session:
            results = await genbooru.random_post(tags=tags, exclude_tags=exclude_tags)
            ryo = str(results)
            async with session.get(ryo) as response:
                filename = os.path.basename(ryo)
                path = os.path.join(directory, filename)
                async with aiofiles.open(path, 'wb') as f:
                    await f.write(await response.read())

        return path


# we don't use this no more, but it can be useful if you want to get a random image locally
# id like to add this to config.ini but i don't think adding more else if statements is a good idea
# this far down the line
""" 
    def chooseRandomImage():
    
    # should be in config.ini but twitter doesn't like other extensions other than this so suck it
    imgExtension = ["png", "jpeg", "jpg", "gif"]

    allImages = []
    for img in os.listdir(directory):
        ext = img.split(".")[len(img.split(".")) - 1]
        if (ext in imgExtension):
            allImages.append(img)
    choice = random.randint(0, len(allImages) - 1)
    chosenImage = allImages[choice]
    return chosenImage 
"""


def compress_image(path, max_size=5):
    """
    Compresses an image file to reduce its file size to less than the specified maximum size.

    Args:
        path (str): The path to the image file to be compressed.
        max_size (int, optional): The maximum file size in MB. Defaults to 5.

    Returns:
        str: The path to the compressed image file.
    """

    # Twitter hates images < 5MB and Gifs < 15MB, so we compress the image to less than 5MB
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


# this starts the bot
def tweet():
    """
    Tweet function that posts an image to Twitter and waits for an hour before posting again,
    unless the compressed image file size is greater than 5MB, in which case it skips the tweet and
    continues to the next iteration.
    :return: None
    """

    # Twitter api keys will be loaded from the .env file
    # pycharm thinks these are typos, so ignore pycharm for now
    debug = config['debug']['enabled']
    auth = tweepy.OAuth1UserHandler(
        os.getenv("TWITTER_APIKEY"),
        os.getenv("TWITTER_APISECRET"),
        os.getenv("ACCESS_TOKEN"),
        os.getenv("ACCESS_TOKENSECRET"),
        os.getenv("BEAR")
    )
    status = config['status']['tweet']
    time2post = config['timer']['time2post']
    # let's convert the time to post to a proper date, so we can send the time to a print statement
    # I want to use this for a countdown to the next post, but I don't know how to do that yet.
    converted = str(datetime.timedelta(seconds=int(time2post)))
    api = tweepy.API(auth)
    # lets the user know we're logging in
    print("logging in...")

    # Debug mode doesn't clear the console, so we can debug...

    if config.getboolean('debug', 'enabled'):
        print("DEBUG MODE ENABLED CONSOLE WILL NOT BE CLEARED")
        # 2hu
        print("Girls are now praying, please wait warmly...")
        while True:

            try:
                # path lets us get a random image without restarting the bot
                path = asyncio.run(main())  # Get a random image from Gelbooru
                compressed_path = compress_image(path)  # Compress the image
                print("Compressed file path:", compressed_path)

                # If the compressed file is larger than 5MB, skip the tweet and continue to the next iteration
                if os.path.getsize(compressed_path) > 5 * 1024 * 1024:
                    print(
                        f"Skipping tweet because compressed file size is {os.path.getsize(compressed_path) / (1024 * 1024):.2f} MB")
                    os.remove(compressed_path)  # Delete the compressed image file
                    print("Deleted compressed file:", compressed_path)
                    continue
                # if the image is gif, set the media category
                media_category = "tweet_gif" if compressed_path.endswith(".gif") else None
                # i don't really remember  why chunked is needed, but it works fine for now
                media = api.media_upload(compressed_path, chunked=True, media_category=media_category)
                status_text = None if status.strip() == '' else status  # Set status_text to None if status is blank
                post_result = api.update_status(status=status_text, media_ids=[media.media_id_string])
                # we delete the compressed image because it's no longer needed and storage is expensive
                os.remove(compressed_path)  # Delete the compressed image file
                print("Deleted compressed file:", compressed_path)
                print("Tweeted!")
                print("Now sleeping for", converted)
                time.sleep(int(time2post))
                # int the time2post variable because it's a string and needs to be converted to
                # an int because config.ini only accepts strings
            # Keep going if an error occurs
            except Exception as e:
                print("Error occurred:", e)
                print("Retrying in 30 seconds...")
                time.sleep(30)
                continue
    else:
        print("Girls are now praying, please wait warmly...")
        while True:

            try:
                # clear the console so we can read the output.
                os.system('cls' if os.name == 'nt' else 'clear')

                # path lets us get a random image without restarting the bot
                path = asyncio.run(main())  # Get a random image from Gelbooru
                compressed_path = compress_image(path)  # Compress the image
                print("Compressed file path:", compressed_path)

                # If the compressed file is larger than 5MB, skip the tweet and continue to the next iteration
                if os.path.getsize(compressed_path) > 5 * 1024 * 1024:
                    # DON'T UNCOMMENT THIS IT WAS JUST FOR TESTING
                    # if os.path.getsize("invalid_path") > 5 * 1024 * 1024:
                    # i feel like this is a unnecessary check but just in case
                    print(f"Skipping tweet because compressed file size is {os.path.getsize(compressed_path) / (1024 * 1024):.2f} MB")
                    os.remove(compressed_path)  # Delete the compressed image file
                    print("Deleted compressed file:", compressed_path)
                    continue
                # if the image is gif, set the media category
                media_category = "tweet_gif" if compressed_path.endswith(".gif") else None

                media = api.media_upload(compressed_path, chunked=True, media_category=media_category)
                status_text = None if status.strip() == '' else status  # Set status_text to None if status is blank
                post_result = api.update_status(status=status_text, media_ids=[media.media_id_string])
                # we delete the compressed image because it's no longer needed and storage is expensive
                os.remove(compressed_path)  # Delete the compressed image file
                print("Deleted compressed file:", compressed_path)
                print("Tweeted!")
                print("Now sleeping for", converted)
                time.sleep(int(time2post))
                # int the time2post variable because it's a string and needs to be converted to
                # an int because config.ini only accepts strings
            # Keep going if an error occurs
            except Exception as e:
                print("Error occurred:", e)
                print("Retrying in 30 seconds...")
                time.sleep(30)
                continue


if __name__ == "__main__":
    tweet()
