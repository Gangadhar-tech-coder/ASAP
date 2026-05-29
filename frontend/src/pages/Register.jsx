import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import './Auth.css';

const Register = () => {
    const [formData, setFormData] = useState({
        email: '', password: '', fullName: '', emergencyContactPhone: '', emergencyContactEmail: ''
    });
    const [error, setError] = useState('');
    const { register } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await register(formData);
            navigate('/login');
        } catch (err) {
            setError('Registration failed. Please try again.');
        }
    };

    return (
        <div className="auth-container">
            <div className="glass-card auth-card fade-in">
                <div className="auth-header">
                    <Shield className="brand-icon" size={48} />
                    <h2>Create Account</h2>
                    <p>Join ASAAP for continuous safety monitoring</p>
                </div>
                
                {error && <div className="auth-error">{error}</div>}
                
                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label>Full Name</label>
                        <input name="fullName" type="text" className="input-field" placeholder="Jane Doe" onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Email Address</label>
                        <input name="email" type="email" className="input-field" placeholder="you@example.com" onChange={handleChange} required />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input name="password" type="password" className="input-field" placeholder="••••••••" onChange={handleChange} required />
                    </div>
                    
                    <div style={{marginTop: '8px', marginBottom: '8px', borderTop: '1px solid var(--border)', paddingTop: '16px'}}>
                        <p style={{fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '12px'}}>Emergency Contact (Required for Alerts)</p>
                        <div className="form-group">
                            <label>Contact Email</label>
                            <input name="emergencyContactEmail" type="email" className="input-field" placeholder="contact@example.com" onChange={handleChange} required />
                        </div>
                    </div>
                    
                    <button type="submit" className="btn btn-primary btn-block">Sign Up</button>
                </form>
                
                <div className="auth-footer">
                    Already have an account? <Link to="/login">Sign in</Link>
                </div>
            </div>
        </div>
    );
};

export default Register;
