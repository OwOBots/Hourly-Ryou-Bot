# @Ryouhourly Twitter Bot

This is a Python script that posts a random image of Yamada Ryou from [Gelbooru](https://gelbooru.com/) to Twitter every hour.

## Prerequisites

Before running the script, you will need to install the following packages:

- `os`
- `dotenv`
- `tweepy`
- `asyncio`
- `pygelbooru`
- `requests`

You can install these packages by running:
pip install -r requirements.txt

## Setup

To use the script, you will need to set up a `.env` file containing your API keys and tokens for Gelbooru and Twitter. You can use the `.env.sample` file as a template for your own `.env` file.

To run the script, simply run:
python memefolderbot.py

The script will post a random image from Gelbooru to your Twitter account at regular intervals. You can adjust the interval by changing the value of `time.sleep()` in the `tweet()` function.

## License

This script is licensed under the [MIT License](LICENSE).


