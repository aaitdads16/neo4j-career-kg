"""
The 3 showcase Cypher queries for the portfolio project.
Run after seed_test.py or load_graph.py has populated the database.
"""
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")),
)


def query_1_skill_overlap():
    """
    QUERY 1: Which companies post roles requiring BOTH NLP and Computer Vision?
    These are the rarest, most research-oriented companies — your best targets.
    """
    print("\n=== Q1: Companies requiring NLP + Computer Vision ===")

    cypher = """
        MATCH (c:Company)<-[:OFFERED_BY]-(j:Job)-[:REQUIRES_SKILL]->(s1:Skill)
        WHERE toLower(s1.name) IN ["nlp", "natural language processing"]
        WITH c, j
        MATCH (j)-[:REQUIRES_SKILL]->(s2:Skill)
        WHERE toLower(s2.name) IN ["cv", "computer vision"]
        RETURN c.name AS company,
               count(DISTINCT j) AS roles_needing_nlp_and_cv
        ORDER BY roles_needing_nlp_and_cv DESC
        LIMIT 15
    """

    with driver.session() as session:
        result = session.run(cypher)
        rows = list(result)   # consume inside the session

    if not rows:
        print("  (no companies found requiring both NLP + CV in the current data)")
    else:
        for r in rows:
            print(f"  {r['company']}: {r['roles_needing_nlp_and_cv']} role(s)")


def query_2_skill_demand():
    """
    QUERY 2: What are the most in-demand skills across all job offers?
    Also shows how many of those jobs you actually applied to.
    Reveals gaps between market demand and your application coverage.
    """
    print("\n=== Q2: Most in-demand skills across all offers ===")

    # All jobs — total demand per skill
    cypher_total = """
        MATCH (j:Job)-[:REQUIRES_SKILL]->(s:Skill)
        RETURN s.name AS skill,
               s.category AS category,
               count(DISTINCT j) AS total_demand
        ORDER BY total_demand DESC
        LIMIT 20
    """

    # Applied jobs only — coverage per skill
    cypher_applied = """
        MATCH (j:Job)-[:REQUIRES_SKILL]->(s:Skill)
        WHERE j.status IN ["Applied", "Interview", "Offer"]
        RETURN s.name AS skill, count(DISTINCT j) AS applied_count
    """

    with driver.session() as session:
        total_rows  = list(session.run(cypher_total))
        applied_rows = list(session.run(cypher_applied))

    # Build lookup: skill -> applied count
    applied_map = {r["skill"]: r["applied_count"] for r in applied_rows}

    if not total_rows:
        print("  (no skill data found — make sure load_graph.py or seed_test.py has been run)")
        return

    for r in total_rows:
        skill    = r["skill"]
        category = r["category"]
        demand   = r["total_demand"]
        applied  = applied_map.get(skill, 0)
        pct      = round(applied / demand * 100, 1) if demand else 0
        bar      = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        print(f"  {skill:25s} [{bar}] {pct:5.1f}%  "
              f"demand={demand}  applied={applied}  ({category})")


def query_3_region_source():
    """
    QUERY 3: By region — which scraping source finds the highest-scoring jobs?
    Tells you where to focus your scraping budget.
    """
    print("\n=== Q3: Average relevance score by region + source ===")

    cypher = """
        MATCH (j:Job)-[:IN_LOCATION]->(l:Location)
        WHERE j.score IS NOT NULL AND j.score > 0
        RETURN l.region AS region,
               j.source AS source,
               round(avg(j.score), 2) AS avg_score,
               count(j) AS total_jobs
        ORDER BY region ASC, avg_score DESC
    """

    with driver.session() as session:
        rows = list(session.run(cypher))

    if not rows:
        print("  (no location/score data found)")
        return

    current_region = None
    for r in rows:
        if r["region"] != current_region:
            current_region = r["region"]
            print(f"\n  {current_region}:")
        print(f"    {r['source']:12s}  avg_score={r['avg_score']}  "
              f"jobs={r['total_jobs']}")


def query_debug():
    """
    DEBUG: Confirm what's in the database before running the showcase queries.
    Run this first if you get empty results.
    """
    print("\n=== DEBUG: What's in the database? ===")

    checks = [
        ("Total nodes by label",
         "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC"),
        ("Relationship types",
         "MATCH ()-[r]->() RETURN type(r) AS rel, count(r) AS count ORDER BY count DESC"),
        ("Sample jobs",
         "MATCH (j:Job) RETURN j.title, j.source, j.status, j.score LIMIT 5"),
        ("Sample skills",
         "MATCH (j:Job)-[:REQUIRES_SKILL]->(s:Skill) RETURN j.title, s.name LIMIT 5"),
    ]

    for label, cypher in checks:
        print(f"\n  -- {label} --")
        with driver.session() as session:
            rows = list(session.run(cypher))
        if not rows:
            print("  (empty)")
        else:
            for r in rows:
                print("  ", dict(r))


if __name__ == "__main__":
    import sys

    if "--debug" in sys.argv:
        query_debug()
    else:
        query_1_skill_overlap()
        query_2_skill_demand()
        query_3_region_source()

    driver.close()
