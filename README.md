# Metro Operations – Neo4j Graph Database (Assessment 3, Sydney Group 21)

Migration of the Assessment 2 SQLite *Metro Operations* database to Neo4j.

| File | Task |
|---|---|
| `import.txt` | Task 2 – constraints, indexes, LOAD CSV scripts for all nodes and relationships, derived relationships, verification |
| `csv/` | Task 2 – the 17 relational tables exported as CSV (one file per table, original column names) |
| `queries.txt` | Task 3 – four Cypher query use cases (basic → complex) |
| `gds_algorithms.txt` | Tasks 4–5 – GDS centrality (7 algorithms) and similarity (5 approaches) use cases |
| `figures/` | Graph data model and analysis figures used in the report |
| `scripts/generate_data.py` | Reproducible generator for the expanded dataset (keeps all Assessment 2 sample rows) |

## How to run
1. Neo4j 5.26 LTS or 2025.x with the **Graph Data Science** plugin (Neo4j Desktop: *Plugins → Graph Data Science*).
2. Copy every file in `csv/` into the database's **import** folder.
3. In Neo4j Browser, enable *multi-statement query editor*, paste `import.txt` and run it
   (or `cypher-shell -u neo4j -p <password> -f import.txt`).
   The batched `CALL … IN TRANSACTIONS` statement (step 4.2) needs the `:auto` prefix in Browser.
4. Run the statements in `queries.txt`, then `gds_algorithms.txt`, one at a time.

Expected after import: 2,203 nodes and 14,514 relationships.
