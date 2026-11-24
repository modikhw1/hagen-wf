"""Fysikaliska, geometriska och strukturella regler för Förvärldens Kärna (R1–R22).

Lagren (prioritet):
1. Hårda regler (fysik, golv, kollision, identitet) har små sigma.
2. Mätningar (stråle, väggar, Manhattan, kontakt) har medelstora sigma.
3. Svaga ledtrådar (ljus, blick, typmått) har mjuka L1-residualer.
4. Strukturpriser (Occam + visuell särdragskoppling R22) avgör mellan hypoteser.
"""

R = dict(
    # --- mätningar (sigma i residualerna)
    sigma_manhattan_deg=3.0,     # rummets axlar ur flyktpunkter / väggnormaler
    sigma_ljus_deg=20.0,         # huvudljusets riktning
    sigma_blick_deg=25.0,        # blickens riktning
    vid_avstand_m=0.65,          # sittande persons vågräta avstånd till bordets mitt (R11/R15)
    sigma_vid_m=0.15,
    sigma_pa_m=0.30,             # föremål på bord (vågrätt avstånd till bordets mitt)
    sigma_vagg_pa_m=0.05,        # dörr/fönster i vägg
    # --- hårda regler (små sigma)
    sigma_inne_m=0.05,           # allt inom rummet
    marginal_vagg_m=0.15,
    kamera_fri_radie_m=0.35,     # kameran står inte i en person
    kamera_fri_bord_m=0.30,
    sigma_kropp_m=0.05,
    bord_minsta_avstand_m=1.0,   # två bord står inte i varandra
    person_minsta_avstand_m=0.5, # två personer står inte i varandra
    sigma_kollision_m=0.05,
    # --- svaga priorer
    svag_prior_m=30.0,           # svag sammanhållning mot rummets mitt för obundna noder
    rum_typ_m=8.0,
    sigma_rum_typ_m=10.0,
    rum_min_m=2.5,
    # --- struktur (log-sannolikhet i nats)
    pris_entitet=1.5,            # varje roll-möbel eller dörr mer än nödvändigt
    pris_smasak=0.5,             # generiska småsaker
    pris_bakgrundsbord=0.3,      # bord utan någon av rollerna
    pris_flytt=6.0,              # en person byter plats utan att det syns
    pris_nytt_rum=6.0,           # klippet hör till ett annat rum
    bonus_samma_distinkt_pa_bord=2.0,  # R22: när ett distinkt föremål (t.ex. burk) står på ett bord som delas
    p_miss_fast=0.10,            # en fast sak som borde synas men saknas
    p_miss_foremal=0.40,         # små föremål saknas ofta (flyttade, skymda)
    synlighet_max_sigma_m=0.5,   # saker med osäkrare läge ger ingen negativ evidens
    synlighet_marginal_m=0.4,    # kameran måste se så här långt förbi saken för att den borde synas
    rum_lika_samma=0.90,         # samma rumsnyckel om samma rum
    rum_lika_annat=0.30,         # samma rumsnyckel om annat rum
    # --- sökning och utdata
    beam=8,
    omprovning_min_p=0.75,
    zon_troskel_m=0.6,
)

# Pris för ännu ett exemplar av ett föremål efter typ i nyckeln.
# Märkta burkar/flaskor är starka identitetsankare mellan tagningar.
FOREMAL_PRIS = {
    "mugg": 0.4,
    "kopp": 0.4,
    "glas": 0.4,
    "bricka": 0.4,
    "burk": 3.2,
    "flaska": 3.2,
    "bonaqua": 3.5,
}
