## Phase 2 — Multi-Domain Hypothesis Engine

### Description

Expand the prediction engine from a single domain (finance) to **multiple domains** (market data, OSINT intelligence, technology trends, company formation signals). Build the parallel hypothesis engine that can run **hundreds of models** simultaneously. Introduce the 3D world model concept — spatial representations of entities and their relationships. Add the horizon extension mechanism that gradually increases prediction lookahead as accuracy improves.

### Deliverable

A multi-domain prediction system with:
- **Multi-domain data layer**: Integration with OSINT feeds, technology databases, company registry data, and social signal processing
- **3D world model**: Spatial representation of entities (companies, people, technologies, capital flows) with dynamic relationships
- **Hypothesis pool (100s)**: Scalable pool of 100-500 parallel hypotheses across domains
- **Horizon extender**: Mechanism that extends prediction horizon from 1-step to multi-step (days → weeks → months) as accuracy permits
- **Cross-domain correlation engine**: Identifies and models relationships between domains (e.g., how a tech patent filing correlates with stock movement)
- **Surprise minimization RL**: Advanced RL (PPO or SAC) that optimizes across all domains simultaneously
- **OSINT Corp bridge**: Preliminary integration with OSINT data collection infrastructure

### Dependencies

- Phase 1 deliverables (core prediction engine)
- `osint_corp` (planned): Open-source intelligence collection and processing
- `forensic` (planned): Forensic analysis of financial and corporate structures
- Distributed computing framework (Ray or Dask)
- Vector database (Pinecone, Weaviate, or Milvus)
- 3D rendering engine (Three.js or Unity for visualization)

### Success Criteria

| Criterion | Target |
|-----------|--------|
| Domain coverage | ≥5 distinct prediction domains operational |
| Hypothesis scale | ≥100 parallel hypotheses with independent scoring |
| Horizon extension | Successfully extends from 1-step to ≥7-step predictions with <10% accuracy degradation |
| Cross-domain correlation | Identifies ≥50 significant cross-domain correlations |
| 3D world model | Spatial representation updated in real-time with ≥10,000 entities |
| Surprise minimization | Overall surprise score reduced by ≥50% from Phase 1 baseline over 100 epochs |
| OSINT integration | Ingests and processes ≥100,000 OSINT signals per day |

### Tasks

- [ ] Design and implement multi-domain data ingestion pipeline
- [ ] Build OSINT data connectors (news, social media, patent databases, company registries)
- [ ] Implement vector database for entity embeddings
- [ ] Build 3D world model engine (entity graph → spatial representation)
- [ ] Design scalable hypothesis pool architecture (Ray/Dask distributed)
- [ ] Implement horizon extension algorithm with accuracy gates
- [ ] Build cross-domain correlation engine
- [ ] Upgrade RL core to multi-objective opti