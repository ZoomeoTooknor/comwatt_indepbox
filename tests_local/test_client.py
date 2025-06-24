import asyncio
from custom_components.comwatt_indepbox.client import ComwattClient

async def main():
    username = "ton@email.com"
    password = "ton_password"
    
    client = ComwattClient(username, password)
    await client.authenticate()
    
    print("Authentifié")

    user = await client.get_authenticated_user()
    print("Utilisateur :", user)

    indepboxes = await client.get_indepboxes()
    print("Boxes :", indepboxes)

    devices = await client.get_devices()
    print("Devices :", devices)

    if devices:
        device_ids = [d["id"] for d in devices]
        stats = await client.get_device_stats(device_ids)
        print("Stats :", stats)

    await client.close()

asyncio.run(main())