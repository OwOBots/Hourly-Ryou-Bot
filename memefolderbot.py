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
time2post = config['timer']['time2post']
status = config['status']['tweet']

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

def compress_image(path, max_size=5):
    """
    Compresses an image file to reduce its file size to less than the specified maximum size.

    Args:
        path (str): The path to the image file to be compressed.
        max_size (int, optional): The maximum file size in MB. Defaults to 5.

    Returns:
        str: The path to the compressed image file.
    """
    compressed_path = path

    # If the file size is already less than the specified maximum, return the original file path
    if os.path.getsize(compressed_path) <= max_size * 1024 * 1024:
        return compressed_path

    quality = 80

    # Iteratively compress the image with lower quality values until the file size is less than the specified maximum
    while os.path.getsize(compressed_path) > max_size * 1024 * 1024:
        quality -= 10
        compressed_path = f"{os.path.splitext(path)[0]}_compressed.jpg"
        with Image.open(path) as img:
            # Convert the image mode to RGB before saving it as a JPEG
            if img.format != 'PNG':
                img = img.convert('RGB')
            img.save(compressed_path, optimize=True, quality=quality)


        # If the quality value gets too low or the file size cannot be reduced below the maximum, break the loop
        if quality < 10 or os.path.getsize(compressed_path) >= os.path.getsize(path):
            compressed_path = path
            break

    return compressed_path

def tweet():
    """
    Tweet function that posts an image to Twitter and waits for an hour before posting again,
    unless the compressed image file size is greater than 5MB, in which case it skips the tweet and
    continues to the next iteration.
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

        # If the compressed file is larger than 5MB, skip the tweet and continue to the next iteration
        if os.path.getsize(compressed_path) > 5 * 1024 * 1024:
            print(f"Skipping tweet because compressed file size is {os.path.getsize(compressed_path) / (1024 * 1024):.2f} MB")
            os.remove(compressed_path)  # Delete the compressed image file
            print("Deleted compressed file:", compressed_path)
            continue

        media = api.media_upload(compressed_path, chunked=True)
        status_text = None if status.strip() == '' else status  # Set status_text to None if status is blank
        post_result = api.update_status(status=status_text, media_ids=[media.media_id_string])
        os.remove(compressed_path)  # Delete the compressed image file
        print("Deleted compressed file:", compressed_path)
        print("Tweeted!")
        print("Now sleeping for 1 hour...")
        
        time.sleep(int(time2post))  # 3600 seconds = 1 hour



if __name__ == "__main__":
    tweet()