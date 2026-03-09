import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { gtagConfig } from './lib/analytics'
import Home from './pages/Home'
import Event from './pages/Event'
import BuyTicket from './pages/BuyTicket'
import Profile from './pages/Profile'
import About from './pages/About'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Policy from './pages/Policy'
import Unsubscribe from './pages/Unsubscribe'
import Callback from './pages/Callback'
import NotFound from './pages/NotFound'

export default function App() {
  useEffect(() => {
    gtagConfig(import.meta.env.DEV ? { debug_mode: true } : {})
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/event/:id" element={<Event />} />
        <Route path="/buy-ticket" element={<BuyTicket />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/about" element={<About />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/policy" element={<Policy />} />
        <Route path="/unsubscribe" element={<Unsubscribe />} />
        <Route path="/callback/*" element={<Callback />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
