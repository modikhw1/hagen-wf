# Semantiska ändringar som operationer (Claude översatte meningarna). Spelas upp mot en ny bas: bash andringar.sh
cd "$(dirname "$0")/../.."
P=".venv/Scripts/python.exe py/scenop.py"
# 1 'Ångra Lumas pizzabyte hos kvinnan, hamburgaren tillbaka'
$P byt_foremal --var roll:A --fran pizzabit --till hamburgare
# 2 'Punchline ska landa: kameran åker långsamt in mot henne i S6'
$P kamera --scen S6 --mot S6:A --zoom 1.35
# 3 'Servitören ska titta mot kvinnan, inte bort, och tagningen ska vara kortare'
$P spegla --skikt S4:C
$P langd --scen S4 --s 1.6
# 4 'I kroken: ta bort burken, flytta muggen närmare henne'
$P dolj --skikt S1:burk
$P flytta --skikt S1:pappmugg --dx 0.10 --dy -0.01
# 5 'Mannens förvirring i slutet ska förstärkas, avsluta med att kameran åker in på honom'
$P rorelse --skikt S7:B --styrka 2.5
$P duplicera --scen S7 --ny S8
$P kamera --scen S8 --mot S8:B --zoom 2.2
$P langd --scen S8 --s 1.4
# 6 'Låt servitören stå i bakgrunden bakom kvinnan i hennes punchline'
#   Claude: bakom = lägre z än A (0.40) men framför väggen; bakgrund = högre upp i bild och mindre (perspektiv).
#   Fönster/bakvägg ligger överst i S6 (rum-ankare); golvlinjen bakom henne ~ y 0.55. Höjd 0.38 ger en person längre bort.
$P lagg_till --scen S6 --fran personer:C --x 0.82 --y 0.60 --hojd 0.40 --z 0.25 --spegel ja
# 7 'Kvinnans tagningar ska kännas mer stressade'
#   Claude: stress = mer rörelse i kroppen + tätare klipp. Tre operationer per tagning.
for s in S1 S3 S6; do $P rorelse --skikt $s:A --styrka 2.0; done
$P langd --scen S1 --s 1.9
$P langd --scen S3 --s 1.5
