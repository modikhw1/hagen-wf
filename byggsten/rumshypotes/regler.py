"""Rumshjärnans allmänna regler.

Reglerna gäller alla klipp inomhus, inte ett visst klipp. Talen är egna startvärden,
inga krav. De ska kalibreras mot biblioteket (2000+ klipp) när riktiga observationer finns.

Lagren (prioritet): hårda regler (fysik, identitet) väger tyngst, sedan mätningar
(stråle, väggar, Manhattan), sedan svaga ledtrådar (ljus, blick, typiska mått).
Strukturpriserna (Occam) avgör mellan hypoteser som passar lika bra.
"""

R = dict(
    # --- mätningar (sigma i residualerna)
    sigma_manhattan_deg=3.0,     # rummets axlar ur flyktpunkter
    sigma_ljus_deg=20.0,         # huvudljusets riktning
    sigma_blick_deg=25.0,        # blickens riktning (kroppens vändning är en svag ledtråd till blicken)
    vid_avstand_m=0.75,          # sittande persons avstånd till bordets mitt
    sigma_vid_m=0.15,
    sigma_pa_m=0.30,             # föremål på bord
    sigma_vagg_pa_m=0.05,        # dörr i vägg
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
    svag_prior_m=30.0,           # mot rummets mitt; bara för att lösningen ska vara bestämd
    rum_typ_m=8.0,
    sigma_rum_typ_m=10.0,
    rum_min_m=2.5,
    # --- struktur (log-sannolikhet i nats)
    pris_entitet=1.5,            # varje möbel eller dörr mer än nödvändigt
    pris_smasak=0.5,             # små föremål finns ofta i flera likadana exemplar (muggar)
    pris_bakgrundsbord=0.3,      # bord utan någon av rollerna: lokaler har många bord
    pris_flytt=6.0,              # en person byter plats utan att det syns (ovanligt mitt i en scen)
    pris_nytt_rum=6.0,           # klippet hör till ett annat rum
    p_miss_fast=0.10,            # en fast sak som borde synas men saknas
    p_miss_foremal=0.40,         # små föremål saknas ofta (flyttade, skymda)
    synlighet_max_sigma_m=0.5,   # saker med osäkrare läge ger ingen negativ evidens
    synlighet_marginal_m=0.4,    # kameran måste se så här långt förbi saken för att den borde synas
    rum_lika_samma=0.90,         # samma rumsnyckel om samma rum
    rum_lika_annat=0.30,         # samma rumsnyckel om annat rum i samma lokal
    # --- sökning och utdata
    beam=8,
    omprovning_min_p=0.75,       # ett byte av tro under detta loggas som vacklan, inte omprövning
    zon_troskel_m=0.6,           # osäkerhet över detta blir en zon i scenen
)

# Pris för ännu ett exemplar av ett föremål, efter typ i nyckeln: vanliga saker finns på många bord,
# märkta burkar och flaskor är ovanligare. Okänd typ: R["pris_smasak"].
FOREMAL_PRIS = {"mugg": 0.3, "kopp": 0.3, "glas": 0.3, "bricka": 0.3, "burk": 2.5, "flaska": 2.5}

REGLER_TEXT = [
    ("R1 Strålen", "Monokulärt djup ger ett avlångt sannolikhetsfält längs strålen: skarpt i sidled, osäkert i djup."),
    ("R2 Manhattan", "Väggar och möbler står i rät vinkel. Varje klipp ger kamerans vridning modulo 90°, men bara när bilden visar en tydlig rät vinkel (koncentration R ≥ 0,6). Vinklar, ljus, blick och väggar är mjuka ledtrådar med robust kostnad."),
    ("R3 Ljuset", "Huvudljuset har en fast riktning i rummet. Det bryter 90°- och 180°-tvetydigheten mellan klipp."),
    ("R4 Identitet", "Samma person eller unikt föremål är samma sak. En generisk möbel är en kandidat, och valet är en hypotes."),
    ("R5 Occam", "Färre möbler föredras tills evidensen kräver fler."),
    ("R6 Blicken", "En blick ger riktning, aldrig avstånd (Kuleshov)."),
    ("R7 Synlighet", "Det som borde synas men saknas sänker hypotesen, prövat i bildplanet mot det kalibrerade djupet. Personer upptäcks nästan alltid: de räknas om de inte är tydligt skymda. Små föremål kostar lite (de flyttas). Bara saker med känt läge räknas."),
    ("R8 Fri yta", "Det kameran ser igenom är tomt. Låga möbler skymmer inte."),
    ("R9 Väggar", "Allt står inom rummet. Ett väggavstånd binder kameran mot väggen."),
    ("R10 Samma rum", "Delade rumsnycklar (vägg, golv, tak) väger mot priset för ett nytt rum."),
    ("R11 Kontakt", "En sittande person sitter vid ett bord, och ett föremål ligger på ett bord."),
    ("R12 Stillhet", "Personer står kvar inom en scen. En flytt är tillåten men kostar."),
    ("R13 Kollision", "Bord och personer står inte i varandra, och kameran står inte i en person."),
    ("R18 Kameran över bordet", "En kamera som ser en bordsskiva ovanifrån står högre än skivan."),
    ("R20 Gamla kopplingar prövas om", "Efter varje klipp prövas att dela saker som kopplats ihop över flera klipp; delningen behålls om den förklarar bättre."),
    ("R21 Golvet som linjal", "Djupet rättas affint (skala och förskjutning) bara där golvet syns över minst 1 m djup; annars ren skala mot kroppen. Två nära ankare (kropp, bord) bestämmer inte lutningen."),
    ("R19 Kroppen är linjalen", "Monokulärt djup har okänd skala per tagning; kroppens storlek (SAM) kalibrerar den."),
    ("R14 Golvet", "Allt står på z = 0 (gäller receptet och 3D-steget)."),
    ("R15 Bordet framför", "En sittande person bakom ett bord sitter cirka 0,55 m bakom bordets mitt; personens djup förankrar bordets."),
    ("R16 Många bord", "Ett bord utan någon av rollerna är billigt att lägga till; bara rollernas bord är få."),
    ("R17 Föremålens identitet", "Ännu ett exemplar av ett föremål kostar efter typ: muggar är vanliga, märkta burkar ovanliga."),
]
