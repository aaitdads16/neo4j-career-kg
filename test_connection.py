import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

uri  = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USERNAME")
pwd  = os.getenv("NEO4J_PASSWORD")

print(f"Connecting to: {uri}")

driver = GraphDatabase.driver(uri, auth=(user, pwd))

with driver.session() as session:
    result = session.run("RETURN 'Connection OK' AS msg, 1+1 AS math")
    row = result.single()
    print(row["msg"], "—", row["math"])

driver.close()
print("Done.")
