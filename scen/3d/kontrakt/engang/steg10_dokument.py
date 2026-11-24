"""Uppdatera filtabeller och den nya dataavgränsningen."""
from steg10_filer import andra
from steg10_koppla import ersatt


def readme(s):
    s = ersatt(s, 'så att resultatet kan renderas om i Blender.', 'så att en upplöst plan kan visas och exporteras. Den interaktiva visaren och det planerade slututseendet flyttas till webbläsaren; Blender används för ingest/export. Det befintliga Blender-renderflödet finns kvar.')
    marker = '| `kalla_prop.py`, `prop_referenser.json` |'
    pos = s.index(marker)
    s = s[:pos] + '| `kalla_handelser.py`, `handelser.py` | Lokala händelser med ursprung/konfidens; tidsankare på källklockan och förekomster efter scenredigering. Se `HANDELSER.md`. |\n| `proptid.py` | Ordnade propändringar över delar av en scen. Hand-/ytfästen löses sedan av `propplan.py`. |\n| `../ingest/kallstatus.py` | Varnar direkt när ingest ändrar mätfiler som ett känt källmanifest hashlåser. |\n' + s[pos:]
    s = s.replace('`test_kroppmatt.py`, `test_props.py`', '`test_kroppmatt.py`, `test_props.py`, `test_handelser.py`')
    s = s.replace('test_kroppmatt test_props`', 'test_kroppmatt test_props test_handelser`')
    s = s.replace('| `kalla_omhasha.py` | Ny källkopia efter lokalt omräknade ingestfiler; originalet bevaras. |', '| `kalla_omhasha.py` | Ny manifestkopia eller uttrycklig `--uppdatera` med originalbackup och ändringslogg. Ändrat händelseunderlag måste mätas om. |')
    return s + '''
## Steg 10, återupptagning med props som data

Aktuell granskning och reproducerbara kommandon finns i
`ut/aterupptagning/rapport.md`. `kalla_handelser.json` för b och notan innehåller
props och lokala händelser; övriga klipp har `kalla_prop.json`.
Nya dataresultat ligger i `ut/<klipp>/data_prop/`: regi, plan och kvalitet,
utan byggd film. Provet med den uttryckligen påhittade produkten ligger i
`ut/b/data_prop_byte/`. Händelsestyrda byten har egna data-mappar.

Planens befintliga backendnamn är fortfarande `blender_mhr`. Ingen
webbläsaradapter infördes i detta uppdrag. Propbankens former, grepppunkter,
upplösta 4×4-matriser, synlighet och händelser är data som en sådan adapter
kan läsa. `ingest/prop_blender.py` och den tidigare kamerahanden finns kvar
bakom sina befintliga gränssnitt; ingen ny Blenderbyggnad eller rendering
gjordes i återupptagningen. Gamla `tom3`, `jamn_tom` och den redan färdiga
`jamn_tom_rattad` är bevarade.

`test_plats_snapshot.py` är stöd till platsprovens historiska indata, inte
en pipelineingång. Frysta stödposer och deras ursprung beskrivs i
`testdata/README.md`. Engångsverktyg för återupptagningen ligger i `engang/`.
'''


def props(s):
    a=s.index('scen/.venv/Scripts/python.exe scen/3d/kontrakt/kor_klipp.py')
    b=s.index('\n```',a)
    s=s[:a]+'scen/.venv/Scripts/python.exe scen/3d/kontrakt/kompilera.py scen/3d/kontrakt/ut/b/kalla_prop.json scen/3d/kontrakt/ut/b/regi_prop_tom.json scen/3d/kontrakt/ut/b/ny_data_plan.json'+s[b:]
    s=s.replace('Filerna skapas bara om utmålet saknas. Ett tungt steg i taget. Bakgrunds-Blender\nhittas genom konstanten i `ingest_klipp.py`; ingen öppen Blender används.',
        'Källbyggaren kräver en ny utfil. Välj alltid en ny planplats manuellt: kompilatorn kan skriva över sin utfil. Ett tungt steg i taget. Den nya avgränsningen gäller data och plan, utan nya renderingar. Befintlig Blenderkod behålls bakom sitt gränssnitt och utvidgas inte.')
    s=s.replace('Handen är kamerafäst och byggs som två\nprimitiver.', 'Handen är kamerafäst i den redan införda Blenderbyggaren som två\nprimitiver; ingen ny propfilm har verifierat den.')
    s=s.replace('En handöverräckning inom en scen modelleras ännu\ninte:', 'En handöverräckning inom en scen modelleras ännu\ninte automatiskt:')
    return s + '\nHändelser och edits från/till en händelse beskrivs i `HANDELSER.md`. Kvalitetsraderna kräver ingen rendering. `byggd` är det äldre fältnamnet för att geometri/matriser är upplösta i planen, inte att Blender har körts. Den aktuella omfattningen och verifieringen står i `ut/aterupptagning/rapport.md`.\n'

andra('scen/3d/kontrakt/README.md',readme)
andra('scen/3d/kontrakt/PROPS.md',props)
andra('scen/3d/kontrakt/engang/README.md',lambda s:s+'''
Återupptagning av steg 10: `steg10_filer.py` bevarar original/radslut;
`steg10_koppla.py`, `steg10_kontroller.py`, `steg10_sista_kod.py` och
`steg10_bakkompat.py` är engångsinkopplingar och ska inte köras igen.
`steg10_prov.py` kör begärda prov sekventiellt från projektroten.
`steg10_dokument.py` uppdaterar dokumentationen en gång.
''')
