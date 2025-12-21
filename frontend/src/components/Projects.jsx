import React from 'react';

const Projects = ({ navigate, accessToken }) => {
    return (
        <div className="p-8 max-w-7xl mx-auto bg-background-light dark:bg-background-dark h-full overflow-y-auto text-slate-900 dark:text-white">
            <header className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Active Projects</h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Manage and track your ongoing initiatives</p>
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl hover:bg-primary/90 transition-colors font-semibold shadow-lg shadow-primary/20">
                    <span className="material-symbols-outlined">add</span>
                    New Project
                </button>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Mock Project 1 */}
                <div className="bg-white dark:bg-[#1e2532] p-6 rounded-2xl border border-slate-200 dark:border-[#2e3646] shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-center justify-between mb-4">
                        <div className="size-10 bg-indigo-500/10 rounded-xl flex items-center justify-center text-indigo-500">
                            <span className="material-symbols-outlined">web</span>
                        </div>
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">60% Complete</span>
                    </div>
                    <h3 className="text-lg font-bold mb-2">Website Redesign</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">UI/UX Polish phase and responsive testing</p>
                    <div className="w-full bg-slate-100 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                        <div className="bg-indigo-500 h-full w-[60%] rounded-full"></div>
                    </div>
                </div>

                {/* Mock Project 2 */}
                <div className="bg-white dark:bg-[#1e2532] p-6 rounded-2xl border border-slate-200 dark:border-[#2e3646] shadow-sm hover:shadow-md transition-all">
                    <div className="flex items-center justify-between mb-4">
                        <div className="size-10 bg-pink-500/10 rounded-xl flex items-center justify-center text-pink-500">
                            <span className="material-symbols-outlined">group_add</span>
                        </div>
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">30% Complete</span>
                    </div>
                    <h3 className="text-lg font-bold mb-2">Hiring Sprint</h3>
                    <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">Interviewing Seniors and technical screening</p>
                    <div className="w-full bg-slate-100 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                        <div className="bg-pink-500 h-full w-[30%] rounded-full"></div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Projects;