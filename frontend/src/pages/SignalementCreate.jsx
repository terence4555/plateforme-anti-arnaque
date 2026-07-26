import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import './SignalementCreate.css';

function SignalementCreate() {
  const navigate = useNavigate();
  const user = JSON.parse(localStorage.getItem('user'));

  const [types, setTypes] = useState([]);
  const [formData, setFormData] = useState({
    numero_telephone: '',
    profil_vendeur: '',
    type_arnaque: '',
    description: '',
  });
  const [fichiers, setFichiers] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get('/signalements/types/').then(({ data }) => {
      setTypes(data);
    }).catch(() => {});
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
  };

  const handleFileChange = (e) => {
    const newFiles = Array.from(e.target.files);
    setFichiers(prev => [...prev, ...newFiles]);

    newFiles.forEach(file => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (ev) => {
          setPreviews(prev => [...prev, { name: file.name, url: ev.target.result }]);
        };
        reader.readAsDataURL(file);
      } else {
        setPreviews(prev => [...prev, { name: file.name, url: null }]);
      }
    });
  };

  const removeFile = (index) => {
    setFichiers(prev => prev.filter((_, i) => i !== index));
    setPreviews(prev => prev.filter((_, i) => i !== index));
  };

  const validate = () => {
    const errs = {};
    if (!formData.description.trim()) errs.description = 'La description est requise';
    if (!formData.type_arnaque) errs.type_arnaque = 'Sélectionnez un type';
    return errs;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setServerError('');

    const errs = validate();
    if (Object.keys(errs).length > 0) {
      setErrors(errs);
      return;
    }

    setLoading(true);
    try {
      const uploadedUrls = [];
      for (const file of fichiers) {
        const fd = new FormData();
        fd.append('fichier', file);
        const { data } = await api.post('/signalements/upload/', fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        uploadedUrls.push(data.url);
      }

      const payload = {
        numero_telephone: formData.numero_telephone.trim() || null,
        profil_vendeur: formData.profil_vendeur.trim() || null,
        type_arnaque: formData.type_arnaque,
        description: formData.description.trim(),
        fichiers_urls: uploadedUrls,
      };

      const { data } = await api.post('/signalements/', payload);
      navigate(`/signalements/${data.id_signalement}`);
    } catch (err) {
      const msg = err.response?.data?.error || err.response?.data?.detail || 'Une erreur est survenue.';
      setServerError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="create-page">
        <header className="create-header">
          <Link to="/" className="create-logo"><span>🛡️</span><span>Anti-Arnaque</span></Link>
          <div className="create-header-actions">
            <Link to="/connexion" className="btn-create-outline">Connexion</Link>
            <Link to="/inscription" className="btn-create-solid">Inscription</Link>
          </div>
        </header>
        <div className="create-auth-required">
          <p>Vous devez être connecté pour signaler une arnaque.</p>
          <Link to="/connexion" className="btn-create-outline">Se connecter</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="create-page">
      <header className="create-header">
        <Link to="/" className="create-logo"><span>🛡️</span><span>Anti-Arnaque</span></Link>
        <Link to="/" className="btn-retour">Retour</Link>
      </header>

      <main className="create-main">
        <form onSubmit={handleSubmit}>
          {serverError && <div className="error-message">{serverError}</div>}

          <section className="section-info">
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="numero_telephone">Numéro</label>
                <input
                  type="text"
                  id="numero_telephone"
                  name="numero_telephone"
                  value={formData.numero_telephone}
                  onChange={handleChange}
                  placeholder="+228 90 00 00 00"
                />
              </div>
              <div className="form-group">
                <label htmlFor="profil_vendeur">Profil / Pseudo</label>
                <input
                  type="text"
                  id="profil_vendeur"
                  name="profil_vendeur"
                  value={formData.profil_vendeur}
                  onChange={handleChange}
                  placeholder="@pseudo_vendeur"
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="type_arnaque">Type d'arnaque</label>
              <select
                id="type_arnaque"
                name="type_arnaque"
                value={formData.type_arnaque}
                onChange={handleChange}
                className={errors.type_arnaque ? 'input-error' : ''}
              >
                <option value="">Sélectionner</option>
                {types.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
              {errors.type_arnaque && <span className="field-error">{errors.type_arnaque}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="description">Description détaillée</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={6}
                placeholder="Décrivez l'arnaque en détail..."
                className={errors.description ? 'input-error' : ''}
              />
              {errors.description && <span className="field-error">{errors.description}</span>}
            </div>
          </section>

          <section className="section-preuves">
            <h2>Preuves (images/pdf)</h2>

            <label className="dropzone" htmlFor="file-input">
              <input
                type="file"
                id="file-input"
                multiple
                accept="image/*,.pdf"
                onChange={handleFileChange}
                hidden
              />
              <div className="dropzone-content">
                <span className="dropzone-plus">+</span>
                <span>Cliquer pour ajouter des preuves</span>
              </div>
            </label>

            {previews.length > 0 && (
              <div className="previews-list">
                {previews.map((p, i) => (
                  <div key={i} className="preview-item">
                    {p.url ? (
                      <img src={p.url} alt={p.name} className="preview-img" />
                    ) : (
                      <span className="preview-icon">📄</span>
                    )}
                    <span className="preview-name">{p.name}</span>
                    <button type="button" className="preview-remove" onClick={() => removeFile(i)}>×</button>
                  </div>
                ))}
              </div>
            )}
          </section>

          <button type="submit" className="btn-signaler" disabled={loading}>
            {loading ? 'Envoi en cours...' : 'Signaler'}
          </button>
        </form>
      </main>
    </div>
  );
}

export default SignalementCreate;
