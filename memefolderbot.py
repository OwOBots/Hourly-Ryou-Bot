import os
import random
import time
from dotenv import load_dotenv
import tweepy
import asyncio
from pygelbooru import Gelbooru
import requests
import configparser
from PIL import Image
config = configparser.ConfigParser()
config.read('config.ini')
tags = config['gelbooru']['tags'].split(',')
exclude_tags = config['gelbooru']['exclude_tags'].split(',')

load_dotenv()
gelbooru = Gelbooru(os.getenv("GELAPI"), os.getenv("UID"))

async def main():
    """
    Get a random post from Gelbooru with the given tags excluding nudity.

    :return: URL of the post as a string.
    """

    results = await gelbooru.random_post(tags=tags, exclude_tags=exclude_tags)
    ryo = str(results)
    response = requests.get(ryo)

    filename = os.path.basename(ryo)
    directory = '.'
    path = os.path.join(directory, filename)
    with open(path, 'wb') as f:
        f.write(response.content)
    return path

def chooseRandomImage(directory="."):
    """
    Randomly choose an image file from the specified directory.

    Args:
        directory (str): The directory to search for image files. Defaults to current directory.

    Returns:
        str: The filename of the randomly chosen image.
    """
    imgExtension = ["png", "jpeg", "jpg", "gif"]
    allImages = []
    for img in os.listdir(directory):
        ext = img.split(".")[len(img.split(".")) - 1]
        if (ext in imgExtension):
            allImages.append(img)
    choice = random.randint(0, len(allImages) - 1)
    chosenImage = allImages[choice]
    return chosenImage

def compress_image(path, quality=80):
    """
    Compresses an image file to reduce its file size.

    Args:
        path (str): The path to the image file to be compressed.
        quality (int, optional): The compression quality to use (0-100). Defaults to 80.

    Returns:
        str: The path to the compressed image file.
    """
    with Image.open(path) as img:
        img.save(path, optimize=True, quality=quality)
    return path

def tweet():
    """
    Tweet function that posts an image to Twitter and waits for an hour before posting again,
    unless the compressed image file size is greater than 5MB, in which case it skips the wait.
    :return: None
    """
    auth = tweepy.OAuth1UserHandler(
       os.getenv("TWITTER_APIKEY"),
       os.getenv("TWITTER_APISECRET"),
       os.getenv("ACCESS_TOKEN"),
       os.getenv("ACCESS_TOKENSECRET"),
       os.getenv("BEAR")
    )

    api = tweepy.API(auth)

def tweet():
    """
    Tweet function that posts an image to Twitter and waits for an hour before posting again.
    :return: None
    """
    auth = tweepy.OAuth1UserHandler(
       os.getenv("TWITTER_APIKEY"),
       os.getenv("TWITTER_APISECRET"),
       os.getenv("ACCESS_TOKEN"),
       os.getenv("ACCESS_TOKENSECRET"),
       os.getenv("BEAR")
    )

    api = tweepy.API(auth)

    while True:
        path = asyncio.run(main())  # Get a random image from Gelbooru
        compressed_path = compress_image(path)  # Compress the image
        print("Compressed file path:", compressed_path)
        media = api.media_upload(compressed_path,chunked=True)
        post_result = api.update_status(status=None, media_ids=[media.media_id_string])
        os.remove(compressed_path)  # Delete the compressed image file
        print("Deleted compressed file:", compressed_path)
        print("Tweeted! Now sleeping for 1 hour...")
        time.sleep(3600) # 3600 seconds = 1 hour


if __name__ == "__main__":
    tweet()