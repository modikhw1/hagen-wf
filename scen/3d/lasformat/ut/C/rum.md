# Room estimates (metres)

Distances: horizontal person-root clearance to object footprint; walls: perpendicular to fitted plane.

Floor used: -1.676 m; rendered difference from golv_h: 0.00 cm. Independent depth difference: None cm; verified: False.
Ingen kameraparallax: Monokulärt MoGe-djup; metrisk skala antagen, inte verifierad mot COLMAP

| Object | Size X × Y × Z (m) | Support frames |
|---|---:|---:|

| Wall | Camera path min / median / max (m) |
|---|---:|
| wall_1 | 2.2904 / 2.2904 / 2.2904 |
| wall_2 | 0.2719 / 0.2719 / 0.2719 |

| Person | Target | Min / median / max (m) |
|---|---|---:|
| 1 | wall_1 | 1.8509 / 1.8537 / 1.8567 |
| 1 | wall_2 | 0.5539 / 0.557 / 0.5601 |
| 3 | wall_1 | 0.8003 / 0.8264 / 1.0069 |
| 3 | wall_2 | 1.3721 / 1.4313 / 1.4527 |

Model licences: ../../RUM-LICENSES.md. Scale, incomplete surfaces and object support are retained in rum.json.

Antaganden: Metrisk rumsskala och ytor från MoGe, inte uppmätta med parallax; Kameraposen från varld.npz; världsskala k=1 är en konvention; Uppåtriktning från kropparnas ryggar; Fokal från sekvens; COLMAP-skattning med få rutor eller antagen max(bredd, höjd); Golv: Starkaste tillgängliga cue-familj: fotter. Svagare cues ändrar inte golvet.
