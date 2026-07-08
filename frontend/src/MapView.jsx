import { useEffect, useRef, useState } from 'react'

const KEY = import.meta.env.VITE_MAPS_API_KEY
const CENTER = { lat: 28.525, lng: 77.255 } // Kalkaji belt, South Delhi PC
const CATEGORY_COLORS = {
  road: '#e2574c', water: '#2f80ed', school: '#f2994a', health: '#9b51e0',
  drainage: '#219653', electricity: '#f2c94c', other: '#828282',
}

let mapsPromise
function loadMaps() {
  if (!KEY) return Promise.reject(new Error('no key'))
  if (!mapsPromise) {
    mapsPromise = new Promise((resolve, reject) => {
      const s = document.createElement('script')
      s.src = `https://maps.googleapis.com/maps/api/js?key=${KEY}&v=weekly`
      s.onload = () => resolve(window.google.maps)
      s.onerror = reject
      document.head.appendChild(s)
    })
  }
  return mapsPromise
}

export default function MapView({ demands, onSelect }) {
  const divRef = useRef(null)
  const mapRef = useRef(null)
  const circlesRef = useRef([])
  const [failed, setFailed] = useState(!KEY)

  useEffect(() => {
    loadMaps()
      .then(maps => {
        if (!divRef.current || mapRef.current) return
        mapRef.current = new maps.Map(divRef.current, {
          center: CENTER, zoom: 13, mapTypeControl: false, streetViewControl: false,
        })
      })
      .catch(() => setFailed(true))
  }, [])

  useEffect(() => {
    const maps = window.google?.maps
    if (!maps || !mapRef.current) return
    circlesRef.current.forEach(c => c.setMap(null))
    circlesRef.current = demands
      .filter(d => d.lat && d.lon)
      .map(d => {
        const circle = new maps.Circle({
          map: mapRef.current,
          center: { lat: d.lat, lng: d.lon },
          radius: 150 + Math.sqrt(d.signal_count) * 120,
          fillColor: CATEGORY_COLORS[d.category] || CATEGORY_COLORS.other,
          fillOpacity: 0.35,
          strokeColor: CATEGORY_COLORS[d.category] || CATEGORY_COLORS.other,
          strokeWeight: 1.5,
        })
        circle.addListener('click', () => onSelect(d.id))
        return circle
      })
  }, [demands])

  if (failed) return <OsmMap demands={demands} onSelect={onSelect} />
  return <div ref={divRef} style={{ height: '52vh', borderRadius: 12, border: '1px solid #e3e8f0' }} />
}

// Fallback: Leaflet + OpenStreetMap — no key, no billing, no Google dependency
function OsmMap({ demands, onSelect }) {
  const divRef = useRef(null)
  const mapRef = useRef(null)
  const circlesRef = useRef([])

  useEffect(() => {
    Promise.all([import('leaflet'), import('leaflet/dist/leaflet.css')]).then(([mod]) => {
      const L = mod.default || mod
      if (!divRef.current || mapRef.current) return
      mapRef.current = L.map(divRef.current).setView([CENTER.lat, CENTER.lng], 13)
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(mapRef.current)
    })
  }, [])

  useEffect(() => {
    import('leaflet').then(mod => {
      const L = mod.default || mod
      if (!mapRef.current) return
      circlesRef.current.forEach(c => c.remove())
      circlesRef.current = demands
        .filter(d => d.lat && d.lon)
        .map(d => {
          const color = CATEGORY_COLORS[d.category] || CATEGORY_COLORS.other
          const circle = L.circle([d.lat, d.lon], {
            radius: 150 + Math.sqrt(d.signal_count) * 120,
            color, fillColor: color, fillOpacity: 0.35, weight: 1.5,
          })
          circle.on('click', () => onSelect(d.id))
          circle.addTo(mapRef.current)
          return circle
        })
    })
  }, [demands])

  return <div ref={divRef} style={{ height: '52vh', borderRadius: 12, border: '1px solid #e3e8f0' }} />
}
