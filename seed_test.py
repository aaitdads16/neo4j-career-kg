import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
)

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n")  # clear first

    session.run("""
        MERGE (j1:Job {job_id: "test-001", title: "ML Research Intern", source: "LinkedIn", score: 9.0, status: "Applied", date: "2025-01-15"})
        MERGE (j2:Job {job_id: "test-002", title: "NLP Intern", source: "Indeed", score: 8.0, status: "Applied", date: "2025-01-16"})
        MERGE (j3:Job {job_id: "test-003", title: "Computer Vision Intern", source: "LinkedIn", score: 9.0, status: "Interview", date: "2025-01-17"})
        MERGE (j4:Job {job_id: "test-004", title: "Data Science Intern", source: "Adzuna", score: 7.0, status: "Applied", date: "2025-01-18"})
        MERGE (j5:Job {job_id: "test-005", title: "LLM Fine-Tuning Intern", source: "LinkedIn", score: 10.0, status: "Applied", date: "2025-01-19"})

        MERGE (c1:Company {name: "DeepMind"})
        MERGE (c2:Company {name: "Mistral AI"})
        MERGE (c3:Company {name: "Meta AI"})

        MERGE (l1:Location {city: "London", country: "UK", region: "Europe"})
        MERGE (l2:Location {city: "Paris", country: "France", region: "Europe"})
        MERGE (l3:Location {city: "San Francisco", country: "USA", region: "USA_Canada"})

        MERGE (s1:Skill {name: "PyTorch", category: "ML Framework"})
        MERGE (s2:Skill {name: "NLP", category: "Domain"})
        MERGE (s3:Skill {name: "Computer Vision", category: "Domain"})
        MERGE (s4:Skill {name: "Python", category: "Programming"})
        MERGE (s5:Skill {name: "LLM", category: "Domain"})

        MERGE (j1)-[:OFFERED_BY]->(c1) MERGE (j1)-[:IN_LOCATION]->(l1) MERGE (c1)-[:LOCATED_IN]->(l1)
        MERGE (j2)-[:OFFERED_BY]->(c2) MERGE (j2)-[:IN_LOCATION]->(l2) MERGE (c2)-[:LOCATED_IN]->(l2)
        MERGE (j3)-[:OFFERED_BY]->(c3) MERGE (j3)-[:IN_LOCATION]->(l3) MERGE (c3)-[:LOCATED_IN]->(l3)
        MERGE (j4)-[:OFFERED_BY]->(c1) MERGE (j4)-[:IN_LOCATION]->(l1)
        MERGE (j5)-[:OFFERED_BY]->(c2) MERGE (j5)-[:IN_LOCATION]->(l2)

        MERGE (j1)-[:REQUIRES_SKILL]->(s1) MERGE (j1)-[:REQUIRES_SKILL]->(s4)
        MERGE (j2)-[:REQUIRES_SKILL]->(s2) MERGE (j2)-[:REQUIRES_SKILL]->(s4)
        MERGE (j3)-[:REQUIRES_SKILL]->(s3) MERGE (j3)-[:REQUIRES_SKILL]->(s1)
        MERGE (j4)-[:REQUIRES_SKILL]->(s2) MERGE (j4)-[:REQUIRES_SKILL]->(s3)
        MERGE (j5)-[:REQUIRES_SKILL]->(s5) MERGE (j5)-[:REQUIRES_SKILL]->(s1)
    """)

    count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
    print(f"Seeded successfully — {count} nodes in database.")

driver.close()
