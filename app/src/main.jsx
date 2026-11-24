import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import Forandring from './forandring/Forandring.jsx'
import Bibliotek from './bibliotek/Bibliotek.jsx'
import Kalibrering from './kalibrering/Kalibrering.jsx'
import Brygga from './brygga/Brygga.jsx'
import Rekon from './rekon/Rekon.jsx'
import Bedom from './bedom/Bedom.jsx'
import Forandring2D from './forandring/Forandring2D.jsx'
import Bedom2D from './bedom/Bedom2D.jsx'
import Bank from './bank/Bank.jsx'
import Felskydd from './Felskydd.jsx'
import './styles.css'

// #1 … #6 är kundrummet. #v är videoförändring. #bibliotek är analysen av riktiga klipp.
// #rekon visar rekonstruerade klipp bredvid originalen. #v2/<id> är reglaget på originalvideon (2D),
// #bedom2d/<id> bedömningar på riktig video (två virtuella kameror).
// #bank visar urvalet av träningsdata och egna bedömningar.
// #kalibrering tränar vertikalerna på parvisa bedömningar. #brygga jämför motorn med analysen.
const h = location.hash
const Vy = h.startsWith('#bedom2d') ? Bedom2D : h.startsWith('#v2') ? Forandring2D : h.startsWith('#bedom') ? Bedom : h.startsWith('#bank') ? Bank : h.startsWith('#rekon') ? Rekon : h.startsWith('#brygga') ? Brygga : h.startsWith('#kalibrering') ? Kalibrering : h.startsWith('#bibliotek') ? Bibliotek : h.startsWith('#v') ? Forandring : App
createRoot(document.getElementById('root')).render(<Felskydd><Vy /></Felskydd>)

addEventListener('hashchange', () => location.reload())
