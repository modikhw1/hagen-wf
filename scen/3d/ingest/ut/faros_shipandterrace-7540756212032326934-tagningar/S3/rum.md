# Room estimates (metres)

Distances: horizontal person-root clearance to object footprint; walls: perpendicular to fitted plane.

Floor used: -1.100 m; rendered difference from golv_h: 0.00 cm. Independent depth difference: -29.049698383638734 cm; verified: False.
Ingen kameraparallax: Monokulärt MoGe-djup; metrisk skala antagen, inte verifierad mot COLMAP

| Object | Size X × Y × Z (m) | Support frames |
|---|---:|---:|

| Wall | Camera path min / median / max (m) |
|---|---:|
| wall_1 | 4.3446 / 4.3446 / 4.3446 |
| wall_2 | 1.1291 / 1.1291 / 1.1291 |

| Person | Target | Min / median / max (m) |
|---|---|---:|
| 1 | wall_1 | 1.8423 / 2.1365 / 2.4496 |
| 1 | wall_2 | 0.6745 / 0.9134 / 1.1144 |
| 2 | wall_1 | 0.733 / 1.0111 / 1.1675 |
| 2 | wall_2 | 0.9109 / 0.9593 / 1.0275 |

Model licences: ../../RUM-LICENSES.md. Scale, incomplete surfaces and object support are retained in rum.json.

Antaganden: Metrisk rumsskala och ytor från MoGe, inte uppmätta med parallax; Kameraposen från varld.npz; världsskala k=1 är en konvention; Uppåtriktning från kropparnas ryggar; Fokal från sekvens; COLMAP-skattning med få rutor eller antagen max(bredd, höjd); Golv: Starkaste tillgängliga cue-familj: fotter. Svagare cues ändrar inte golvet.
