import httpx

headers = {'Host': 'www.instagram.com', 'X-Requested-With': 'XMLHttpRequest', 'Sec-Ch-Prefers-Color-Scheme': 'dark', 'Sec-Ch-Ua-Platform': '"Linux"', 'X-Ig-App-Id': '936619743392459', 'Sec-Ch-Ua-Model': '""', 'Sec-Ch-Ua-Mobile': '?0',
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36', 'Accept': '*/*', 'X-Asbd-Id': '129477', 'Sec-Fetch-Site': 'same-origin', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Dest': 'empty', 'Referer': 'https://www.instagram.com/', 'Accept-Language': 'en-US,en;q=0.9', 'Priority': 'u=1, i'}


async def instagram_check(username):
    with httpx.Client() as client:

        try:
            resp = client.get(
                f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}", headers=headers)

            resp.raise_for_status()
            print(resp.status_code)
        except httpx.HTTPStatusError as e:
            return

        data = resp.json().get("data")

        if not data:
            return

        user_data = data.get("user")

        if not user_data:
            return

        instagram_info = {
            "username": username,
            "followers": user_data["edge_followed_by"]["count"],
            "avatar_url": user_data["profile_pic_url"]
        }

        return instagram_info
