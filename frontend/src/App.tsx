import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useEffect, lazy, Suspense } from 'react'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => { window.scrollTo(0, 0) }, [pathname])
  return null
}

const Home = lazy(() => import('./pages/Home'))
const Event = lazy(() => import('./pages/Event'))
const BuyTicket = lazy(() => import('./pages/BuyTicket'))
const Profile = lazy(() => import('./pages/Profile'))
const Login = lazy(() => import('./pages/Login'))
const Signup = lazy(() => import('./pages/Signup'))
const Unsubscribe = lazy(() => import('./pages/Unsubscribe'))
const Callback = lazy(() => import('./pages/Callback'))
const NotFound = lazy(() => import('./pages/NotFound'))
const AdminLayout = lazy(() => import('./pages/admin/AdminLayout'))
const AdminPeople = lazy(() => import('./pages/admin/People'))
const AdminPersonDetail = lazy(() => import('./pages/admin/PersonDetail'))
const AdminEvents = lazy(() => import('./pages/admin/Events'))
const AdminEventDetail = lazy(() => import('./pages/admin/EventDetail'))
const AdminEventForm = lazy(() => import('./pages/admin/EventForm'))
const AdminVenues = lazy(() => import('./pages/admin/Venues'))
const AdminVenueDetail = lazy(() => import('./pages/admin/VenueDetail'))
const AdminVenueForm = lazy(() => import('./pages/admin/VenueForm'))
const AdminPersonForm = lazy(() => import('./pages/admin/PersonForm'))
const AdminDrinks = lazy(() => import('./pages/admin/Drinks'))
const AdminStats = lazy(() => import('./pages/admin/Stats'))

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Suspense>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/event/:id" element={<Event />} />
          <Route path="/buy-ticket" element={<BuyTicket />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/unsubscribe" element={<Unsubscribe />} />
          <Route path="/callback/*" element={<Callback />} />
          <Route path="/ameriatransactionstate" element={<Callback />} />
          <Route path="/bindingpayment" element={<Callback />} />
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
            <Route path="stats" element={<AdminStats />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
