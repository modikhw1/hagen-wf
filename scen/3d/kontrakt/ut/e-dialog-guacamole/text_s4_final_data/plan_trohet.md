# Bildtrohet i slutkameran

Exakta MHR70–riggledpar projiceras genom planens slutliga renderkamera och jämförs med samma rutors cachade 2D-leder. Medeloffset anges i slutbildspixlar och andel av bildhöjden; skalfaktor och bbox-IoU bygger på samma synliga ledpars omslutningar. Den äldre ingestkamerakontrollen finns per roll under ingestkamera.

Egna diagnostiska trösklar: 3 % av bildhöjden är en tydligt synlig förskjutning (31 px vid 576x1024), 15 % är ett märkbart byte av bildstorlek och IoU 0,65 återanvänder den äldre ledkontrollens undre gräns. Inga ägarkrav.
{'offset_bildhojdandel': 0.03, 'skalfaktor_min': 0.85, 'skalfaktor_max': 1.15, 'bbox_iou': 0.65}

| Scen/person | medel px/% höjd | skala | IoU | flaggad |
|---|---|---|---|---|
| s1/A | 2.56/0.25 % | 1.002 | 0.974 | False |
| s2/B | 3.98/0.39 % | 0.999 | 0.984 | False |
| s3/A | 4.84/0.47 % | 0.998 | 0.939 | False |
| s4/B | 3.52/0.34 % | 1.000 | 0.965 | False |
| s4/A | 0.92/0.09 % | 0.999 | 0.980 | False |
