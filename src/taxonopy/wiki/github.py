
import asyncio
import datetime

import aiohttp


async def get(session: aiohttp.ClientSession,
              *args,
              **kwargs) -> dict:
    
    route = "/".join(args)
    url = f"https://api.github.com/repos/{route}"
    
    async with session.request('GET', url=url, **kwargs) as resp:
        
        data = await resp.json()
        
        if resp.ok:
            return data
        
        raise RuntimeError(f"{data['message']} on {url}")


async def main(paths, **kwargs):
    
    async with aiohttp.ClientSession() as session:
      
        tasks = []
        
        for p in paths:
            tasks.append(get(session, *p, **kwargs))
            
        return await asyncio.gather(*tasks, return_exceptions=True)


def confirm_GitHub(uri):
    return 'github' in uri.split('/')[2].split('.')


def parse_URI(uri):
    splitURI = uri.split('/')
    return {"username": splitURI[3],
            "reponame": splitURI[4]}


async def fetch_GitHub(uri_details, token=None):
    
    headers = {"Accept": "application/vnd.github+json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    
    base = [uri_details["username"], uri_details["reponame"]]
    routes = [base,
              base + ["languages"],
              base + ["releases", "latest"]]
    
    results = await main(routes, headers=headers)
    
    data = {"description": "",
            "created": "",
            "languages": "",
            "licenses": "",
            "topics": "",
            "version": ""}
    errors = []
    
    if isinstance(results[0], RuntimeError):
        errors.append(results[0])
    else:
        
        data["description"] =  results[0]["description"]
        data["topics"] =  results[0]["topics"]
        
        created = results[0].get("created_at")
        if created is not None:
            data["created"] = datetime.datetime.strptime(created,
                                                    '%Y-%m-%dT%H:%M:%SZ')
        
        if results[0].get("licenses"):
            data["licenses"] = [license["name"]
                                    for license in results[0].get("licenses")]
    
    if isinstance(results[1], RuntimeError):
        errors.append(results[1])
    else:
        data["languages"] = list(results[1].keys())
    
    if isinstance(results[2], RuntimeError):
        errors.append(results[2])
    else:
        data["version"] = results[2]["name"]
    
    return data, errors
