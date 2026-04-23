import os, json, urllib.request

TOKEN = os.environ['README_TOKEN']
LOGIN = os.environ.get('GITHUB_LOGIN', 'TheNolle')

QUERY = '''
query($login: String!) {
  user(login: $login) {
    sponsorshipsAsMaintainer(first: 100, includePrivate: true, orderBy: { field: CREATED_AT, direction: DESC }, activeOnly: true) {
      nodes {
        createdAt
        tier { monthlyPriceInCents }
        sponsorEntity {
          ... on User { login avatarUrl name }
          ... on Organization { login avatarUrl name }
        }
      }
    }
  }
}
'''

def graphql(query: str, variables: dict) -> dict:
  payload = json.dumps({'query': query, 'variables': variables}).encode('utf-8')
  request = urllib.request.Request('https://api.github.com/graphql', data=payload, headers={ 'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json', 'User-Agent': 'sponsors-fetcher' })
  with urllib.request.urlopen(request) as response:
    return json.load(response)

def download_avatar(url: str, path: str) -> None:
  request = urllib.request.Request(url + '&s=200', headers={'User-Agent': 'sponsors-fetcher'})
  with urllib.request.urlopen(request) as response:
        with open(path, 'wb') as file:
            file.write(response.read())

data = graphql(QUERY, { 'login': LOGIN })
nodes = data['data']['user']['sponsorshipsAsMaintainer']['nodes']
public = [node for node in nodes if node['sponsorEntity'] is not None]

last_6 = public[:6]
top_3 = sorted(public, key=lambda node: node['tier']['monthlyPriceInCents'] if node['tier'] else 0, reverse=True)[:3]

os.makedirs('sponsors/avatars', exist_ok=True)

def process(sponsors: list, label: str) -> list:
  out = []
  for index, sponsor in enumerate(sponsors):
    entity = sponsor['sponsorEntity']
    login = entity['login']
    avatar = entity['avatarUrl']
    cents = sponsor['tier']['monthlyPriceInCents'] if sponsor['tier'] else 0
    path = f'sponsors/avatars/{label}_{index + 1}_{login}.png'
    download_avatar(avatar, path)
    out.append({ 'rank': index + 1, 'login': login, 'avatar_path': path, 'monthly_cents': cents })
    print(f'[{label}] #{index + 1}: {login} (${cents / 100:.2f}/month) -> {path}')
  return out

result = {
  'top3': process(top_3, 'top'),
  'last6': process(last_6, 'last')
}

with open('sponsors/sponsors.json', 'w') as file:
  json.dump(result, file, indent=2)

print('Written sponsors/sponsors.json')