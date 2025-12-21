import React from 'react';

export default function Sidebar({ currentView, setCurrentView, user, onLogout }) {
    const displayName = user?.search_name || user?.given_name || user?.name || "Alex";
    const profilePic = user?.picture || "https://lh3.googleusercontent.com/aida-public/AB6AXuDsaIY-rrWv3iY4SOq8FXdMQDPvBWlWzH7D1rk_2pQaftvsT-nDtFIPc71Y4olgtmoojaQtxna7e4akwz1kM87LrQOVqTYOgY6VcaNIehm36hlnfs5L6WNamcLTrrXZulm_WC79L2xtndUPxWUIHxiiM3A4-HYX_i9ju76jyDr6OH-s2xUOOTfMe_8weDIdZof76l_QtQlt_miuf9aj_WSOaprctkwOvi_X4nVKGqYhwBj2Pz3OAiLVQCOBuD-FfWnYX4LKkYwT_Nk";

    const navItems = [
        { id: 'dashboard', label: 'Home', icon: 'dashboard' },
        { id: 'solve', label: 'Solve', icon: 'lightbulb' },
        { id: 'projects', label: 'Projects', icon: 'folder_open' },
        { id: 'settings', label: 'Settings', icon: 'settings' },
    ];

    return (
        <aside className="hidden md:flex flex-col w-64 h-screen bg-white dark:bg-[#111318] border-r border-slate-200 dark:border-slate-800 shrink-0">
            {/* Logo Area */}
            <div className="p-6 flex items-center gap-2">
                <div className="size-8 bg-primary rounded-lg flex items-center justify-center">
                    <span className="material-symbols-outlined text-white text-[20px]">auto_awesome</span>
                </div>
                <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">SmartSolve</h1>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-4 py-4 space-y-1 overflow-hidden">
                {navItems.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => setCurrentView(item.id)}
                        className={`flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-colors font-medium text-sm
                            ${currentView === item.id
                                ? 'bg-primary/10 text-primary'
                                : 'text-slate-500 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5 hover:text-slate-900 dark:hover:text-white'
                            }`}
                    >
                        <span className="material-symbols-outlined text-[24px]" style={currentView === item.id ? { fontVariationSettings: "'FILL' 1" } : {}}>
                            {item.icon}
                        </span>
                        {item.label}
                    </button>
                ))}
            </nav>

            {/* User Profile */}
            <div className="p-4 border-t border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-slate-50 dark:hover:bg-white/5 transition-colors cursor-pointer group">
                    <div
                        className="bg-center bg-no-repeat bg-cover rounded-full size-10 ring-2 ring-slate-100 dark:ring-slate-700"
                        style={{ backgroundImage: `url("${profilePic}")` }}
                    ></div>
                    <div className="flex-1 overflow-hidden">
                        <p className="text-sm font-bold text-slate-900 dark:text-white truncate">{displayName}</p>
                        <button onClick={onLogout} className="text-xs text-slate-500 dark:text-slate-400 hover:text-red-500 transition-colors">Log Out</button>
                    </div>
                </div>
            </div>
        </aside>
    );
}