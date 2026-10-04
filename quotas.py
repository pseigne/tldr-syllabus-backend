import os
import requests


class QuotaUnavailable(Exception):
    pass


SCRIPT = '''
local visitor = tonumber(redis.call('GET', KEYS[1]) or '0')
local total = tonumber(redis.call('GET', KEYS[2]) or '0')
if visitor >= 3 or total >= 20 then return 0 end
redis.call('INCR', KEYS[1])
redis.call('INCR', KEYS[2])
redis.call('EXPIRE', KEYS[1], 172800)
redis.call('EXPIRE', KEYS[2], 172800)
return 1
'''


def reserve(day, visitor):
    try:
        response = requests.post(
            os.environ['UPSTASH_REDIS_REST_URL'],
            headers={'Authorization': 'Bearer ' + os.environ['UPSTASH_REDIS_REST_TOKEN']},
            json=['EVAL', SCRIPT, '2', f'syllabus:{day}:ip:{visitor}', f'syllabus:{day}:total'],
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()['result']
        if type(result) is not int or result not in (0, 1):
            raise QuotaUnavailable()
        return result == 1
    except (requests.RequestException, ValueError, KeyError) as error:
        raise QuotaUnavailable() from error
