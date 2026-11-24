# Room estimates (metres)

Distances: horizontal person-root clearance to object footprint; walls: perpendicular to fitted plane.

Floor used: -1.450 m; rendered difference from golv_h: 0.00 cm. Independent depth difference: None cm; verified: False.
Ingen kameraparallax: Monokulärt MoGe-djup; metrisk skala antagen, inte verifierad mot COLMAP

| Object | Size X × Y × Z (m) | Support frames |
|---|---:|---:|
| prop_1 (table) | 0.34 × 0.18 × 1.18 | 8 |
| prop_2 (table) | 1.26 × 0.56 × 0.99 | 8 |
| prop_3 (chair) | 0.93 × 0.55 × 0.95 | 8 |
| prop_4 (chair) | 1.32 × 0.33 × 0.96 | 8 |

| Wall | Camera path min / median / max (m) |
|---|---:|
| wall_1 | 0.337 / 0.337 / 0.337 |

| Person | Target | Min / median / max (m) |
|---|---|---:|
| 1 | wall_1 | 0.6162 / 0.621 / 0.6521 |
| 1 | prop_1 | 1.9808 / 2.0038 / 2.1847 |
| 1 | prop_2 | 0.4731 / 0.4957 / 0.6759 |
| 1 | prop_3 | 0.3324 / 0.3468 / 0.4948 |
| 1 | prop_4 | 0.2946 / 0.3046 / 0.3316 |

Model licences: ../../RUM-LICENSES.md. Scale, incomplete surfaces and object support are retained in rum.json.

Antaganden: Metrisk rumsskala och ytor från MoGe, inte uppmätta med parallax; Kameraposen från varld.npz; världsskala k=1 är en konvention; Uppåtriktning från kropparnas ryggar; Fokal från sekvens; COLMAP-skattning med få rutor eller antagen max(bredd, höjd); Golv: antagen kamerahöjd 1.45 m
