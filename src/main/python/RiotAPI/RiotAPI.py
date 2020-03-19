import logging
import json
import sys
from collections import defaultdict

import requests

from utils import KDA

logger = logging.getLogger('app.RiotAPI.RiotAPI')

# API Key
API_KEY = None

# Queue Types
_queues_raw = None
try:
    qr = requests.get('http://static.developer.riotgames.com/docs/lol/queues.json')
    if qr.status_code != 200:
        raise ConnectionError
    _queues_raw = qr.json()
except:
    raise IOError('No queues.json file')
    logger.warning('Could not reach Riot for queues file. Falling back on local...')
    with open('RiotAPI/queues.json') as qf:
        _queues_raw = json.load(qf)

ALL_QUEUE_TYPES = {}
for info in _queues_raw:
    try:
        if 'deprecated' in info['notes'].lower():
            continue
    except AttributeError:
        pass
    try:
        desc = info['description'].replace('games', '').strip()
    except AttributeError:
        desc = 'Custom'
    ALL_QUEUE_TYPES[desc] = info['queueId']

_popular_queue_types = {'Custom', '5v5 ARAM', '5v5 Draft Pick', '5v5 Ranked Solo', '5v5 Blind Pick', '5v5 Ranked Flex'}
QUEUE_TYPES = {k: v for k, v in ALL_QUEUE_TYPES.items() if k in _popular_queue_types}

if len(_popular_queue_types) != len(QUEUE_TYPES):
    logger.warning('Gamemode listed in _popular_queue_types not found in ALL_QUEUE_TYPES', file=sys.stderr)

# Riot API Requester
class RiotApiRequester:
    def __init__(self, API_KEY, region):
        self.API_KEY = API_KEY
        self.region = region
        self.logger = logging.getLogger('app.RiotAPI.RiotAPI.RiotApiRequester')

    def dump_response(self, r):
        msg = f'HTTP Response:\n\t{r}\n\t{r.status_code}\n\t{r.headers}\n\t'
        try:
            msg += r.json()
        except:
            msg += r.content.decode('utf-8')
        self.logger.critical(msg)

    def get(self, url, **kwargs):
        req = f'https://{self.region}.api.riotgames.com{url}?api_key={API_KEY}'
        for arg, vals in kwargs.items():
            for val in vals:
                req += f'&{arg}={val}'
        self.logger.info(f'Make GET request: "{req}"')
        r = requests.get(req)
        if r.status_code != 200:
            self.logger.critical(f'Failed GET Request')
            self.dump_response(r)
            raise Exception('Invalid request')
        return r

# Console application - used for testing
def main():
    summoner = input('Enter summoner to search for: ')
    region = input('Enter region to search for (default NA1): ')
    matches = input('Enter number of matches to look up (default 10): ')
    queues = map(lambda x: x.strip(), input(
        'Enter queue types to search for (default any): ').split(','))

    if region == '':
        region = 'na1'

    if matches == '':
        matches = '10'

    RAR = RiotApiRequester(API_KEY, region)

    summoner_r = RAR.get(f'/lol/summoner/v4/summoners/by-name/{summoner}')
    account_eid = summoner_r.json()['accountId']

    matches_r = RAR.get(
        f'/lol/match/v4/matchlists/by-account/{account_eid}', endIndex=[matches], queue=queues)
    matches = matches_r.json()['matches']

    player_kdas = defaultdict(lambda: [0, KDA()])

    for match in matches:
        match_r = RAR.get(f'/lol/match/v4/matches/{match["gameId"]}')

        players = match_r.json()['participantIdentities']
        players = dict([(player['participantId'], player['player']
                         ['summonerName']) for player in players])

        player_data = match_r.json()['participants']

        for player in player_data:
            summoner_name = players[player['participantId']]
            player_kdas[summoner_name][0] += 1
            for val in ('kills', 'deaths', 'assists'):
                player_kda = player_kdas[summoner_name][1]
                setattr(player_kda, val, getattr(
                    player_kda, val) + player['stats'][val])

    player_kdas = {k: v for k, v in sorted(
        player_kdas.items(), key=lambda KDA: KDA[1][0])}

    [print(name, player_kda) for name, player_kda in player_kdas.items()]
    print(f'{len(player_kdas)} players found')


if __name__ == '__main__':
    main()
