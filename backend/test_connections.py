import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from neo4j import GraphDatabase
from config.settings import get_settings

settings = get_settings()

def print_header():
    print("\n" + "="*50)
    print("🎬 CineFeels - Database Connection Test")
    print("="*50 + "\n")

async def test_mongodb():
    """Test MongoDB Atlas connection"""
    print("📦 Testing MongoDB Atlas...")
    try:
        client = AsyncIOMotorClient(settings.mongodb_uri)
        await client.admin.command('ping')
        print(f"   ✅ Connected to: {settings.mongodb_db_name}")
        
        # List collections
        db = client[settings.mongodb_db_name]
        collections = await db.list_collection_names()
        print(f"   📚 Collections: {collections if collections else 'None (fresh database)'}")

        client.close()
        return True
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def test_neo4j():
    """Test Neo4j Aura connection"""
    print("\n🕸️  Testing Neo4j Aura...")
    try:
        driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        
        driver.verify_connectivity()
        print(f"   ✅ Connected successfully!")
        
        # Count nodes
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count")
            count = result.single()["count"]
            print(f"   📊 Total nodes: {count}")
        
        driver.close()
        return True
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

async def main():
    print_header()
    
    mongo_ok = await test_mongodb()
    neo4j_ok = test_neo4j()
    
    print("\n" + "="*50)
    if mongo_ok and neo4j_ok:
        print("✨ All systems ready! CineFeels is good to go! 🚀")
    else:
        print("⚠️  Some connections failed. Check your .env file.")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())