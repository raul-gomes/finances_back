import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_mongo_connection():
    client = AsyncIOMotorClient("mongodb://admin:password@localhost:27017/finances-db?authSource=admin")
    print(client.address)
    try:
        await client.admin.command('ping')
        print("Conectado ao MongoDB com sucesso!")
    except Exception as e:
        print(f"Erro ao conectar: {e}")

if __name__ == "__main__":
    asyncio.run(test_mongo_connection())
