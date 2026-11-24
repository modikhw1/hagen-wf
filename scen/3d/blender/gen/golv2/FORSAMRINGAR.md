# Alla numeriska försämringar i de prövade måtten

Små rasternedgångar redovisas också. De är inte belägg för en visuellt märkbar försämring. Kontakter, inklusive alla före/efter-rutor, finns i mobelkontakter.json och sitskontakter.json.

| Ruta | Δ IoU efter−före | Δ synlig IoU | Δ median led px | Δ p90 led px |
|---|---:|---:|---:|---:|
| s1/2 | +0.00013591 | +0.00002513 | +0.00053119 | +0.00001844 |
| s1/70 | -0.00004347 | +0.00000028 | +0.00008619 | -0.00007704 |
| s2/75 | -0.00008913 | -0.00004904 | -0.00001368 | -0.00135004 |
| s2/93 | -0.00012874 | -0.00009467 | +0.00077097 | -0.00030135 |
| s2/111 | -0.00017214 | -0.00009502 | +0.00013966 | +0.00020173 |
| s3/116 | -0.00012532 | -0.00013893 | -0.00001800 | -0.00001948 |
| s3/142 | -0.00010041 | -0.00011697 | +0.00010774 | +0.00028944 |
| s3/168 | +0.00000000 | -0.00007129 | +0.00009737 | -0.00032329 |
| s4/213 | +0.01784193 | +0.01784193 | +0.00011587 | -0.00004764 |
| s4/253 | +0.01430898 | +0.01430898 | +0.00032986 | -0.00004408 |
| s5/258 | -0.00022420 | -0.00009663 | -0.00059666 | +0.00017630 |
| s5/268 | -0.00008181 | -0.00004542 | -0.00001511 | +0.00049928 |
| s5/278 | -0.00014224 | -0.00010350 | -0.00009689 | +0.00018180 |
| s6/283 | -0.00006142 | +0.00000000 | -0.00006271 | -0.00019937 |
| s6/309 | -0.00006278 | +0.00000000 | +0.00027815 | -0.00006735 |
| s7/360 | +0.00038971 | +0.00039401 | -0.00011902 | +0.00021966 |

## Rekvisita, samtliga befintliga källregioner

Beräknad bankforms omslutning, samma geometri/matriser som Blender. Källboxarna är tidigare manuellt avlästa, inte objektmasker. Dessa referensrutor är inte exakt de 21 renderprovrutorna. Breddkvot 1 vore lika bred som källregionen.

| Scen/prop/källruta | Centrumfel före → efter px | Breddkvot före → efter | Försämring |
|---|---:|---:|---|
| s1/prop_o1/24 | 25.345528 → 23.013511 | 1.946957 → 1.978775 | bredd |
| s1/prop_o1/48 | 29.037720 → 23.013511 | 1.947151 → 1.978775 | bredd |
| s2/prop_o1/86 | 123.735523 → 152.681435 | 2.232490 → 2.312601 | centrum, bredd |
| s2/prop_o1/100 | 123.608489 → 152.681435 | 2.231346 → 2.312601 | centrum, bredd |
| s3/prop_o1/133 | 35.389078 → 102.852869 | 2.111027 → 2.287529 | centrum, bredd |
| s3/prop_o1/152 | 34.441664 → 102.852869 | 2.111073 → 2.287529 | centrum, bredd |
| s5/prop_o1/264 | 38.080821 → 38.080821 | 1.812683 → 1.812683 | ingen |
| s5/prop_o1/272 | 24.618470 → 24.618470 | 1.908798 → 1.908798 | ingen |
| s6/prop_o1/299 | 26.809355 → 26.809355 | 1.958645 → 1.958645 | ingen |
| s6/prop_o1/318 | 26.409257 → 26.809355 | 1.963868 → 1.958645 | centrum |
| s7/prop_o1/352 | 17.088109 → 45.118380 | 1.947143 → 2.207489 | centrum, bredd |
| s7/prop_o1/367 | 17.333742 → 45.118380 | 1.946402 → 2.207489 | centrum, bredd |
| s1/prop_burk_kallbild/24 | 61.712481 → 61.712481 | 1.674798 → 1.674798 | ingen |
| s1/prop_burk_kallbild/48 | 65.086368 → 61.712481 | 1.678490 → 1.674798 | ingen |
| s3/prop_burk_kallbild/133 | 50.498939 → 70.109684 | 1.850174 → 2.020032 | centrum, bredd |
| s3/prop_burk_kallbild/152 | 51.139059 → 70.109684 | 1.850125 → 2.020032 | centrum, bredd |
| s6/prop_burk_kallbild/299 | 62.147877 → 62.147877 | 1.654453 → 1.654453 | ingen |
| s6/prop_burk_kallbild/318 | 61.266691 → 62.147877 | 1.659678 → 1.654453 | centrum |

S4/C: sulhöjden ökar från cirka 0 till 10,4–11,9 cm. S7 saknar synlig sits före och efter. Före/efter-bordskontakter ska läsas som led mot mallmöbel, inte som bevisad handkontakt; personer gestikulerar.
