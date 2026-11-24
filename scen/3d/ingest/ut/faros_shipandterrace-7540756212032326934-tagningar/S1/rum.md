# Room estimates (metres)

Distances: horizontal person-root clearance to object footprint; walls: perpendicular to fitted plane.

Floor used: -1.424 m; rendered difference from golv_h: 0.00 cm. Independent depth difference: -1.0935183443068652 cm; verified: True.
Ingen kameraparallax: Monokulärt MoGe-djup; metrisk skala antagen, inte verifierad mot COLMAP

| Object | Size X × Y × Z (m) | Support frames |
|---|---:|---:|

| Wall | Camera path min / median / max (m) |
|---|---:|
| wall_1 | 0.655 / 0.655 / 0.655 |
| wall_2 | 4.3515 / 4.3515 / 4.3515 |

| Person | Target | Min / median / max (m) |
|---|---|---:|
| 1 | wall_1 | 0.4887 / 0.6452 / 0.7379 |
| 1 | wall_2 | 0.3338 / 1.1504 / 1.5794 |
| 2 | wall_1 | 0.7863 / 0.9329 / 1.0385 |
| 2 | wall_2 | 2.0115 / 2.2416 / 2.4251 |

Model licences: ../../RUM-LICENSES.md. Scale, incomplete surfaces and object support are retained in rum.json.

Antaganden: Metrisk rumsskala och ytor från MoGe, inte uppmätta med parallax; Kameraposen från varld.npz; världsskala k=1 är en konvention; Uppåtriktning från kropparnas ryggar; Fokal från sekvens; COLMAP-skattning med få rutor eller antagen max(bredd, höjd); Golv: Starkaste tillgängliga cue-familj: fotter. Svagare cues ändrar inte golvet.
