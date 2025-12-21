import React from 'react';

export default function Loading() {
    return (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-background-light dark:bg-background-dark">
            <div className="relative flex items-center justify-center">
                {/* Outer Ring */}
                <div className="absolute size-24 rounded-full border-4 border-primary/20 animate-[spin_3s_linear_infinite]"></div>
                {/* Middle Ring */}
                <div className="absolute size-16 rounded-full border-4 border-t-primary border-r-transparent border-b-primary/50 border-l-transparent animate-[spin_1.5s_linear_infinite]"></div>
                {/* Inner Icon */}
                <div className="relative z-10 bg-primary/10 p-4 rounded-full animate-pulse">
                    <span className="material-symbols-outlined text-primary text-[32px]">auto_awesome</span>
                </div>
            </div>
            <div className="mt-8 flex flex-col items-center gap-2">
                <h2 className="text-slate-900 dark:text-white text-xl font-bold tracking-tight">SmartSolve</h2>
                <p className="text-slate-500 dark:text-slate-400 text-sm font-medium animate-pulse">Authenticating...</p>
            </div>
        </div>
    );
}