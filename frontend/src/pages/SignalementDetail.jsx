import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import './SignalementDetail.css';

function SignalementDetail() {
  const { id } = useParams();
  const user = JSON.parse(localStorage.getItem('user'));

  const [signalement, setSignalement] = useState(null);
  const [commentaires, setCommentaires] = useState([]);
  const [preuvesVisible, setPreuvesVisible] = useState(false);
  const [nouveauCommentaire, setNouveauCommentaire] = useState('');
  const [voteStatus, setVoteStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [voteError, setVoteError] = useState('');
  const [commentError, setCommentError] = useState('');

  useEffect(() => {
    api.get(`/signalements/${id}/`).then(({ data }) => {
      setSignalement(data);
      setLoading(false);
    }).catch(() => {
      setError('Signalement introuvable.');
      setLoading(false);
    });

    api.get('/commentaires/', { params: { signalement: id } }).then(({ data }) => {
      const items = data.results || data;
      setCommentaires(Array.isArray(items) ? items : []);
    }).catch(() => {});
  }, [id]);

  const handleVote = async (type) => {
    if (!user) return window.location.href = '/connexion';
    setVoteError('');
    try {
      await api.post('/votes/', {
        id_signalement: parseInt(id),
        type_vote: type,
      });
      setVoteStatus(type);
      const { data } = await api.get(`/signalements/${id}/`);
      setSignalement(data);
    } catch (err) {
      setVoteError(err.response?.data?.error || 'Erreur lors du vote. Vérifiez que vous êtes connecté.');
    }
  };

  const handleComment = async (e) => {
    e.preventDefault();
    if (!user) return window.location.href = '/connexion';
    if (!nouveauCommentaire.trim()) return;
    setCommentError('');

    try {
      const { data } = await api.post('/commentaires/', {
        id_signalement: parseInt(id),
        contenu: nouveauCommentaire.trim(),
      });
      setCommentaires([...commentaires, {
        ...data,
        auteur_nom: `${user.prenom} ${user.nom}`,
      }]);
      setNouveauCommentaire('');
    } catch (err) {
      setCommentError(err.response?.data?.error || err.response?.data?.contenu || 'Erreur lors de l\'ajout du commentaire.');
    }
  };

  if (loading) return <div className="detail-loading">Chargement...</div>;
  if (error) return <div className="detail-error">{error}</div>;
  if (!signalement) return null;

  const typeLabels = {
    faux_vendeur: 'Faux vendeur',
    phishing: 'Phishing',
    usurpation_identite: "Usurpation d'identité",
    produit_non_livre: 'Produit non livré',
    autre: 'Autre',
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: '2-digit' });
  };

  return (
    <div className="detail-page">
      <header className="detail-header">
        <Link to="/" className="detail-logo">
          <span>🛡️</span>
          <span>Anti-Arnaque</span>
        </Link>
        <div className="detail-header-actions">
          {user ? (
            <Link to="/profil" className="btn-detail-header">{user.prenom}</Link>
          ) : (
            <>
              <Link to="/connexion" className="btn-detail-outline">Connexion</Link>
              <Link to="/inscription" className="btn-detail-solid">Inscription</Link>
            </>
          )}
        </div>
      </header>

      <main className="detail-main">
        <div className="detail-card">
          <div className="detail-contact">
            <div className="contact-avatar">
              {(signalement.profil_vendeur || signalement.numero_telephone || '?').charAt(0).toUpperCase()}
            </div>
            <div className="contact-info">
              <span className="contact-phone">{signalement.numero_telephone || 'Non renseigné'}</span>
              <span className="contact-seller">{signalement.profil_vendeur || ''}</span>
            </div>
          </div>

          <p className="detail-subtitle">
            Détail du signalement — <strong>{typeLabels[signalement.type_arnaque] || signalement.type_arnaque}</strong>
          </p>

          <div className="detail-description">
            <p>{signalement.description}</p>
          </div>

          <div className="detail-actions">
            {signalement.preuves && signalement.preuves.length > 0 && (
              <button
                className="btn-preuves"
                onClick={() => setPreuvesVisible(!preuvesVisible)}
              >
                {preuvesVisible ? 'Masquer les preuves' : 'Voir preuves'}
              </button>
            )}

            <div className="vote-buttons">
              <button
                className={`vote-btn vote-confirm ${voteStatus === 'up' ? 'active' : ''}`}
                onClick={() => handleVote('up')}
              >
                <span className="vote-icon">♥</span>
                <span>Confirme</span>
                <span className="vote-count">{signalement.votes_up || 0}</span>
              </button>
              <button
                className={`vote-btn vote-refuse ${voteStatus === 'down' ? 'active' : ''}`}
                onClick={() => handleVote('down')}
              >
                <span className="vote-icon">✕</span>
                <span>Je refuse</span>
                <span className="vote-count">{signalement.votes_down || 0}</span>
              </button>
            </div>
          </div>
          {voteError && <p className="vote-error-msg">{voteError}</p>}

          {preuvesVisible && signalement.preuves && (
            <div className="preuves-list">
              {signalement.preuves.map((p) => (
                <div key={p.id_preuve} className="preuve-item">
                  <a href={p.fichier_url} target="_blank" rel="noreferrer">
                    📎 {p.type_fichier.toUpperCase()} — Preuve {p.id_preuve}
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>

        <section className="commentaires-section">
          <div className="commentaires-header">
            <h2>Commentaires</h2>
          </div>

          <form className="comment-form" onSubmit={handleComment}>
            <textarea
              placeholder="Ajoutez un commentaire..."
              value={nouveauCommentaire}
              onChange={(e) => setNouveauCommentaire(e.target.value)}
              rows={3}
            />
            {commentError && <p className="comment-error-msg">{commentError}</p>}
            <button type="submit" className="btn-ajouter">Ajouter</button>
          </form>

          <div className="commentaires-list">
            {commentaires.length === 0 && (
              <p className="no-comments">Aucun commentaire pour le moment.</p>
            )}
            {commentaires.map((c) => (
              <div key={c.id_commentaire} className="comment-card">
                <div className="comment-avatar">
                  {(c.auteur_nom || 'U').charAt(0).toUpperCase()}
                </div>
                <div className="comment-body">
                  <div className="comment-meta">
                    <strong>{c.auteur_nom || 'Utilisateur'}</strong>
                    <span>{formatDate(c.date_commentaire)}</span>
                  </div>
                  <p>{c.contenu}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default SignalementDetail;
