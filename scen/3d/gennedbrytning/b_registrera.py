"""0017 del B: registrera ett resultat mot originalet (ORB + homografi) och mät ändring utanför personmasken efter registreringen."""
import json, sys
import cv2, numpy as np
def reg(orig, res, maskfil):
    a = cv2.imread(orig); b = cv2.imread(res); m = cv2.imread(maskfil, 0)
    o = cv2.ORB_create(5000); ka, da = o.detectAndCompute(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY), (m == 0).astype(np.uint8)); kb, db = o.detectAndCompute(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY), None)
    mt = sorted(cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db), key=lambda x: x.distance)[:800]
    A = np.float32([ka[x.queryIdx].pt for x in mt]); B = np.float32([kb[x.trainIdx].pt for x in mt])
    H, inl = cv2.findHomography(B, A, cv2.RANSAC, 3.0)
    w = cv2.warpPerspective(b, H, (a.shape[1], a.shape[0]))
    d = np.abs(a.astype(np.int16) - w.astype(np.int16)).max(2); ute = (m == 0) & (w.sum(2) > 0)
    # skala och förskjutning av bildens mitt
    c = H @ np.array([b.shape[1] / 2, b.shape[0] / 2, 1.]); c = c[:2] / c[2]
    return dict(inliers=int(inl.sum()), skala_x=round(float(np.hypot(H[0, 0], H[1, 0])), 4), skala_y=round(float(np.hypot(H[0, 1], H[1, 1])), 4),
                mitt_forskjutning_px=[round(float(c[0] - a.shape[1] / 2), 1), round(float(c[1] - a.shape[0] / 2), 1)],
                andel_andrad_utanfor_efter_reg=round(float((d[ute] > 12).mean()), 4), medelfel_utanfor_efter_reg=round(float(d[ute].mean()), 2)), w
if __name__ == '__main__':
    r, w = reg(*sys.argv[1:4]); print(json.dumps(r)); 
    if len(sys.argv) > 4: cv2.imwrite(sys.argv[4], w)
