import React from 'react';

export default function Settings({ user, navigate, onLogout }) {
    const displayName = user?.search_name || user?.given_name || user?.name || "Alex Johnson";
    const email = user?.email || "alex.j@smartsolve.ai";
    const profilePic = user?.picture || "https://lh3.googleusercontent.com/aida-public/AB6AXuBxcJdfCLUZkiUklYVyD1PtN_ZED6J1frjPIiTnQCIcmCcKJX8GVeOfKuqNyFziv2XxAiRDDGJ6erKHH0QQ56wQ_xvnajOvf91a7f87ypGSW2AL_f-1BWTNWI3u0HZe61WJywxjdrVQp8jOMVKYFRty9Tcki5pLjiW5Eb-7itcAfsCo8VzMusUT5SsKGidyKOrs26az8Hy7i7NFio0dH0za4DZS-rmAh4_nWGgom-dqEbtKu0XJHORvNChxhpbPPMRYL3DoCK2u7yw";

    return (
        <div className="bg-background-light dark:bg-background-dark font-display text-slate-900 dark:text-white antialiased selection:bg-primary/30 h-full overflow-y-auto">
            <div className="w-full max-w-5xl mx-auto p-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">Settings</h2>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    {/* Left Column: Profile Card - Span 4 */}
                    <div className="lg:col-span-4">
                        <div className="bg-white dark:bg-[#1c2932] rounded-2xl p-6 shadow-sm border border-slate-200 dark:border-white/5 flex flex-col items-center">
                            <div className="relative mb-6 group cursor-pointer">
                                <div
                                    className="bg-center bg-no-repeat aspect-square bg-cover rounded-full h-32 w-32 ring-4 ring-offset-4 ring-slate-100 dark:ring-surface-dark dark:ring-offset-[#1c2932]"
                                    data-alt={`Portrait of ${displayName}`}
                                    style={{ backgroundImage: `url("${profilePic}")` }}
                                >
                                </div>
                                <div className="absolute bottom-1 right-1 bg-primary text-white rounded-full p-2 border-4 border-white dark:border-[#1c2932] flex items-center justify-center hover:scale-110 transition-transform">
                                    <span className="material-symbols-outlined text-[18px]">edit</span>
                                </div>
                            </div>
                            <div className="text-center mb-6">
                                <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">{displayName}</h1>
                                <p className="text-slate-500 dark:text-slate-400 font-medium">{email}</p>
                                <div className="mt-4 inline-flex items-center px-3 py-1 bg-primary/10 text-primary rounded-full border border-primary/20">
                                    <span className="text-xs font-bold uppercase tracking-wider">Pro Member</span>
                                </div>
                            </div>
                            <button className="w-full flex items-center justify-center gap-2 rounded-xl h-12 px-4 bg-slate-100 dark:bg-black/20 hover:bg-slate-200 dark:hover:bg-black/40 transition-colors text-sm font-semibold">
                                <span className="material-symbols-outlined text-[20px]">manage_accounts</span>
                                <span>Manage Google Account</span>
                            </button>
                        </div>
                    </div>

                    {/* Right Column: Settings Options - Span 8 */}
                    <div className="lg:col-span-8 space-y-8">

                        {/* Section 1: AI Configuration */}
                        <div>
                            <h3 className="text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-wider mb-3 ml-1">AI Agent Configuration</h3>
                            <div className="bg-white dark:bg-[#1c2932] rounded-2xl overflow-hidden shadow-sm border border-slate-200 dark:border-white/5 divide-y divide-slate-100 dark:divide-white/5">
                                {/* Item: Solving Mode */}
                                <button className="flex items-center gap-4 p-5 w-full text-left hover:bg-slate-50 dark:hover:bg-white/5 transition-colors group">
                                    <div className="flex items-center justify-center rounded-xl bg-primary/10 text-primary shrink-0 size-12 group-hover:scale-110 transition-transform">
                                        <span className="material-symbols-outlined text-[24px]">psychology</span>
                                    </div>
                                    <div className="flex flex-col flex-1">
                                        <p className="text-base font-semibold text-slate-900 dark:text-white">Solving Mode</p>
                                        <p className="text-sm text-slate-500 dark:text-slate-400">Set the default reasoning model</p>
                                    </div>
                                    <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                                        <span className="text-sm font-medium">Analytical</span>
                                        <span className="material-symbols-outlined text-[20px]">chevron_right</span>
                                    </div>
                                </button>
                                {/* Item: Response Length */}
                                <button className="flex items-center gap-4 p-5 w-full text-left hover:bg-slate-50 dark:hover:bg-white/5 transition-colors group">
                                    <div className="flex items-center justify-center rounded-xl bg-primary/10 text-primary shrink-0 size-12 group-hover:scale-110 transition-transform">
                                        <span className="material-symbols-outlined text-[24px]">short_text</span>
                                    </div>
                                    <div className="flex flex-col flex-1">
                                        <p className="text-base font-semibold text-slate-900 dark:text-white">Response Length</p>
                                        <p className="text-sm text-slate-500 dark:text-slate-400">Preferred detail level</p>
                                    </div>
                                    <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                                        <span className="text-sm font-medium">Concise</span>
                                        <span className="material-symbols-outlined text-[20px]">chevron_right</span>
                                    </div>
                                </button>
                                {/* Item: Auto-suggest */}
                                <div className="flex items-center gap-4 p-5 w-full justify-between hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className="flex items-center justify-center rounded-xl bg-primary/10 text-primary shrink-0 size-12">
                                            <span className="material-symbols-outlined text-[24px]">auto_awesome</span>
                                        </div>
                                        <div className="flex flex-col">
                                            <p className="text-base font-semibold text-slate-900 dark:text-white">Auto-suggest</p>
                                            <p className="text-sm text-slate-500 dark:text-slate-400">Proactively offer solutions</p>
                                        </div>
                                    </div>
                                    <label className="relative inline-flex items-center cursor-pointer">
                                        <input type="checkbox" defaultChecked className="sr-only peer" />
                                        <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 dark:peer-focus:ring-primary/30 rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"></div>
                                    </label>
                                </div>
                            </div>
                        </div>

                        {/* Section 2: App Preferences */}
                        <div>
                            <h3 className="text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-wider mb-3 ml-1">App Preferences</h3>
                            <div className="bg-white dark:bg-[#1c2932] rounded-2xl overflow-hidden shadow-sm border border-slate-200 dark:border-white/5 divide-y divide-slate-100 dark:divide-white/5">
                                {/* Item: Notifications */}
                                <button className="flex items-center gap-4 p-5 w-full text-left hover:bg-slate-50 dark:hover:bg-white/5 transition-colors group">
                                    <div className="flex items-center justify-center rounded-xl bg-orange-500/10 text-orange-500 shrink-0 size-12 group-hover:scale-110 transition-transform">
                                        <span className="material-symbols-outlined text-[24px]">notifications</span>
                                    </div>
                                    <div className="flex flex-col flex-1">
                                        <p className="text-base font-semibold text-slate-900 dark:text-white">Notifications</p>
                                    </div>
                                    <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                                        <span className="material-symbols-outlined text-[20px]">chevron_right</span>
                                    </div>
                                </button>
                                {/* Item: Integrations */}
                                <button className="flex items-center gap-4 p-5 w-full text-left hover:bg-slate-50 dark:hover:bg-white/5 transition-colors group">
                                    <div className="flex items-center justify-center rounded-xl bg-purple-500/10 text-purple-500 shrink-0 size-12 group-hover:scale-110 transition-transform">
                                        <span className="material-symbols-outlined text-[24px]">extension</span>
                                    </div>
                                    <div className="flex flex-col flex-1">
                                        <p className="text-base font-semibold text-slate-900 dark:text-white">Integrations</p>
                                    </div>
                                    <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                                        <span className="text-sm font-medium">3 Connected</span>
                                        <span className="material-symbols-outlined text-[20px]">chevron_right</span>
                                    </div>
                                </button>
                                {/* Item: Theme */}
                                <button className="flex items-center gap-4 p-5 w-full text-left hover:bg-slate-50 dark:hover:bg-white/5 transition-colors group">
                                    <div className="flex items-center justify-center rounded-xl bg-slate-500/10 text-slate-500 dark:text-slate-400 shrink-0 size-12 group-hover:scale-110 transition-transform">
                                        <span className="material-symbols-outlined text-[24px]">contrast</span>
                                    </div>
                                    <div className="flex flex-col flex-1">
                                        <p className="text-base font-semibold text-slate-900 dark:text-white">Theme</p>
                                    </div>
                                    <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
                                        <span className="text-sm font-medium">Dark Mode</span>
                                        <span className="material-symbols-outlined text-[20px]">chevron_right</span>
                                    </div>
                                </button>
                            </div>
                        </div>

                        {/* Logout Button */}
                        <div className="pt-4">
                            <button
                                onClick={onLogout}
                                className="w-full bg-red-50 dark:bg-red-900/10 rounded-xl p-4 text-red-600 dark:text-red-400 font-bold text-base border border-red-100 dark:border-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/20 transition-colors flex items-center justify-center gap-2"
                            >
                                <span className="material-symbols-outlined">logout</span>
                                Log Out
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}