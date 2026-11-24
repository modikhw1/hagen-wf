"""Lokal förskjutning mellan original och registrerad V2 på ytor originalet ser (utanför personen, utan överlagrad text).
DIS optiskt flöde (tätt): median och 90-percentil av |flöde| i px, normalt vid 540 px bredd, valfritt i full upplösning. Fångar det som affin registrering
missar: perspektivskifte och inklistrat ankarinnehåll (Gemini-granskningen 21 nov: 8/8 falskt släppta var ankarbetingade).
"""
from __future__ import annotations
import cv2, numpy as np


def rest_px(org, reg, synlig, bredd=540):
    """BGR och bool-mask i samma storlek. bredd=None mäter i originalets fulla upplösning."""
    if org is None or reg is None or org.shape != reg.shape or synlig.shape != org.shape[:2]:
        raise ValueError('rest_px: bilder och synlighetsmask har olika form')
    synlig = synlig.astype(bool)
    a = cv2.cvtColor(org, cv2.COLOR_BGR2GRAY); b = cv2.cvtColor(reg, cv2.COLOR_BGR2GRAY)
    s = float(bredd) / a.shape[1] if bredd is not None else 1.0
    if abs(s - 1) > 1e-3:
        a = cv2.resize(a, None, fx=s, fy=s, interpolation=cv2.INTER_AREA); b = cv2.resize(b, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        synlig = cv2.resize(synlig.astype(np.uint8), (a.shape[1], a.shape[0]), interpolation=cv2.INTER_NEAREST).astype(bool)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    f = dis.calc(a, b, None); mag = np.linalg.norm(f, axis=-1)
    # bara strukturerade pixlar (gradient) räknas: på släta ytor är flödet obestämt
    gx = cv2.Sobel(a, cv2.CV_32F, 1, 0); gy = cv2.Sobel(a, cv2.CV_32F, 0, 1); g = np.hypot(gx, gy)
    m = synlig & (g > np.percentile(g[synlig], 60) if synlig.any() else synlig)
    if m.sum() < 500:
        return None
    return {'median_px': round(float(np.median(mag[m])), 2), 'p90_px': round(float(np.percentile(mag[m], 90)), 2), 'n': int(m.sum())}
