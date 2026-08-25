import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Profile.css';

function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [signalements, setSignalements] = useState([]);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({ nom: '', prenom: '', email: '' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem('user'));
    if (!stored) {
      navigate('/connexion');
      return;
    }

    api.get('/auth/me/').then(({ data }) => {
      setUser(data);
      setFormData({ nom: data.nom, prenom: data.prenom, email: data.email });
      setLoading(false);

      // On ne filtre qu'une fois qu'on a l'utilisateur authentifié réel
      // (via /auth/me/), pas la copie potentiellement obsolète dans
      // localStorage -- id_utilisateur doit venir de la même source que
      // ce qu'on compare pour éviter tout décalage de forme de données.
      api.get('/signalements/').then(({ data: sigData }) => {
        const items = sigData.results || sigData;
        const mine = Array.isArray(items)
          ? items.filter(s => s.id_utilisateur === data.id_utilisateur)
          : [];
        setSignalements(mine);
      }).catch(() => {});
    }).catch(() => {
      localStorage.removeItem('user');
      navigate('/connexion');
    });
  }, [navigate]);

  const handleLogout = async () => {
    try { await api.post('/auth/logout/'); } catch {}
    localStorage.removeItem('user');
    navigate('/connexion');
  };

  const handleSave = async () => {
    try {
      const { data } = await api.patch('/auth/me/', {
        nom: formData.nom.trim(),
        prenom: formData.prenom.trim(),
        email: formData.email.trim(),
      });
      setUser(data);
      setEditing(false);
    } catch {
      // ignore
    }
  };

  if (loading || !user) return <div className="profile-loading">Chargement...</div>;

  const typeLabels = {
    faux_vendeur: 'Faux vendeur',
    phishing: 'Phishing',
    usurpation_identite: "Usurpation d'identité",
    produit_non_livre: 'Produit non livré',
    autre: 'Autre',
  };

  return (
    <div className="profile-page">
      <header className="profile-header">
        <Link to="/" className="profile-logo"><span>🛡️</span><span>Anti-Arnaque</span></Link>
        <div className="profile-header-actions">
          <Link to="/signalement" className="btn-header-action btn-primary-light">Signaler</Link>
          <Link to="/" className="btn-header-action btn-ghost-light">Accueil</Link>
          <button onClick={handleLogout} className="btn-header-action btn-outline-danger">Déconnexion</button>
        </div>
      </header>

      <main className="profile-main">
        <div className="profile-grid">

          <div className="profile-left">
            <div className="card profile-card">
              <div className="avatar-large">
                {(user.prenom || 'U').charAt(0).toUpperCase()}
              </div>
              <h2 className="profile-name">{user.nom?.toUpperCase()}</h2>
              <p className="profile-pseudo">{user.prenom?.toLowerCase()}{user.nom?.toLowerCase()}</p>
            </div>

            <div className="card stats-card">
              <h3>Statistiques</h3>
              <div className="stats-grid">
                <div className="stat-box">
                  <span className="stat-val">{signalements.length}</span>
                  <span className="stat-lbl">Signalements</span>
                </div>
                <div className="stat-box">
                  <span className="stat-val">{user.signalements_count || 0}</span>
                  <span className="stat-lbl">Total créés</span>
                </div>
              </div>
            </div>
          </div>

          <div className="profile-right">
            <div className="card">
              <h3>Mes signalements</h3>
              {signalements.length === 0 ? (
                <p className="empty-msg">Aucun signalement pour le moment.</p>
              ) : (
                <div className="signalements-grid">
                  {signalements.slice(0, 6).map(s => (
                    <Link to={`/signalements/${s.id_signalement}`} key={s.id_signalement} className="signalement-thumb">
                      <span className="thumb-type">{typeLabels[s.type_arnaque] || s.type_arnaque}</span>
                      <span className={`thumb-status ${s.statut === 'confirme' || s.statut === 'approuve' ? 'status-red' : 'status-orange'}`}>
                        {s.statut_display || s.statut}
                      </span>
                      <span className="thumb-score">Score: {s.score}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <div className="card info-card">
              <div className="info-header">
                <h3>Information sur le compte</h3>
                {!editing && (
                  <button className="btn-modifier" onClick={() => setEditing(true)}>Modifier</button>
                )}
              </div>

              <div className="info-fields">
                <div className="info-row">
                  <label>Nom</label>
                  {editing ? (
                    <input value={formData.nom} onChange={e => setFormData({...formData, nom: e.target.value})} />
                  ) : (
                    <span>{user.nom}</span>
                  )}
                </div>
                <div className="info-row">
                  <label>Prénom</label>
                  {editing ? (
                    <input value={formData.prenom} onChange={e => setFormData({...formData, prenom: e.target.value})} />
                  ) : (
                    <span>{user.prenom}</span>
                  )}
                </div>
                <div className="info-row">
                  <label>Email</label>
                  {editing ? (
                    <input value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})} />
                  ) : (
                    <span>{user.email}</span>
                  )}
                </div>
                <div className="info-row">
                  <label>Date d'inscription</label>
                  <span>{user.date_inscription ? new Date(user.date_inscription).toLocaleDateString('fr-FR') : '—'}</span>
                </div>
              </div>

              {editing && (
                <div className="info-actions">
                  <button className="btn-save" onClick={handleSave}>Enregistrer</button>
                  <button className="btn-cancel" onClick={() => { setEditing(false); setFormData({ nom: user.nom, prenom: user.prenom, email: user.email }); }}>Annuler</button>
                </div>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

export default Profile;