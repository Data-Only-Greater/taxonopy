
import asyncio
import datetime

import aiohttp


async def get(session: aiohttp.ClientSession,
              *args,
              **kwargs) -> dict:
    
    route = "/".join(args)
    url = f"https://api.github.com/repos/{route}"
    resp = await session.request('GET', url=url, **kwargs)
    data = await resp.json()
    
    return data


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


async def fetch_GitHub(uri_details):
    
    headers = {"Accept": "application/vnd.github+json"}
    
    base = [uri_details["username"], uri_details["reponame"]]
    routes = [base,
              base + ["languages"],
              base + ["releases", "latest"]]
    
    results = await main(routes, headers=headers)
    
    data = {"description": results[0].get("description", ""),
            "created": '',
            "languages": list(results[1].keys()),
            "licenses": '',
            "topics": results[0].get("topics", ""),
            "version": results[2].get('name', "")}
    
    created = results[0].get("created_at")
    if created is not None:
        data["created"] = datetime.datetime.strptime(created,
                                                 '%Y-%m-%dT%H:%M:%SZ')
    
    if results[0].get("licenses"):
        data["licenses"] = [license["name"]
                                for license in results[0].get("licenses")]
    
    return data
