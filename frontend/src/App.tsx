import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
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
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/app" element={<Home />} />
        <Route path="/app/event/:id" element={<Event />} />
        <Route path="/app/buy-ticket" element={<BuyTicket />} />
        <Route path="/app/profile" element={<Profile />} />
        <Route path="/app/about" element={<About />} />
        <Route path="/app/login" element={<Login />} />
        <Route path="/app/signup" element={<Signup />} />
        <Route path="/app/policy" element={<Policy />} />
        <Route path="/app/unsubscribe" element={<Unsubscribe />} />
        <Route path="/app/callback/*" element={<Callback />} />
        <Route path="/app/*" element={<NotFound />} />
        <Route path="*" element={<Navigate to="/app" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
