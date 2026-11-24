# Room estimates (metres)

Distances: horizontal person-root clearance to object footprint; walls: perpendicular to fitted plane.

Floor used: -2.010 m; rendered difference from golv_h: 0.00 cm. Independent depth difference: None cm; verified: False.
Ingen kameraparallax: Monokulärt MoGe-djup; metrisk skala antagen, inte verifierad mot COLMAP

| Object | Size X × Y × Z (m) | Support frames |
|---|---:|---:|

| Wall | Camera path min / median / max (m) |
|---|---:|
| wall_1 | 3.0882 / 3.0882 / 3.0882 |
| wall_2 | 2.6858 / 2.6858 / 2.6858 |

| Person | Target | Min / median / max (m) |
|---|---|---:|
| 1 | wall_1 | 1.3578 / 1.3663 / 1.3691 |
| 1 | wall_2 | 1.0785 / 1.0863 / 1.0889 |
| 2 | wall_1 | 0.8063 / 0.8122 / 0.813 |
| 2 | wall_2 | 0.639 / 0.6442 / 0.6449 |

Model licences: ../../RUM-LICENSES.md. Scale, incomplete surfaces and object support are retained in rum.json.

Antaganden: Metrisk rumsskala och ytor från MoGe, inte uppmätta med parallax; Kameraposen från varld.npz; världsskala k=1 är en konvention; Uppåtriktning från kropparnas ryggar; Fokal från sekvens; COLMAP-skattning med få rutor eller antagen max(bredd, höjd); Golv: Starkaste tillgängliga cue-familj: fotter. Svagare cues ändrar inte golvet.
