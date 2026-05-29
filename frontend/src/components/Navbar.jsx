import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { Shield, LogOut } from 'lucide-react';
import './Navbar.css';

const Navbar = () => {
    const { user, logout } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <nav className="glass navbar">
            <div className="container nav-content">
                <Link to="/" className="nav-brand">
                    <Shield className="brand-icon" size={28} />
                    <span>ASAAP</span>
                </Link>
                
                <div className="nav-links">
                    {user ? (
                        <>
                            <span className="user-greeting">Hi, {user.fullName}</span>
                            <button className="btn btn-danger btn-sm" onClick={handleLogout}>
                                <LogOut size={16} /> Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="nav-link">Login</Link>
                            <Link to="/register" className="btn btn-primary btn-sm">Register</Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
