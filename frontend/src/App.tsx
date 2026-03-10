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
import AdminLayout from './pages/admin/AdminLayout'
import AdminPeople from './pages/admin/People'
import AdminPersonDetail from './pages/admin/PersonDetail'
import AdminEvents from './pages/admin/Events'
import AdminEventDetail from './pages/admin/EventDetail'
import AdminEventForm from './pages/admin/EventForm'
import AdminVenues from './pages/admin/Venues'
import AdminVenueDetail from './pages/admin/VenueDetail'
import AdminVenueForm from './pages/admin/VenueForm'
import AdminPersonForm from './pages/admin/PersonForm'
import AdminDrinks from './pages/admin/Drinks'

export default function App() {
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
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<Navigate to="/admin/people" replace />} />
          <Route path="people" element={<AdminPeople />} />
          <Route path="people/:id" element={<AdminPersonDetail />} />
          <Route path="people/:id/edit" element={<AdminPersonForm />} />
          <Route path="events" element={<AdminEvents />} />
          <Route path="events/create" element={<AdminEventForm />} />
          <Route path="events/:id" element={<AdminEventDetail />} />
          <Route path="events/:id/edit" element={<AdminEventForm />} />
          <Route path="venues" element={<AdminVenues />} />
          <Route path="venues/create" element={<AdminVenueForm />} />
          <Route path="venues/:id" element={<AdminVenueDetail />} />
          <Route path="venues/:id/edit" element={<AdminVenueForm />} />
          <Route path="drinks" element={<AdminDrinks />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
