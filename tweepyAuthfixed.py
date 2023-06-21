import tweepy
import webbrowser
import os


# stolen from https://gitlab.com/mocchapi/tweepyauth/
# god dammit (lis)anne why didn't you update this in the first place
# it was just adding 1 extra argument to the function
def auto_authenticate(tokenfile='twitter_tokens.txt', keyfile='twitter_keys.txt', silent=False):
    if os.path.isfile(keyfile):
        if not silent: print('loading twitter_keys.txt')
        with open(keyfile, 'r') as f:
            keys = list(f.read().split(','))
            auth = tweepy.OAuthHandler(keys[0], keys[1], callback="oob")
    else:
        print(keyfile + ' doesnt exist')
        keys = [input('consumer API key:'), input('consumer API secret key:')]
        try:
            auth = tweepy.OAuthHandler(keys[0], keys[1], callback="oob")
        except BaseException as e:
            print('keys invalid:', e)
            return None
        try:
            with open(keyfile, 'w') as f:
                f.write(','.join(keys))
        except BaseException as e:
            print(f'error writing {keyfile}:', e)
            os.remove(keyfile)
            return None

    if os.path.isfile(tokenfile):
        if not silent: print('loading ' + tokenfile)
        try:
            with open(tokenfile, 'r') as f:
                tokens = list(f.read().split(','))
                auth.set_access_token(tokens[0], tokens[1])
                if not silent: print('all done')
                return tweepy.API(auth)
        except BaseException as e:
            print('tweepyauth error:', e)
            return None
    else:
        if not silent: print(tokenfile + ' doesnt exist, creating now...')
        auth = authenticate(keys[0], keys[1])
        return verify(auth, tokenfile)


def authenticate(consumer_token, consumer_secret):
    auth = tweepy.OAuthHandler(consumer_token, consumer_secret, callback="oob")
    try:
        redirect_url = auth.get_authorization_url()
        print(redirect_url)
        try:
            webbrowser.open(redirect_url, new=0)
        except:
            pass
        print('opening broswer window, please log in')
        return auth
    except tweepy.TweepError:
        print('Error! Failed to authorize.')


def verify(auth, tokenfile, verifier=None):
    if verifier == None:
        verifier = input('Verifier: ')
    try:
        access_tokens = auth.get_access_token(verifier)
        token_key = access_tokens[0]
        token_secret = access_tokens[1]
        auth.set_access_token(token_key, token_secret)
        with open(tokenfile, 'w') as f:
            f.write(f'{token_key},{token_secret}')
    except tweepy.TweepError:
        print('Error! Failed to get access token.')
        return None
    api = tweepy.API(auth)
    return api


if __name__ == '__main__':
    api = auto_authenticate()
    print(api.home_timeline()[0])
