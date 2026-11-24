# Room estimates (metres)

Distances: horizontal person-root clearance to object footprint; walls: perpendicular to fitted plane.

Floor used: -1.450 m; rendered difference from golv_h: 0.00 cm. Independent depth difference: None cm; verified: False.
Ingen kameraparallax: Monokulärt MoGe-djup; metrisk skala antagen, inte verifierad mot COLMAP

| Object | Size X × Y × Z (m) | Support frames |
|---|---:|---:|
| bar_counter_1 (bar counter) | 0.93 × 0.32 × 0.67 | 9 |
| prop_1 (card payment terminal) | 0.80 × 0.61 × 0.64 | 8 |

| Wall | Camera path min / median / max (m) |
|---|---:|

| Person | Target | Min / median / max (m) |
|---|---|---:|
| 1 | bar_counter_1 | 0.0 / 0.1058 / 0.2349 |
| 1 | prop_1 | 0.0 / 0.0524 / 0.181 |
| 2 | bar_counter_1 | 0.0 / 0.1599 / 0.2923 |
| 2 | prop_1 | 0.0 / 0.0 / 0.1702 |

Model licences: ../../RUM-LICENSES.md. Scale, incomplete surfaces and object support are retained in rum.json.

Antaganden: Metrisk rumsskala och ytor från MoGe, inte uppmätta med parallax; Kameraposen från varld.npz; världsskala k=1 är en konvention; Uppåtriktning från kropparnas ryggar; Fokal från sekvens; COLMAP-skattning med få rutor eller antagen max(bredd, höjd); Golv: antagen kamerahöjd 1.45 m
