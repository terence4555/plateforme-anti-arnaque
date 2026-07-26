import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import SignalementDetail from './pages/SignalementDetail';
import SignalementCreate from './pages/SignalementCreate';
import Profile from './pages/Profile';
import Chatbot from './components/Chatbot';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/connexion" element={<Login />} />
        <Route path="/inscription" element={<Register />} />
        <Route path="/signalement" element={<SignalementCreate />} />
        <Route path="/signalements/:id" element={<SignalementDetail />} />
        <Route path="/profil" element={<Profile />} />
      </Routes>
      <Chatbot />
    </BrowserRouter>
  );
}

export default App;
