import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../services/api';
import './SignalementsList.css';

function SignalementsList() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [signalements, setSignalements] = useState([]);
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const q = searchParams.get('q');
    const url = q ? `/signalements/rechercher/?q=${encodeURIComponent(q)}` : '/signalements/';

    setLoading(true);
    api.get(url).then(({ data }) => {
      const items = data.results || data;
      setSignalements(Array.isArray(items) ? items : []);
      setLoading(false);
    }).catch(() => {
      setError('Erreur lors du chargement des signalements.');
      setLoading(false);
    });
  }, [searchParams]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (query.trim()) {
      setSearchParams({ q: query.trim() });
    } else {
      setSearchParams({});
    }
  };

  const typeLabels = {
    faux_vendeur: 'Faux vendeur',
    phishing: 'Phishing',
    usurpation_identite: "Usurpation d'identité",
    produit_non_livre: 'Produit non livré',
    autre: 'Autre',
  };

  return (
    <div className="list-page">
      <header className="list-header">
        <Link to="/" className="list-logo"><span>🛡️</span><span>Anti-Arnaque</span></Link>
        <div className="list-header-actions">
          <Link to="/signalement" className="btn-list-primary">Signaler</Link>
          <Link to="/" className="btn-list-ghost">Accueil</Link>
        </div>
      </header>

      <main className="list-main">
        <form className="list-search" onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Rechercher par numéro ou profil vendeur..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button type="submit">Rechercher</button>
        </form>

        {error && <div className="list-error">{error}</div>}

        {loading ? (
          <p className="list-loading">Chargement...</p>
        ) : signalements.length === 0 ? (
          <p className="list-empty">Aucun signalement trouvé.</p>
        ) : (
          <div className="list-grid">
            {signalements.map((s) => (
              <Link to={`/signalements/${s.id_signalement}`} key={s.id_signalement} className="list-card">
                <div className="list-card-header">
                  <div className="list-avatar">{(s.auteur_nom || 'U').charAt(0).toUpperCase()}</div>
                  <div className="list-card-info">
                    <span className="list-author">{s.auteur_nom || 'Utilisateur'}</span>
                    <span className="list-date">{s.date_signalement ? new Date(s.date_signalement).toLocaleDateString('fr-FR') : ''}</span>
                  </div>
                  <span className="list-score">{s.score}</span>
                </div>
                <div className="list-card-body">
                  <span className="list-type">{typeLabels[s.type_arnaque] || s.type_arnaque}</span>
                  {s.numero_telephone && <span className="list-phone">📞 {s.numero_telephone}</span>}
                  {s.profil_vendeur && <span className="list-seller">👤 {s.profil_vendeur}</span>}
                </div>
                <div className="list-card-footer">
                  <span className={`list-badge ${s.statut === 'confirme' || s.statut === 'approuve' ? 'badge-red' : 'badge-orange'}`}>
                    {s.statut_display || s.statut}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

export default SignalementsList;
