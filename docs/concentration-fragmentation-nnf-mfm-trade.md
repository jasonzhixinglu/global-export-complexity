# Concentration and Fragmentation in a Non-Negative Matrix Factor Model of Bilateral Trade

> **Implementation:** `scripts/network_stats.py` computes every measure below monthly
> from the era-anchored TV-MFM output → `results/network_stats/` (per-basket series,
> figures, break-window readings; `findings.md` for interpretation).

## Roadmap

This document builds every concentration and fragmentation measure used below from a single, deliberately minimal starting point: ordinary Euclidean geometry applied to share vectors on a simplex. Everything else — Herfindahl concentration, hub overlap/fragmentation, the Gram matrix, effective rank, and the exact relationship between one-sided and two-sided (joint) measures — falls out of that one choice plus one inequality (Cauchy–Schwarz) applied at successive levels of aggregation. The intent is that nothing below is an ad hoc index; each object is either an algebraic identity or an explicit, flagged modeling choice.

**The shape of the argument, in one paragraph:** a hub's country-composition is a point on the probability simplex. Its distance from the simplex's center (perfect evenness) is, up to a constant, the squared Euclidean norm of the share vector — this *is* the Herfindahl index, not merely analogous to it. Comparing two hubs' compositions is the same geometric question asked of two points instead of one, and after removing the scale effect (via the same Cauchy–Schwarz inequality that bounds the Herfindahl index itself), it becomes cosine similarity — a genuine measure of shared composition, cleanly separated from either hub's internal concentration. Stacking all hub vectors into one matrix and taking its Gram matrix produces a single object whose diagonal is concentration and whose normalized off-diagonal is overlap; the eigenvalue spectrum of that same matrix generalizes both notions to the level of the whole network. The two-sided (export × import) picture is the same machinery applied to the bipartite structure of the trade network, and it decomposes *exactly* — no approximation — into the one-sided concentration measures, the core matrix's own linkage concentration, and a covariance term measuring whether concentrated hubs preferentially link to other concentrated hubs.

---

## Part I — Geometric foundations (bottom-up)

### I.1 The state space: the simplex

A share vector — the country-composition of one hub — is a point $p$ in

$$
\Delta^{N-1} = \Big\{ p \in \mathbb{R}^N : p_i \ge 0,\ \sum_{i=1}^N p_i = 1 \Big\}
$$

We adopt the ordinary Euclidean inner product on $\mathbb{R}^N$ as the geometry on this space. This is a choice — the simplex admits other geometries (e.g. the Hellinger/Fisher–Rao metric, reached by mapping $p\mapsto\sqrt p$) — but the Euclidean choice is the one that keeps every downstream object a closed-form quadratic or bilinear form, which is what makes the whole system tractable in one pass. We use it throughout and flag the one place (Part IV) where the choice actually matters.

### I.2 Concentration as distance from the center

The simplex has a distinguished point: the uniform vector $u = (1/N, \dots, 1/N)$, representing perfect evenness — the point of *minimum* concentration. The most primitive question one can ask of $p$ is: how far is it from $u$?

$$
\|p - u\|_2^2 = \sum_i p_i^2 - \tfrac{2}{N}\sum_i p_i + \tfrac1N = \sum_i p_i^2 - \tfrac1N
$$

Rearranged:

$$
\boxed{\; HHI(p) \equiv \sum_i p_i^2 = \|p-u\|_2^2 + \tfrac1N \;}
$$

The Herfindahl index is not a separately-invented index sitting alongside Euclidean geometry — it *is* the squared Euclidean distance from uniformity, shifted by a constant. Equivalently, since the mean of any $p\in\Delta^{N-1}$ over its $N$ entries is exactly $1/N$:

$$
HHI(p) = \tfrac1N + N\cdot\mathrm{Var}(p)
$$

$HHI$ is a rescaled variance of the shares. This also is simply $\|p\|_2^2$ — the squared Euclidean norm of $p$ itself, since $\|p-u\|_2^2 + 1/N = \|p\|_2^2$ algebraically (both expand to $\sum p_i^2$).

**Bounds, via Cauchy–Schwarz.** Applying $(x\cdot y)^2 \le \|x\|^2\|y\|^2$ with $x=p$, $y=\mathbf 1$ (the all-ones vector):

$$
1 = \Big(\sum_i p_i\Big)^2 \le N\sum_i p_i^2 = N\cdot HHI(p) \;\Rightarrow\; HHI(p) \ge \tfrac1N
$$

with equality iff $p=u$. The upper bound $HHI(p)\le 1$ is immediate ($p_i\le1$ for all $i$ when non-negative and summing to 1), with equality iff $p$ is a vertex of the simplex (all mass on one country). So $HHI \in [1/N, 1]$ measures exactly where $p$ sits between the simplex's center and its corners.

*(Caveat: this specific quadratic functional is the $\alpha=2$ member of the broader Rényi/Hill diversity family — Shannon entropy, richness, and the Berger–Parker index are other members. Choosing $\alpha=2$ is what buys the closed-form linear-algebra structure that follows; it is a deliberate choice, not the unique way to measure "distance from uniform.")*

### I.3 Overlap as normalized inner product between two points

The analogous primitive question for *two* hubs' compositions, $p^{(k)}$ and $p^{(k')}$, is how close together they sit — measured via their inner product:

$$
p^{(k)}\cdot p^{(k')} = \sum_i p_i^{(k)} p_i^{(k')}
$$

Applying Cauchy–Schwarz again, this time between the two hub vectors themselves:

$$
\big(p^{(k)}\cdot p^{(k')}\big)^2 \;\le\; HHI_k\cdot HHI_{k'}
$$

with equality iff the two hubs are proportional — and since both sum to 1, proportional means *identical*. This is the same inequality used in I.2, one level up. It also reveals the problem with using the raw inner product directly as an overlap measure: **it is bounded above by each hub's own concentration**, so two hubs that are diffuse-but-identical necessarily register a *small* raw inner product — indistinguishable from two hubs that are diffuse and genuinely disjoint. Concentration and overlap are entangled in the raw quantity.

**The fix is the same normalization used to build a correlation coefficient from a covariance:** divide by the norms.

$$
\boxed{\;\text{overlap}_{k,k'} = \cos\theta_{k,k'} = \frac{p^{(k)}\cdot p^{(k')}}{\sqrt{HHI_k}\sqrt{HHI_{k'}}} \in [0,1]\;}
$$

equal to 1 iff the hubs are identical (regardless of how concentrated or diffuse either one is), equal to 0 iff they have disjoint support. Define disjointedness as $1-\cos\theta_{k,k'}$. This genuinely separates the two questions — "how tight is this hub" and "do these two hubs draw on the same countries" — that the raw inner product conflated.

---

## Part II — The NNF-MFM and hub interpretation

$$
X_t \;\approx\; R\, F_t\, C', \qquad R\in\mathbb{R}_{\ge0}^{N\times K_1},\;\; C\in\mathbb{R}_{\ge0}^{N\times K_2},\;\; F_t\in\mathbb{R}_{\ge0}^{K_1\times K_2}
$$

$X_t[i,j]$ is the flow from exporter $i$ to importer $j$. $R$'s columns are **export hubs**: column $k$ groups exporters that co-move together. $C$'s columns are **import hubs**. $F_t[k,k']$ is the flow intensity between export hub $k$ and import hub $k'$ — the hub-to-hub linkage. Non-negativity throughout (NNF) is what guarantees every quantity below is a genuine, non-negative share — nothing in Part I required signed vectors to work, so this factorization keeps the whole geometric picture valid without modification.

Rescale each hub's loading column into the share vector from Part I:

$$
p_i^{(k)} = \frac{R[i,k]}{\sum_{i'}R[i',k]}, \qquad q_j^{(k')} = \frac{C[j,k']}{\sum_{j'}C[j',k']}
$$

and normalize the core matrix into a distribution over hub-pairs. **The scale removed from the loading columns must be pushed into $F_t$ first** — otherwise $w_k$ below is not hub $k$'s share of trade. With $\sigma_k = \sum_i R[i,k]$ and $\tau_{k'} = \sum_j C[j,k']$ the column sums absorbed by the share-normalization,

$$
\tilde F_t[k,k'] = \sigma_k\, F_t[k,k']\, \tau_{k'}, \qquad
g_{k,k'} = \frac{\tilde F_t[k,k']}{\sum_{k,k'}\tilde F_t[k,k']}, \qquad w_k = \sum_{k'}g_{k,k'},\quad v_{k'} = \sum_k g_{k,k'}
$$

so that $R F_t C' = P \tilde F_t Q'$ identically ($P, Q$ the share-column matrices). Then $w_k$ is export hub $k$'s share of total (reconstructed) trade flow; $v_{k'}$ is the analogous import-hub share.

---

## Part III — Concentration measures

### III.1 Level 0 — within-hub

$$
a_k \equiv HHI_k^{\text{exp}} = \sum_i \big(p_i^{(k)}\big)^2, \qquad b_{k'} \equiv HHI_{k'}^{\text{imp}} = \sum_j \big(q_j^{(k')}\big)^2
$$

$1/a_k$ is the effective number of countries in export hub $k$.

### III.2 Level 1 — one-sided network aggregate

Volume-weighted average across hubs:

$$
HHI^{\text{exp}} = \sum_k w_k\, a_k, \qquad HHI^{\text{imp}} = \sum_{k'} v_{k'}\, b_{k'}
$$

### III.3 The core matrix's own concentration

$$
HHI_F = \sum_{k,k'} g_{k,k'}^2
$$

— a structurally distinct notion: not which countries dominate a hub, but which hub-*pairs* dominate total world trade.

### III.4 The Gram matrix

Stack the export-hub share vectors as columns of $P$ ($N\times K_1$). Define

$$
S = P'P, \qquad S_{k,k'} = p^{(k)}\cdot p^{(k')}
$$

Computing $S$ requires nothing beyond a single matrix product — no decomposition is needed to construct it. Its diagonal is exactly the Level-0 concentration vector: $S_{kk} = a_k$. Its off-diagonal, once cosine-normalized ($S_{k,k'}/\sqrt{S_{kk}S_{k'k'}}$), is exactly the overlap measure from I.3. Concentration and overlap are two readouts of one object, not two separate constructions.

**Relationship to a covariance matrix — an exact identity, not an analogy.** Because every hub-share column sums to 1 over $N$ countries, its cross-sectional mean is always exactly $1/N$ — a universal constant, identical for every hub regardless of concentration. This constancy makes $S$ an exact affine transform of the genuine (population) covariance matrix of the hub columns, treating **countries as observations and hubs as variables**:

$$
\boxed{\; S = \tfrac1N J + N\cdot\mathrm{Cov}(P) \;}
$$

where $J$ is the all-ones matrix and $\mathrm{Cov}(P)_{k,k'} = \tfrac1N\sum_i(p_i^{(k)}-\tfrac1N)(p_i^{(k')}-\tfrac1N)$. This is the matrix generalization of the $HHI = 1/N + N\,\mathrm{Var}(p)$ identity from I.2, with cross-hub covariances now filling the off-diagonal.

**Where the analogy stops.** A genuine correlation matrix normalizes by *variance*, $\mathrm{Corr} = D_{\mathrm{var}}^{-1/2}\mathrm{Cov}\,D_{\mathrm{var}}^{-1/2}$. The cosine/overlap matrix from I.3 instead normalizes by $HHI$ — and since $HHI = 1/N + N\,\mathrm{Var}$, these differ by the additive $1/N$ baked into every diagonal entry. In practice this is not a minor discrepancy: the same underlying data can produce a cosine-overlap reading of $0.69$ between two hubs against a Pearson correlation of $-0.07$. **The Gram matrix is exactly an affine-shifted covariance matrix; the overlap matrix is a related but genuinely distinct normalization of it — not literally a correlation matrix.**

### III.5 Effective rank — the network-level generalization

Ordinary matrix rank is a hard count: an eigenvalue either is or isn't exactly zero, so rank is insensitive to whether the nonzero eigenvalues are similar in size or wildly unequal. Effective rank is the smooth analogue, built from the same inverse-participation-ratio (IPR) functional used to turn $HHI_k$ into "effective number of members," now applied to the *eigenvalue spectrum* of $S$ instead of to a share vector:

$$
\mathrm{IPR}(x) = \frac{(\sum_i x_i)^2}{\sum_i x_i^2}, \qquad \frac{1}{HHI_k} = \mathrm{IPR}\big(p^{(k)}\big), \qquad \mathrm{EffRank} = \mathrm{IPR}(\lambda) = \frac{(\operatorname{tr}S)^2}{\lVert S\rVert_F^2}
$$

using $\operatorname{tr}(S)=\sum_k\lambda_k$ and $\lVert S\rVert_F^2 = \sum_{k,k'}S_{k,k'}^2 = \sum_k\lambda_k^2$ (valid since $S$ is symmetric, so its Frobenius norm squared equals the sum of squared eigenvalues). $\mathrm{EffRank}\in[1,K_1]$ by the same Cauchy–Schwarz inequality applied to the eigenvalue vector against $\mathbf 1\in\mathbb{R}^{K_1}$ — the third instance of the identical bound used in I.2 and I.3. $\mathrm{EffRank}=1$ iff all hubs are identical (regardless of their shared concentration level); $\mathrm{EffRank}=K_1$ iff all hubs have *equal* concentration and pairwise disjoint support. Between those extremes it answers: "how many genuinely independent export hubs does the network actually support," as a continuous number rather than the integer $K_1$ fixed by the estimation.

---

## Part IV — Fragmentation and network-wide overlap

### IV.1 Aggregating pairwise overlap

Volume-weighted average disjointedness across all hub pairs on the export side:

$$
\mathrm{Fragmentation}^{\text{exp}} = 1 - \sum_{k\ne l} \omega_{k,l}\cdot\text{overlap}_{k,l}, \qquad \omega_{k,l} = \frac{w_k w_l}{\sum_{m\ne n}w_m w_n}
$$

mirrored on the import side using $v_{k'}$ and $q^{(k')}$.

### IV.2 Choice-of-geometry caveat

The overlap measure above depends on having fixed the Euclidean geometry in Part I. An alternative, statistically-motivated route exists (mapping $p\mapsto\sqrt p$, under which every point of the simplex has *fixed* unit norm by construction, giving the Bhattacharyya coefficient as the natural overlap measure with no post-hoc normalization needed) — but it generally produces different numbers from cosine similarity for the same pair of hubs, and does not reduce the algebra to closed-form quadratic objects the way the Euclidean choice does. We do not pursue it further here; it is flagged only so that "overlap" is understood as *a* well-motivated construction under a stated choice of geometry, not the unique one.

### IV.3 Joint (bipartite) overlap factorizes exactly

Treat each export-hub/import-hub pair $(k,k')$ as a distinct trade channel, with joint country-pair distribution $\pi^{(k,k')}_{i,j} = p_i^{(k)}q_j^{(k')}$. Overlap between two channels $(k,k')$ and $(l,l')$ decomposes with no approximation:

$$
\text{Overlap}^{\text{joint}}_{(k,k'),(l,l')} = \text{overlap}^{\text{exp}}_{k,l}\times\text{overlap}^{\text{imp}}_{k',l'}
$$

Two channels overlap if and only if they share exporters *and* share importers — the product of the two one-sided cosine similarities, an immediate consequence of the multiplicative $p\otimes q$ structure. This gives a joint effective rank, $\mathrm{EffRank}^{\text{joint}}$, using the same IPR construction over the weighted spectrum of channel-overlaps — the "effective number of independent trade channels" in the whole bipartite network.

### IV.4 Two notions of fragmentation: hub overlap vs bloc structure

The overlap-based fragmentation of IV.1 is *agnostic*: it asks whether the network's demand programs draw on distinct country sets, with no prior about which countries "belong together." The fragmentation of current geopolitical interest is *bloc* fragmentation: US-aligned and China-aligned trade separating into parallel circuits. These are related but not the same measure, and both belong in the toolkit.

Bloc fragmentation lives primarily in the **core matrix $g$**, not in hub compositions. Given a partition of countries into blocs, use *smooth* bloc weights rather than hard hub-to-bloc assignment: export hub $k$'s weight on bloc $B$ is $P_k(B) = \sum_{i\in B} p_i^{(k)}$, and likewise $Q_{k'}(B)$ on the import side. The model-implied share of trade flowing from bloc $B$ exporters to bloc $B'$ importers is then

$$
s_{B\to B'} = \sum_{k,k'} g_{k,k'}\, P_k(B)\, Q_{k'}(B')
$$

The headline bloc-fragmentation statistics are the **cross-bloc channel share** (e.g. $s_{CN\to US} + s_{US\to CN}$, falling as blocs decouple) and the **within-bloc share** $\sum_B s_{B\to B}$, rising with bloc-ification. These are computable per period directly from $(p, q, g)_t$.

The two notions should co-move, with a mechanical link: if blocs pull apart, hub country-supports reorganize along bloc lines, so hubs straddling a bloc boundary split and pairwise overlap falls — the agnostic inverse-overlap measure partially captures bloc fragmentation without being told the bloc labels. The converse fails: hubs can become more disjoint for non-bloc reasons (e.g. a single country's rise pulling it out of a shared hub, as with Taiwan in 2023). Divergence between the two series is therefore itself informative — overlap-fragmentation rising while bloc measures are flat points to technological/market reorganization rather than geopolitical sorting. One estimation-specific caveat: under an anchor-identified basis the hubs are largely disjoint *by construction* (that near-disjointness is what identifies them), so the overlap measure has a compressed dynamic range and doubles as an identification diagnostic — months where overlap jumps are also months to distrust the basis.

---

## Part V — From one-sided to two-sided: the exact decomposition

### V.1 The flattened joint concentration measure

The reconstructed flow decomposes across exporter, export hub, import hub, and importer. Treating $\pi_{i,k,k',j} = g_{k,k'}\,p_i^{(k)}\,q_j^{(k')}$ as one probability distribution (valid: it is non-negative and sums to 1, since $g$, $p^{(k)}$, $q^{(k')}$ each do):

$$
HHI_{\text{flat}} = \sum_{i,k,k',j}\pi_{i,k,k',j}^2 = \sum_{k,k'} g_{k,k'}^2\, a_k\, b_{k'}
$$

This single number is sensitive to concentration at all three structural levels simultaneously — within export hubs, within import hubs, and across hub-pair linkages — but cannot by itself say which is responsible for a given reading.

**What $HHI_{\text{flat}}$ is and is not.** $\pi$ is a distribution over *quadruples* $(i,k,k',j)$: it treats the same exporter–importer flow routed through two different channels as two distinct outcomes. It is therefore a **channel-level** concentration measure, not the bilateral concentration of trade. The bilateral HHI of the reconstructed flows sums over channels *before* squaring:

$$
HHI_{\text{bilat}} = \sum_{i,j}\Big(\sum_{k,k'}\pi_{i,k,k',j}\Big)^2 \;\ge\; \sum_{i,j}\sum_{k,k'}\pi_{i,k,k',j}^2 = HHI_{\text{flat}}
$$

(squaring a sum of non-negatives always dominates summing the squares), with equality only when no $(i,j)$ pair receives flow from more than one channel. So $HHI_{\text{flat}}$ systematically *understates* bilateral concentration, and the gap grows with channel overlap. Both numbers are legitimate; they answer different questions ("how concentrated is the channel structure" vs "how concentrated are the realized bilateral flows") and should be reported side by side rather than conflated.

### V.2 The exact covariance decomposition

Define $\tilde g_{k,k'} = g_{k,k'}^2/HHI_F$ — itself a valid probability distribution over hub-pairs, since $\sum_{k,k'}g_{k,k'}^2 = HHI_F$ by construction. By the algebraic identity $\mathbb{E}[XY]=\mathbb{E}[X]\mathbb{E}[Y]+\mathrm{Cov}(X,Y)$ applied under $\tilde g$:

$$
\boxed{\; HHI_{\text{flat}} = HHI_F \cdot \Big(\mu_a\mu_b + \mathrm{Cov}_{\tilde g}(a,b)\Big) \;}
$$

with $\mu_a=\mathbb{E}_{\tilde g}[a_k]$, $\mu_b=\mathbb{E}_{\tilde g}[b_{k'}]$. This holds **exactly**, for any core matrix and any hub-level concentrations — no independence or homogeneity assumption required. The new, third-order object this introduces:

$$
\text{Alignment covariance} = \mathrm{Cov}_{\tilde g}\big(HHI_k^{\text{exp}}, HHI_{k'}^{\text{imp}}\big)
$$

positive when internally-tight hubs preferentially link to other internally-tight hubs (concentration compounds in the joint measure); negative when tight hubs are linked mainly to diffuse ones (concentration is diluted); zero exactly when $HHI_{\text{flat}}$ factors into the naive product of marginals.

### V.3 Reconciling $\mu_a$ with the Level-1 measure $HHI^{\text{exp}}$

$\mu_a$ is $\tilde g$-weighted (squared-linkage-weighted); $HHI^{\text{exp}}$ from III.2 is $w$-weighted (linear-volume-weighted) — these generally differ. Writing the conditional linkage distribution of hub $k$ as $h_{k,k'}=g_{k,k'}/w_k$, define its own concentration — the **linkage concentration of hub $k$**:

$$
HHI_k^{F,\text{row}} = \sum_{k'} h_{k,k'}^2
$$

Since $\sum_{k'}g_{k,k'}^2 = w_k^2\,HHI_k^{F,\text{row}}$:

$$
\mu_a = \sum_k w_k\,a_k\cdot\underbrace{\frac{w_k\,HHI_k^{F,\text{row}}}{HHI_F}}_{\displaystyle\phi_k}, \qquad \sum_k w_k\phi_k=1
$$

$\mu_a = HHI^{\text{exp}}$ exactly iff $\phi_k=1$ for every hub — i.e. iff a hub's volume and the concentration of its own linkage pattern are not systematically related across hubs. If large hubs also happen to funnel flow through few counterpart hubs, $\mu_a$ exceeds $HHI^{\text{exp}}$.

### V.4 Full decomposition tree

$$
HHI_{\text{flat}} = \underbrace{HHI_F}_{\text{linkage concentration}} \times \Big(\underbrace{\mu_a\mu_b}_{\text{linkage-weighted means}} + \underbrace{\mathrm{Cov}_{\tilde g}(a,b)}_{\text{alignment}}\Big)
$$

with $\mu_a,\mu_b$ reconciled to the simpler volume-weighted $HHI^{\text{exp}}, HHI^{\text{imp}}$ via $HHI_k^{F,\text{row}}, HHI_{k'}^{F,\text{col}}$ (V.3).

| Level | Object | Answers |
|---|---|---|
| 0 | $a_k, b_{k'}$ | How concentrated is this specific hub, country-wise? |
| 1 | $HHI^{\text{exp}}, HHI^{\text{imp}}$ | How concentrated is each side of trade, volume-weighted on average? |
| — | $HHI_F$, $HHI_k^{F,\text{row}}$ | How concentrated is the hub-to-hub linkage structure, globally and per hub? |
| — | $\mathrm{Cov}_{\tilde g}(a,b)$ | Do concentrated hubs preferentially link to other concentrated hubs? |
| 2 | $HHI_{\text{flat}}$ | The single joint concentration of world trade — a lossless function of all of the above, and nothing coarser reconstructs it in general. |

**Numerical illustration** (three synthetic $3\times3$ core matrices, identical marginals, different linkage patterns):

| Scenario | $HHI_F$ | $HHI^{\text{exp}}=HHI^{\text{imp}}$ | $\mathrm{Cov}_{\tilde g}(a,b)$ | $HHI_{\text{flat}}$ |
|---|---|---|---|---|
| Homogeneous hub concentration | 0.184 | 0.500 / 0.400 | 0.000 | 0.0367 |
| Concentrated hubs linked together | 0.240 | 0.596 / 0.596 | +0.025 | 0.1231 |
| Concentrated hubs linked to diffuse ones | 0.229 | 0.500 / 0.500 | −0.075 | 0.0402 |

Identical marginal concentrations in the second and third rows still produce joint concentrations differing by more than 3×, driven entirely by the alignment covariance. **The one-sided HHIs are not sufficient statistics for the joint measure; the alignment covariance is a necessary, and generally non-negligible, third ingredient.**

---

## Part VI — Practical notes for NNF-MFM estimation

- **Non-negativity is what makes the whole geometric picture clean.** Every measure above needs genuine non-negative shares summing to 1. Signed loadings (e.g. orthonormal/PCA-style factorizations) would require squaring before applying the L1-then-L2 route, and $|F_t|$ or $F_t^2$ in place of $F_t$ throughout Part V to avoid cancellation.
- **What our estimator actually is — approximately, not exactly, non-negative.** This repo does *not* fit an NMF. It estimates the factor space spectrally (Chen et al. MFM eigendecomposition, signed loadings) and then rotates within that fixed column space to the basis minimizing negative mass — which the rotation experiment (docs/notes/nonneg-rotation-experiment.md) showed is unique and coincides with varimax for this data. Residual negative entries are small but nonzero. Two consequences: (i) before applying anything above, **clip negatives to zero and renormalize** the loading columns into shares — track the clipped mass as a per-period diagnostic, since a jump in it means the admissible-basis approximation degraded that month; (ii) the "check sensitivity to initialization" advice standard for NMF does not apply here — basis uniqueness was established directly. **Open item:** fit a true NMF (e.g. multiplicative updates or HALS on the pooled data), which is free to leave the spectral subspace entirely, and compare both fit and hub compositions against the rotate-then-clip basis. If the two agree, the cheap spectral route is vindicated; if not, the difference is itself a finding about what the spectral subspace misses.
- **Scale indeterminacy.** NNF has a free positive-diagonal rescaling between $R$, $C$, $F_t$. Harmless here because every quantity is computed from normalized shares ($p^{(k)}, q^{(k')}, g$), which absorb the scale freedom — provided normalization is applied per-factor (Part II's $\sigma_k, \tau_{k'}$ pushed into $F_t$), not globally.
- **Sparsity.** Bilateral trade has many near-zero pairs; near-zero NNF loadings are usually a genuine "not a hub member" signal, but confirm against a numerical tolerance before it inflates effective hub sizes.
- **Time dimension.** All measures can be computed per period from $F_t$ directly, producing full concentration/fragmentation-over-time series — useful for tracking whether hub-linkage alignment (V.2) is strengthening or weakening as a fragmentation indicator.
- **Aggregation order matters.** Averaging $HHI_k$ then inverting is not the same as averaging $1/HHI_k$ then inverting (Jensen's inequality). Decide upfront whether the headline object is "average concentration" or "average effective hub size" and keep the aggregation order consistent with that choice throughout.
- **Concentration is not market power.** Everything above is flows accounting — the measurement layer. Whether a concentrated position confers pricing power depends on substitutability, which no HHI can see: the repo's canonical example is Mexico's near-monopoly on US server assembly, contested away within one quarter of the 2025 tariffs, versus Taiwan's position in boards, defended with an order-of-magnitude unit-value increase. The right use of these measures is as the *left-hand side* of that comparison: compute upstream (origin-side) and downstream (destination-side) concentration per segment, then test whether they predict where realized pricing power (unit-value behavior under stress) actually appeared. Where concentration and power diverge, the divergence localizes the substitution elasticities — which is what the structural model is after.
