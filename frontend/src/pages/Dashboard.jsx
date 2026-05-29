import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import axios from 'axios';
import { Activity, AlertTriangle, ShieldCheck, History } from 'lucide-react';
import './Dashboard.css';

const Dashboard = () => {
    const { user } = useContext(AuthContext);
    const [alerts, setAlerts] = useState([]);
    const [isMonitoring, setIsMonitoring] = useState(false);
    const [triggering, setTriggering] = useState(false);

    const fetchAlerts = async () => {
        try {
            const res = await axios.get('http://localhost:8082/api/alerts/history');
            setAlerts(res.data);
        } catch (error) {
            console.error('Failed to fetch alerts', error);
        }
    };

    useEffect(() => {
        fetchAlerts();
    }, []);

    useEffect(() => {
        let mediaRecorder;
        let stream;

        const startRecording = async () => {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = async (e) => {
                    if (e.data.size > 0) {
                        const formData = new FormData();
                        formData.append('file', e.data, 'audio_chunk.webm');
                        
                        try {
                            const res = await axios.post('http://localhost:8000/api/v1/model/predict', formData);
                            if (res.data.is_distress) {
                                simulateAlert(res.data.confidence);
                            }
                        } catch (error) {
                            console.error('Prediction failed', error);
                        }
                    }
                };

                // Record in 2.5 second chunks
                mediaRecorder.start(2500);
            } catch (err) {
                console.error("Microphone access denied", err);
                setIsMonitoring(false);
            }
        };

        if (isMonitoring) {
            startRecording();
        }

        return () => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, [isMonitoring]);

    const simulateAlert = async (confidence = 0.95) => {
        setTriggering(true);
        try {
            await axios.post('http://localhost:8082/api/alerts/trigger', {
                latitude: 40.7128,
                longitude: -74.0060,
                confidenceScore: confidence,
                emergencyContactEmail: user?.emergencyContactEmail
            });
            await fetchAlerts();
            setTimeout(() => setTriggering(false), 1000);
        } catch (error) {
            console.error('Alert failed', error);
            setTriggering(false);
        }
    };

    if (!user) return null;

    return (
        <div className="container dashboard-container fade-in">
            <header className="dashboard-header">
                <div>
                    <h1>Safety Dashboard</h1>
                    <p>Monitor your safety status and alert history.</p>
                </div>
            </header>

            <div className="dashboard-grid">
                {/* Status Card */}
                <div className="glass-card stat-card">
                    <div className="stat-header">
                        <h3>Live Monitoring</h3>
                        {isMonitoring ? <Activity className="icon-pulse text-success" /> : <ShieldCheck className="text-secondary" />}
                    </div>
                    
                    <div className="status-indicator">
                        <div className={`status-dot ${isMonitoring ? 'active' : ''}`}></div>
                        <span>{isMonitoring ? 'System Active & Listening' : 'System Offline'}</span>
                    </div>

                    <p className="status-desc">
                        {isMonitoring 
                            ? "ASAAP is passively analyzing background audio for distress signals."
                            : "Click start to begin passive audio analysis via the AI Engine."}
                    </p>

                    <div className="status-actions">
                        <button 
                            className={`btn ${isMonitoring ? 'btn-danger' : 'btn-primary'}`} 
                            onClick={() => setIsMonitoring(!isMonitoring)}
                        >
                            {isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'}
                        </button>
                    </div>
                </div>

                {/* Emergency Contact */}
                <div className="glass-card stat-card">
                    <div className="stat-header">
                        <h3>Emergency Contact</h3>
                        <AlertTriangle className="text-warning" />
                    </div>
                    <div className="contact-info">
                        <div className="contact-row">
                            <span>Email:</span>
                            <strong>{user.emergencyContactEmail || 'Not Set'}</strong>
                        </div>
                        <div className="contact-row">
                            <span>Phone:</span>
                            <strong>{user.emergencyContactPhone || 'Not Set'}</strong>
                        </div>
                    </div>
                    <button 
                        className={`btn btn-danger btn-block ${triggering ? 'animate-pulse-danger' : ''}`}
                        onClick={simulateAlert}
                        disabled={triggering}
                        style={{marginTop: 'auto'}}
                    >
                        {triggering ? 'Triggering...' : 'Simulate Distress (Test Alert)'}
                    </button>
                </div>
            </div>

            {/* Alert History */}
            <div className="glass-card history-card">
                <div className="history-header">
                    <History />
                    <h3>Recent Alerts</h3>
                </div>
                
                {alerts.length === 0 ? (
                    <div className="no-alerts">
                        No alerts triggered yet.
                    </div>
                ) : (
                    <div className="alert-list">
                        {alerts.map((alert) => (
                            <div key={alert.id} className="alert-item">
                                <div className="alert-time">
                                    {new Date(alert.timestamp).toLocaleString()}
                                </div>
                                <div className="alert-details">
                                    <span className="badge badge-danger">High Confidence ({Math.round(alert.confidenceScore * 100)}%)</span>
                                    <span>Location: {alert.latitude.toFixed(2)}, {alert.longitude.toFixed(2)}</span>
                                </div>
                                <div className="alert-status">
                                    {alert.status}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;
