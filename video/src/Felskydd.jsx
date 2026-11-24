import { Component } from 'react'

// Visar felet i stället för en blank sida, med en knapp för att ladda om.
export default class Felskydd extends Component {
  constructor(props) {
    super(props)
    this.state = { fel: null }
  }
  static getDerivedStateFromError(fel) { return { fel } }
  componentDidCatch(fel, info) { console.error('Vyn kraschade:', fel, info?.componentStack) }
  render() {
    if (!this.state.fel) return this.props.children
    return (
      <div style={{ padding: 24, maxWidth: 720 }}>
        <h2 style={{ margin: '0 0 8px' }}>Något gick fel i vyn</h2>
        <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, background: 'var(--g1)', padding: 12, borderRadius: 8 }}>{String(this.state.fel?.stack ?? this.state.fel)}</pre>
        <button onClick={() => location.reload()} style={{ border: '1.5px solid var(--ink)', borderRadius: 999, padding: '4px 12px' }}>ladda om</button>
      </div>
    )
  }
}
