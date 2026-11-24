# Bildtrohet i slutkameran

Exakta MHR70–riggledpar projiceras genom planens slutliga renderkamera och jämförs med samma rutors cachade 2D-leder. Medeloffset anges i slutbildspixlar och andel av bildhöjden; skalfaktor och bbox-IoU bygger på samma synliga ledpars omslutningar. Den äldre ingestkamerakontrollen finns per roll under ingestkamera.

Egna diagnostiska trösklar: 3 % av bildhöjden är en tydligt synlig förskjutning (31 px vid 576x1024), 15 % är ett märkbart byte av bildstorlek och IoU 0,65 återanvänder den äldre ledkontrollens undre gräns. Inga ägarkrav.
{'offset_bildhojdandel': 0.03, 'skalfaktor_min': 0.85, 'skalfaktor_max': 1.15, 'bbox_iou': 0.65}

| Scen/person | medel px/% höjd | skala | IoU | flaggad |
|---|---|---|---|---|
| s1/A | 24.09/1.25 % | 1.013 | 0.926 | False |
| s2/A | 338.46/17.63 % | 1.034 | 0.714 | True |
