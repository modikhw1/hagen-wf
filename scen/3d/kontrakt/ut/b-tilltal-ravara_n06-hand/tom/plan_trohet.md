# Bildtrohet i slutkameran

Exakta MHR70–riggledpar projiceras genom planens slutliga renderkamera och jämförs med samma rutors cachade 2D-leder. Medeloffset anges i slutbildspixlar och andel av bildhöjden; skalfaktor och bbox-IoU bygger på samma synliga ledpars omslutningar. Den äldre ingestkamerakontrollen finns per roll under ingestkamera.

Egna diagnostiska trösklar: 3 % av bildhöjden är en tydligt synlig förskjutning (31 px vid 576x1024), 15 % är ett märkbart byte av bildstorlek och IoU 0,65 återanvänder den äldre ledkontrollens undre gräns. Inga ägarkrav.
{'offset_bildhojdandel': 0.03, 'skalfaktor_min': 0.85, 'skalfaktor_max': 1.15, 'bbox_iou': 0.65}

| Scen/person | medel px/% höjd | skala | IoU | flaggad |
|---|---|---|---|---|
| s1/A | 22.77/2.22 % | 1.008 | 0.908 | False |
| s2/A | 12.01/1.17 % | 0.999 | 0.952 | False |
| s3/B | 10.74/1.05 % | 1.006 | 0.951 | False |
| s4/B | 5.12/0.50 % | 1.000 | 0.979 | False |
| s5/C | 13.43/1.31 % | 1.011 | 0.921 | False |
| s6/C | 8.40/0.82 % | 0.998 | 0.966 | False |
| s7/C | 4.30/0.42 % | 1.000 | 0.983 | False |
| s8/C | 15.21/1.49 % | 1.003 | 0.944 | False |
| s9/C | 10.48/1.02 % | 1.000 | 0.966 | False |
| s10/C | 12.60/1.23 % | 1.002 | 0.876 | False |
| s11/C | 18.99/1.85 % | 1.002 | 0.945 | False |
