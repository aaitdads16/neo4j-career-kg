"""
Load career-ops tracker.xlsx into Neo4j as a knowledge graph.
Run once to populate, re-run to update (uses MERGE to avoid duplicates).
"""
import os
import re
from pathlib import Path
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv
from extract_skills import extract_skills

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
TRACKER_PATH = Path.home() / "Desktop/projects/neo4j-career-kg/tracker.xlsx"
# Adjust this path to where your tracker.xlsx lives

URI      = os.getenv("NEO4J_URI")
USER     = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")


# ── Neo4j driver ──────────────────────────────────────────────────────────────
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def _clean(val):
    """Return None for NaN/empty, string otherwise."""
    if pd.isna(val) or str(val).strip() in ("", "nan", "None"):
        return None
    return str(val).strip()


def load_jobs(df: pd.DataFrame, session):
    """Create all Job, Company, Location, Skill nodes and relationships."""
    
    for i, row in df.iterrows():
        title   = _clean(row.get("title"))
        company = _clean(row.get("company"))
        if not title or not company:
            continue
        
        job_id    = _clean(row.get("job_id")) or f"job_{i}"
        source    = _clean(row.get("source"))    or "Unknown"
        location  = _clean(row.get("location"))  or "Unknown"
        region    = _clean(row.get("region"))     or "Unknown"
        score     = row.get("relevance_score")
        status    = _clean(row.get("status"))     or "Applied"
        date_val  = str(row.get("date_found", ""))[:10]

        # Parse city and country from location string
        parts   = location.split(",")
        city    = parts[0].strip() if parts else location
        country = parts[-1].strip() if len(parts) > 1 else region

        # Extract skills via Claude
        print(f"  [{i+1}/{len(df)}] Extracting skills for: {title} @ {company}")
        skills = extract_skills(title, company)

        # ── Create nodes + relationships ──────────────────────────────────
        session.run("""
            MERGE (j:Job {job_id: $job_id})
            SET j.title = $title,
                j.source = $source,
                j.score  = $score,
                j.status = $status,
                j.date   = $date

            MERGE (c:Company {name: $company})
            MERGE (l:Location {city: $city, country: $country})
            SET l.region = $region

            MERGE (j)-[:OFFERED_BY]->(c)
            MERGE (j)-[:IN_LOCATION]->(l)
            MERGE (c)-[:LOCATED_IN]->(l)
        """, job_id=job_id, title=title, source=source,
             score=float(score) if score and str(score) != "nan" else 0.0,
             status=status, date=date_val,
             company=company, city=city, country=country, region=region)

        # Create Skill nodes and REQUIRES_SKILL relationships
        for skill in skills:
            # Categorise skill
            if skill in ("Python", "SQL", "Bash", "R", "Julia"):
                category = "Programming"
            elif skill in ("PyTorch", "TensorFlow", "Scikit-learn", "Keras", "JAX"):
                category = "ML Framework"
            elif skill in ("NLP", "CV", "Computer Vision", "LLM", "RL", "GenAI"):
                category = "Domain"
            else:
                category = "Tool"
            
            session.run("""
                MERGE (s:Skill {name: $skill})
                SET s.category = $category
                WITH s
                MATCH (j:Job {job_id: $job_id})
                MERGE (j)-[:REQUIRES_SKILL]->(s)
            """, skill=skill, category=category, job_id=job_id)

    print(f"\nLoaded {len(df)} jobs into Neo4j.")


def main():
    if not TRACKER_PATH.exists():
        print(f"Tracker not found at {TRACKER_PATH}")
        print("Update TRACKER_PATH in load_graph.py to point to your tracker.xlsx")
        return

    print(f"Reading {TRACKER_PATH}...")
    df = pd.read_excel(TRACKER_PATH)
    print(f"Found {len(df)} rows")

    with driver.session() as session:
        # Clear existing data (comment out if you want to append)
        session.run("MATCH (n) DETACH DELETE n")
        print("Cleared existing graph.")

        load_jobs(df, session)
    
    driver.close()
    print("Done!")


if __name__ == "__main__":
    main()