import { useState, useEffect } from 'react'
import Onboarding from './components/Onboarding'
import Dashboard from './components/Dashboard'
import Settings from './components/Settings'
import Sidebar from './components/Sidebar'
import Loading from './components/Loading'
import Solve from './components/Solve'
import Projects from './components/Projects'

function App() {
    // view can be: 'onboarding', 'dashboard', 'settings', 'solve', 'projects'
    const [currentView, setCurrentView] = useState('onboarding')
    const [user, setUser] = useState(null)
    const [userEmail, setUserEmail] = useState(null)
    const [accessToken, setAccessToken] = useState(null)
    const [initialSolveQuery, setInitialSolveQuery] = useState(null)

    // Initialize isLoading based on whether we are redirecting from auth (user_email param present)
    const [isLoading, setIsLoading] = useState(() => {
        return new URLSearchParams(window.location.search).has('user_email');
    });

    useEffect(() => {
        // Check for user_email in URL
        const params = new URLSearchParams(window.location.search);
        const email = params.get('user_email');

        if (email) {
            console.log("Auth redirect detected for", email);
            setUserEmail(email);
            // We have a user_email, fetch the token
            fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/token/${email}`)
                .then(res => res.json())
                .then(data => {
                    if (data.access_token) {
                        console.log("Authenticated!");
                        setAccessToken(data.access_token);
                        // Optional: Fetch full user info if needed, or just set email
                        setUser({ name: email.split('@')[0], email: email });
                        setCurrentView('dashboard');
                        // Clean up URL
                        window.history.replaceState({}, document.title, window.location.pathname);
                    } else {
                        console.error("Token fetch failed:", data);
                    }
                })
                .catch(err => console.error("Auth error:", err))
                .finally(() => {
                    setIsLoading(false);
                });
        }
    }, []);

    const handleLogout = () => {
        setUser(null);
        setUserEmail(null);
        setAccessToken(null);
        setCurrentView('onboarding');
        setInitialSolveQuery(null);
    };

    const navigateWithQuery = (view, query = null) => {
        if (query) setInitialSolveQuery(query);
        setCurrentView(view);
    };

    if (isLoading) {
        return <Loading />
    }

    if (currentView === 'onboarding') {
        return <Onboarding onFinish={() => setCurrentView('dashboard')} />
    }

    return (
        <div className="flex h-screen bg-background-light dark:bg-background-dark overflow-hidden">
            <Sidebar
                currentView={currentView}
                setCurrentView={setCurrentView}
                user={user}
                onLogout={handleLogout}
            />
            <main className="flex-1 overflow-hidden">
                {currentView === 'settings' && <Settings user={user} userEmail={userEmail} navigate={navigateWithQuery} onLogout={handleLogout} />}
                {currentView === 'dashboard' && <Dashboard user={user} userEmail={userEmail} navigate={navigateWithQuery} accessToken={accessToken} />}
                {currentView === 'solve' && (
                    <Solve
                        navigate={navigateWithQuery}
                        accessToken={accessToken}
                        initialQuery={initialSolveQuery}
                        userEmail={userEmail}
                        user={user}
                        onClearQuery={() => setInitialSolveQuery(null)}
                    />
                )}
                {currentView === 'projects' && <Projects userEmail={userEmail} navigate={navigateWithQuery} accessToken={accessToken} />}
            </main>
        </div>
    );
}

export default App