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
