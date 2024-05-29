async def await_open_browser(host, port, url='/', method="GET"):
    import asyncio
    import http
    import webbrowser

    while True:
        try:
            conn = http.client.HTTPConnection(host, port)
            conn.request(method, url)
            response = conn.getresponse()
            if response.status == 200:
                break
        except (http.client.HTTPException, ConnectionRefusedError):
            pass
        await asyncio.sleep(1)
    webbrowser.open(url)
