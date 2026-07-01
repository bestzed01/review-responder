import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './Dashboard.jsx'
import './App.css'

// This is the routing layer: it maps a URL pattern to a component.
// When a business owner visits yoursite.com/dashboard/biz_a8f3k2,
// React Router matches the ":slug" pattern and passes "biz_a8f3k2"
// into the Dashboard component as a URL param (see Dashboard.jsx,
// where we read it with useParams()).
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/dashboard/:slug" element={<Dashboard />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}

function NotFound() {
  return (
    <div style={{ padding: '4rem', textAlign: 'center', fontFamily: 'system-ui' }}>
      <h1>No dashboard here</h1>
      <p>Check the link your provider sent you.</p>
    </div>
  )
}

export default App
