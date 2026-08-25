import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Home.css';

function Home() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user'));
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState({ signalements: 0, utilisateurs: 0, verification: 0 });
  const [recentSignalements, setRecentSignalements] = useState([]);

  useEffect(() => {
    api.get('/signalements/stats/').then(({ data }) => {
      setStats({
        signalements: data.total || 0,
        utilisateurs: data.utilisateurs || 0,
        verification: 92,
      });
    }).catch(() => {});

    api.get('/signalements/?page_size=5').then(({ data }) => {
      const items = data.results || data;
      setRecentSignalements(Array.isArray(items) ? items.slice(0, 5) : []);
    }).catch(() => {});
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/signalements?q=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/');
    } catch {
      // ignore
    } finally {
      localStorage.removeItem('user');
      window.location.reload();
    }
  };

  const typeLabels = {
    faux_vendeur: 'Faux vendeur',
    phishing: 'Phishing',
    usurpation_identite: 'Usurpation d\'identité',
    produit_non_livre: 'Produit non livré',
    autre: 'Autre',
  };

  return (
    <div className="home-page">
      <header className="header">
        <div className="header-inner">
          <Link to="/" className="logo">
            <span className="shield-icon">🛡️</span>
            <span className="logo-text">Anti-Arnaque</span>
          </Link>
          <div className="header-actions">
            {user ? (
              <>
                <Link to="/profil" className="header-user">{user.prenom}</Link>
                <button onClick={handleLogout} className="btn-header btn-outline-light">Déconnexion</button>
              </>
            ) : (
              <>
                <Link to="/connexion" className="btn-header btn-outline-light">Connexion</Link>
                <Link to="/inscription" className="btn-header btn-solid-light">S'inscrire</Link>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="hero">
        <div className="hero-inner">
          <h1>
            <span className="hero-blue">PROTÉGEZ-VOUS</span>{' '}
            <span className="hero-dark">CONTRE LES ARNAQUES EN LIGNE</span>
          </h1>
          <p className="hero-subtitle">
            Vérifiez un vendeur, signalez une fraude, protégez la communauté
          </p>
          <form className="search-bar" onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Entrez un numéro de téléphone/email ou un profil vendeur"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="btn-verify">Vérifier</button>
          </form>
        </div>
      </section>

      <section className="stats-section">
        <div className="stat-item">
          <span className="stat-icon">🔔</span>
          <span className="stat-number">{stats.signalements.toLocaleString()}</span>
          <span className="stat-label">Signalements</span>
        </div>
        <div className="stat-item">
          <span className="stat-icon">👥</span>
          <span className="stat-number">{stats.utilisateurs.toLocaleString()}</span>
          <span className="stat-label">Utilisateurs</span>
        </div>
        <div className="stat-item">
          <span className="stat-icon">🛡️</span>
          <span className="stat-number">{stats.verification}%</span>
          <span className="stat-label">Arnaques évitées</span>
        </div>
      </section>

      <section className="features-section">
        <div className="feature-card">
          <div className="feature-icon-wrapper warning">⚠️</div>
          <h3>Signaler une arnaque</h3>
          <p>Publiez un signalement avec des preuves pour alerter la communauté.</p>
          <Link to="/signalement" className="feature-link">Signaler maintenant →</Link>
        </div>
        <div className="feature-card">
          <div className="feature-icon-wrapper info">🔍</div>
          <h3>Vérifier un vendeur</h3>
          <p>Recherchez un numéro/email ou un profil pour vérifier sa fiabilité.</p>
          <Link to="/signalements" className="feature-link">Vérifier →</Link>
        </div>
        <div className="feature-card">
          <div className="feature-icon-wrapper success">👥</div>
          <h3>Votes communautaires</h3>
          <p>Contribuez à évaluer la crédibilité des signalements par vos votes.</p>
          <Link to="/signalements" className="feature-link">Voir les signalements →</Link>
        </div>
      </section>

      <section className="recent-section">
        <h2>Signalements Récents</h2>
        <div className="recent-list">
          {recentSignalements.length === 0 && (
            <p className="no-recent">Aucun signalement récent pour le moment.</p>
          )}
          {recentSignalements.map((s) => (
            <Link to={`/signalements/${s.id_signalement}`} key={s.id_signalement} className="recent-card">
              <div className="recent-avatar">
                {(s.auteur_nom || 'U').charAt(0).toUpperCase()}
              </div>
              <div className="recent-info">
                <span className="recent-author">{s.auteur_nom || 'Utilisateur'}</span>
                <span className="recent-desc">
                  {typeLabels[s.type_arnaque] || s.type_arnaque}
                  {s.numero_telephone && ` — ${s.numero_telephone}`}
                  {s.profil_vendeur && ` — ${s.profil_vendeur}`}
                </span>
              </div>
              <div className="recent-right">
                <span className={`badge ${s.statut === 'confirme' || s.statut === 'approuve' ? 'badge-red' : 'badge-orange'}`}>
                  {s.statut === 'confirme' || s.statut === 'approuve' ? 'Arnaque Confirmée' : 'Fraude suspectée'}
                </span>
                <span className={`recent-score ${s.score < 50 ? 'score-low' : ''}`}>
                  {s.score}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <footer className="home-footer">
        <p>&copy; 2026 Anti-Arnaque — Plateforme citoyenne de lutte contre la fraude en ligne</p>
      </footer>
    </div>
  );
}

export default Home;
