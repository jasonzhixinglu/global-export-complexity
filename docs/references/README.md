# External reference papers

Papers kept in-repo because they directly inform the modeling or analysis. Name files
`<authors>-<year>-<short-title>-<source-id>.pdf`.

## Chen, Chen, Bolivar & Chen (2024) — Time-Varying Matrix Factor Models

- File: [chen-et-al-2024-time-varying-matrix-factor-models-arxiv-2404.01546.pdf](chen-et-al-2024-time-varying-matrix-factor-models-arxiv-2404.01546.pdf)
- Source: [arXiv:2404.01546](https://arxiv.org/abs/2404.01546) (v1, April 2024). JEL: C13, C14, C32, C55.

**What it offers.** A matrix factor model Y_t = R_t F_t C_t' + E_t for matrix-valued
time series where the row/column loading matrices are smooth *time-varying* functions
of t/T, estimated by local (kernel-weighted) PCA. Contributions: consistency and
asymptotic normality under weak cross-row/column/time noise correlation; a generalized
eigenvalue-ratio estimator for the latent factor dimensions; and a smoothing procedure
that resolves rotational ambiguity so estimated loadings are interpretable over time.

**Why it's here.** The paper's headline application is international trade flows
(monthly exporter x importer matrices, 24 countries, 1982-2018), interpreting factors
F_t as trade among latent *trading hubs* and loadings R_t, C_t as each country's
evolving participation in those hubs. That maps directly onto this project's data:
product-group-specific (e.g. tech/AI-related) bilateral export matrices could be
modeled the same way, with time-varying loadings capturing structural shifts such as
China's rise in electronics or supply-chain reconfiguration — shifts a constant-loading
factor model would smear out.


## Network measures, fragmentation, and quantitative trade (added 2026-07)

Working-paper versions from public sources (NBER, IMF, author/Cornell sites),
supporting the network-measures and structural-model sections of
[research-proposal.md](../research-proposal.md):

| file | why it's here |
|---|---|
| kleinberg-1999-hits… | HITS hub/authority scores — our factor loadings are their time-varying generalization |
| acemoglu-et-al-2012-network-origins… | production-network propagation; the Katz/influence-vector centrality |
| antras-chor-fally-hillberry-2012-upstreamness… | upstreamness/downstreamness — chain-position measures |
| caliendo-parro-2015-trade-io-nafta… | the workhorse quantitative trade model with IO links (our demand block baseline) |
| baqaee-farhi-2019-beyond-hultens-theorem… | nested-CES propagation; the complementarity-vs-capacity distinction we test against |
| amiti-redding-weinstein-2019-trade-war-prices… | 2018 tariff pass-through — template for estimating sigma off dated policy |
| fajgelbaum-et-al-2020-return-to-protectionism… | 2018-19 trade-war GE estimation — same role |
| antras-de-gortari-2020-geography-of-gvcs… | multi-stage location choice for value chains |
| bonadio-et-al-2021-global-supply-chains-pandemic… | pandemic quantification of GVC shock propagation |
| grossman-helpman-lhuillier-2023-supply-chain-resilience… | diversification-vs-reshoring theory |
| alfaro-chor-2023-great-reallocation… | the descriptive reallocation facts our panel sharpens |
| gopinath-et-al-2024-changing-global-linkages… | bloc-based fragmentation measurement (our fragmentation baseline) |
