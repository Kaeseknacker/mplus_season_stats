import re
import requests
import json
from functools import partial
from concurrent.futures import ThreadPoolExecutor


def is_json(myjson):
	try:
		json.loads(myjson)
	except ValueError as e:
		return False
	return True


def pull(urls, proxy=''):    #sometimes gets stuck if Proxy does not response -.-
    with requests.Session() as s:
		s.headers.update({'Cache-Control': 'none','Pragma':'ino-cache'})
		if proxy != '':
			with open('proxykey') as f:
				key = f.readlines()
				proxies = {
				'http': f'http://{key[0].strip()}@{proxy}:8080',
				'https': f'http://{key[0].strip()}@{proxy}:8080'
				}
				s.proxies.update(proxies)
		connection_timeout = 90
		read_timeout = 90
		s_get_with_timeout = partial(s.get, timeout=(connection_timeout,read_timeout))
		if len(urls) > 1:
			with ThreadPoolExecutor(max_workers=20) as pool:
				results = pool.map(s_get_with_timeout, urls, chunksize=1)  # DL all URLS !!
		elif len(urls) == 1:
			results = [s_get_with_timeout(urls[0])]
		else:
			return []
		checked_results = []
		try:
			for r in results:
				for x in range(3):
					if r.ok and is_json(r.text):
						checked_results.append(r)
						break
					else:
						r = s.get(r.url)
					if x == 2:
						checked_results.append(r)
		except requests.exceptions.ReadTimeout as e:
			print(e)
			quit(1)

	return checked_results


def extract_player_ids(players, proxy='') -> None:
	run_id_pattern = re.compile('\/(\d+)')
	run_ids = [run_id_pattern.findall(p._data['mythic_plus_best_runs'][0]['url'])[0] for p in players if len(p._data['mythic_plus_best_runs']) > 0]
	season_slug = players[0]._data['mythic_plus_scores_by_season'][0]['season']
	pull_urls = [f'https://raider.io/api/v1/mythic-plus/run-details?season={season_slug}&id={run_id}' for run_id in run_ids]
	runs_response = pull(pull_urls, proxy)
	dict_player_ids = {}
	for p in players:
		for r in runs_response:
			player_found = False
			if r.ok and is_json(r.text):
				for char in r.json()['roster']:
					if char['character']['name'] == p.name:
						dict_player_ids[p.name] = char['character']['id']
						player_found = True
						break
			if player_found:
				break
	with open('player_ids.json', 'w') as f:
		json.dump(dict_player_ids, f)


def main():
    dungeons = [
        {
            "id": 13991,
            "challenge_mode_id": 405,
            "slug": "brackenhide-hollow",
            "name": "Brackenhide Hollow",
            "short_name": "BH"
        },
        {
            "id": 9164,
            "challenge_mode_id": 245,
            "slug": "freehold",
            "name": "Freehold",
            "short_name": "FH"
        },
        {
            "id": 14082,
            "challenge_mode_id": 406,
            "slug": "halls-of-infusion",
            "name": "Halls of Infusion",
            "short_name": "HOI"
        },
        {
            "id": 7546,
            "challenge_mode_id": 206,
            "slug": "neltharions-lair",
            "name": "Neltharion's Lair",
            "short_name": "NL"
        },
        {
            "id": 14011,
            "challenge_mode_id": 404,
            "slug": "neltharus",
            "name": "Neltharus",
            "short_name": "NELT"
        },
        {
            "id": 9391,
            "challenge_mode_id": 251,
            "slug": "the-underrot",
            "name": "The Underrot",
            "short_name": "UNDR"
        },
        {
            "id": 5035,
            "challenge_mode_id": 438,
            "slug": "the-vortex-pinnacle",
            "name": "The Vortex Pinnacle",
            "short_name": "VP"
        },
        {
            "id": 13968,
            "challenge_mode_id": 403,
            "slug": "uldaman-legacy-of-tyr",
            "name": "Uldaman: Legacy of Tyr",
            "short_name": "ULD"
        }
    ]
    characters = [
        {
            "name": "Astoria",
            "id": 14161988
        },
        {
            "name": "Ayumii",
            "id": 6376434
        },
        {
            "name": "Bratwurscht",
            "id": 115621689
        },
        {
            "name": "Demage",
            "id": 52272508
        },
        {
            "name": "Easydracthyr",
            "id": 118710312
        },
        {
            "name": "Hoppala",
            "id": 52679546
        },
        {
            "name": "Kyria",
            "id": 2459640
        },
        {
            "name": "Käseknacker",
            "id": 71542379
        },
        {
            "name": "Lenis",
            "id": 56320624
        },
        {
            "name": "Liamos",
            "id": 54165090
        },
        {
            "name": "Macaronis",
            "id": 84039504
        },
        {
            "name": "Nodoká",
            "id": 52725936
        },
        {
            "name": "Thymár",
            "id": 115326806
        },
        {
            "name": "Zephalon",
            "id": 49445028
        }
    ]

    # characterId:
    # Käseknacker: 71542379
    # Demage:      52272508


    url = "https://raider.io/api/characters/mythic-plus-runs"

    print("#mplus_runs")
    print("character    | #overall | #+20 | ratio of +20")
    print("-------------+----------+------+-------------")
    for character in characters:
        characterId = character['id']
        sum = 0
        sum_20 = 0
        for dungeon in dungeons:
            dungeonId = dungeon['id']
            querystring = {"season":"season-df-2","characterId":f"{characterId}","dungeonId":f"{dungeonId}","role":"all","specId":"0","mode":"scored","affixes":"all","date":"all"}

            payload = ""
            headers = {}
            response = requests.request("GET", url, data=payload, headers=headers, params=querystring)

            result = response.json()
            sum += len(result['runs'])
            for run in result['runs']:
                if run['summary']['mythic_level'] >= 20:
                    sum_20 += 1
            #print(dungeon['name'], len(result['runs']))
        name = "{:12s}".format(character['name'])
        overall = "{:8d}".format(sum)
        twenties = "{:4d}".format(sum_20)
        percent_20 = "{:3d}%".format(round(sum_20 / sum * 100))
        print(f"{name} | {overall} | {twenties} |         {percent_20}")


if __name__ == "__main__":
    main()
