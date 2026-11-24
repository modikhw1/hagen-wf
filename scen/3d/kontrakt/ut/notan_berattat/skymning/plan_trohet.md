# Bildtrohet i slutkameran

Exakta MHR70–riggledpar projiceras genom planens slutliga renderkamera och jämförs med samma rutors cachade 2D-leder. Medeloffset anges i slutbildspixlar och andel av bildhöjden; skalfaktor och bbox-IoU bygger på samma synliga ledpars omslutningar. Den äldre ingestkamerakontrollen finns per roll under ingestkamera.

Egna diagnostiska trösklar: 3 % av bildhöjden är en tydligt synlig förskjutning (31 px vid 576x1024), 15 % är ett märkbart byte av bildstorlek och IoU 0,65 återanvänder den äldre ledkontrollens undre gräns. Inga ägarkrav.
{'offset_bildhojdandel': 0.03, 'skalfaktor_min': 0.85, 'skalfaktor_max': 1.15, 'bbox_iou': 0.65}

| Scen/person | medel px/% höjd | skala | IoU | flaggad |
|---|---|---|---|---|
| s1/A | 2.72/0.27 % | 1.003 | 0.964 | False |
| s2/B | 6.14/0.60 % | 1.002 | 0.964 | False |
| s3/A | 6.88/0.67 % | 1.013 | 0.943 | False |
| s4/C | 2.62/0.26 % | 1.000 | 0.995 | False |
| s5/B | 5.49/0.54 % | 1.004 | 0.970 | False |
| s6/A | 28.35/2.77 % | 0.993 | 0.929 | False |
| s7/B | 1.88/0.18 % | 0.994 | 0.966 | False |
