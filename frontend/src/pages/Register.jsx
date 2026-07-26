import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Register.css';

function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
    setServerError('');
  };

  const validate = () => {
    const errs = {};
    if (!formData.nom.trim()) errs.nom = 'Le nom est requis';
    if (!formData.prenom.trim()) errs.prenom = 'Le prénom est requis';
    if (!formData.email.trim()) errs.email = 'L\'email est requis';
    if (formData.password.length < 8) errs.password = 'Minimum 8 caractères';
    if (formData.password !== formData.confirmPassword) errs.confirmPassword = 'Les mots de passe ne correspondent pas';
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
      await api.post('/auth/register/', {
        nom: formData.nom.trim(),
        prenom: formData.prenom.trim(),
        email: formData.email.trim(),
        password: formData.password,
      });
      navigate('/connexion');
    } catch (err) {
      const data = err.response?.data;
      if (data?.email) {
        setErrors({ email: Array.isArray(data.email) ? data.email[0] : data.email });
      } else if (data?.error) {
        setServerError(data.error);
      } else {
        setServerError('Une erreur est survenue. Veuillez réessayer.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-page">
      <Link to="/" className="accueil-btn">Accueil</Link>

      <div className="register-container">
        <h1>INSCRIPTION</h1>

        {serverError && <div className="error-message">{serverError}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="nom">Nom</label>
              <input
                type="text"
                id="nom"
                name="nom"
                value={formData.nom}
                onChange={handleChange}
                placeholder="Dupont"
                className={errors.nom ? 'input-error' : ''}
              />
              {errors.nom && <span className="field-error">{errors.nom}</span>}
            </div>
            <div className="form-group">
              <label htmlFor="prenom">Prénom</label>
              <input
                type="text"
                id="prenom"
                name="prenom"
                value={formData.prenom}
                onChange={handleChange}
                placeholder="Jean"
                className={errors.prenom ? 'input-error' : ''}
              />
              {errors.prenom && <span className="field-error">{errors.prenom}</span>}
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="exemple@email.com"
              className={errors.email ? 'input-error' : ''}
            />
            {errors.email && <span className="field-error">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Mot de passe</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
              className={errors.password ? 'input-error' : ''}
            />
            {errors.password && <span className="field-error">{errors.password}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirmer le mot de passe</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder="••••••••"
              className={errors.confirmPassword ? 'input-error' : ''}
            />
            {errors.confirmPassword && <span className="field-error">{errors.confirmPassword}</span>}
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Inscription en cours...' : "S'inscrire"}
          </button>
        </form>

        <p className="switch-auth">
          Déjà un compte ? <Link to="/connexion">Se connecter</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;
