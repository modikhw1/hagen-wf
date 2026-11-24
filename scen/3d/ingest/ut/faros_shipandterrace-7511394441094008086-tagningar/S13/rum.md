# Room estimates (metres)

Distances: horizontal person-root clearance to object footprint; walls: perpendicular to fitted plane.

Floor used: -1.450 m; rendered difference from golv_h: 0.00 cm. Independent depth difference: None cm; verified: False.
Ingen kameraparallax: Monokulärt MoGe-djup; metrisk skala antagen, inte verifierad mot COLMAP

| Object | Size X × Y × Z (m) | Support frames |
|---|---:|---:|

| Wall | Camera path min / median / max (m) |
|---|---:|
| wall_1 | 0.8353 / 0.8353 / 0.8353 |
| wall_2 | 2.1525 / 2.1525 / 2.1525 |

| Person | Target | Min / median / max (m) |
|---|---|---:|
| 1 | wall_1 | 0.3532 / 0.3707 / 0.3724 |
| 1 | wall_2 | 0.2882 / 0.2937 / 0.3093 |
| 2 | wall_1 | 0.343 / 0.3441 / 0.3451 |
| 2 | wall_2 | 0.283 / 0.2866 / 0.2887 |

Model licences: ../../RUM-LICENSES.md. Scale, incomplete surfaces and object support are retained in rum.json.

Antaganden: Metrisk rumsskala och ytor från MoGe, inte uppmätta med parallax; Kameraposen från varld.npz; världsskala k=1 är en konvention; Uppåtriktning från kropparnas ryggar; Fokal från sekvens; COLMAP-skattning med få rutor eller antagen max(bredd, höjd); Golv: Endast kamerahöjdens prior finns.
