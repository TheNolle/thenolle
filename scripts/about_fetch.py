import os, json, urllib.request

TOKEN = os.environ['README_TOKEN']
LOGIN = os.environ.get('GITHUB_LOGIN', 'TheNolle')

QUERY = '''
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false) { totalCount }
    starredByOthers: repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      nodes { stargazerCount }
    }
    contributionsCollection {
      contributionCalendar { totalContributions }
    }
  }
}
'''

def graphql(query: str, variables: dict) -> dict:
    payload = json.dumps({'query': query, 'variables': variables}).encode('utf-8')
    request = urllib.request.Request('https://api.github.com/graphql', data=payload, headers={ 'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json', 'User-Agent': 'about-fetcher' })
    with urllib.request.urlopen(request) as response:
        return json.load(response)

data = graphql(QUERY, {'login': LOGIN})
user = data['data']['user']

followers = user['followers']['totalCount']
repositories = user['repositories']['totalCount']
stars = sum(repo['stargazerCount'] for repo in user['starredByOthers']['nodes'])
contributions = user['contributionsCollection']['contributionCalendar']['totalContributions']

os.makedirs('about', exist_ok=True)

result = {
    'followers': followers,
    'repositories': repositories,
    'stars': stars,
    'contributions': contributions,
}

with open('about/about.json', 'w') as f:
    json.dump(result, f, indent=2)

print(f'followers:     {followers}')
print(f'repositories:  {repositories}')
print(f'stars:         {stars}')
print(f'contributions: {contributions}')
print('Written about/about.json')