import os
import random
import time
from dotenv import load_dotenv
import tweepy
import asyncio
from pygelbooru import Gelbooru
import requests


load_dotenv()
gelbooru = Gelbooru(os.getenv("GELAPI"), os.getenv("UID"))

async def main():
    """
    Get a random post from Gelbooru with the given tags excluding nudity.

    :return: URL of the post as a string.
    """

    results = await gelbooru.random_post(tags=['yamada ryou', '1girl'], exclude_tags=['nude','gotou hitori','ijichi nijika ','kita ikuyo'])
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
        media = api.media_upload(path,chunked=True)
        post_result = api.update_status(status=None, media_ids=[media.media_id_string])
        os.remove(path)
        print("Tweeted! Now sleeping for 1 hour...")
        time.sleep(3600) # 3600 seconds = 1 hour


if __name__ == "__main__":
    tweet()
