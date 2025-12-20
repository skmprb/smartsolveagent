import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [userInfo, setUserInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('user_id');
    
    if (userId && !userInfo) {
      fetch(`http://localhost:5000/token/${userId}`)
        .then(response => response.json())
        .then(data => {
          if (data.access_token) {
            return fetch(`https://www.googleapis.com/oauth2/v2/userinfo?access_token=${data.access_token}`);
          }
        })
        .then(response => response.json())
        .then(userData => {
          setUserInfo(userData);
          setLoading(false);
        })
        .catch(error => {
          console.error('Error:', error);
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, [userInfo]);

  const handleLogin = () => {
    window.location.href = 'http://localhost:5000/auth';
  };

  const handleLogout = () => {
    setUserInfo(null);
    window.history.replaceState({}, document.title, "/");
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>🔑 Google OAuth Login Demo</h1>
        
        {userInfo ? (
          <div className="user-info">
            <div className="success-message">✅ Successfully logged in!</div>
            
            <div className="user-details">
              <div className="user-avatar">
                {userInfo.picture && (
                  <img src={userInfo.picture} alt="Profile" width="100" />
                )}
              </div>
              
              <div className="user-data">
                <h2>User Details</h2>
                <p><strong>Name:</strong> {userInfo.name || 'N/A'}</p>
                <p><strong>Email:</strong> {userInfo.email || 'N/A'}</p>
                <p><strong>ID:</strong> {userInfo.id || 'N/A'}</p>
              </div>
            </div>
            
            <button onClick={handleLogout} className="logout-btn">
              🚪 Logout
            </button>
          </div>
        ) : (
          <div className="login-section">
            <p>Please log in with your Google account to continue.</p>
            <button onClick={handleLogin} className="login-btn">
              🔑 Sign in with Google
            </button>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;