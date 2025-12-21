import React from 'react';

const Onboarding = ({ onFinish }) => {
    return (
        <div className="relative flex h-full min-h-screen w-full flex-col justify-between bg-background-light dark:bg-background-dark overflow-x-hidden transition-colors duration-200">
            {/* Top Navigation */}
            <div className="flex items-center w-full p-4 pt-6 justify-end z-10">
                {/* Skip button removed */}
            </div>

            {/* Content Wrapper */}
            <div className="flex flex-col flex-grow items-center justify-center w-full">
                {/* Hero Image Section */}
                <div className="w-full max-w-md px-6 @container mb-6">
                    <div className="relative w-full aspect-[4/3] rounded-2xl overflow-hidden shadow-2xl shadow-primary/20 ring-1 ring-white/10">
                        <div className="absolute inset-0 bg-gradient-to-t from-background-light dark:from-background-dark via-transparent to-transparent opacity-20 z-10"></div>
                        <div
                            className="w-full h-full bg-center bg-no-repeat bg-cover transform hover:scale-105 transition-transform duration-700"
                            style={{ backgroundImage: 'url("https://lh3.googleusercontent.com/aida-public/AB6AXuBDs8mefiaCpr9caVEyMGPk_VWdDFNEnwMnmi1YCcQs3602o5e4j73DEmotXN7II7SdGHCu1urJVlKfYYX0IoBAz86z7vL8CiTBXLKDccub4vuM_mefv2QLffWsPmOOYvqA16aeCefkNbD0cpMJidl7lGMpF7_kYPxFSRX1n1cAn5w6RhYT0SbMQM2DS1OTLJtV7wDu8lOLSM8Lv2fhF_jK-rvmsI2yHBBEKEqqB7pBm38Wn0hRzdJ211DJGLCHLPPjYLElLQLoPwsV")' }}
                        >
                        </div>
                    </div>
                </div>

                {/* Text Content */}
                <div className="w-full max-w-md px-6 text-center space-y-3">
                    <h1 className="text-gray-900 dark:text-white text-3xl md:text-4xl font-extrabold leading-tight tracking-tight">
                        Your Personal <br />
                        <span className="text-primary">AI Strategist</span>
                    </h1>
                    <p className="text-gray-600 dark:text-[#9da6b9] text-base font-normal leading-relaxed px-2">
                        SmartSolve breaks down complex goals into actionable steps, helping you achieve more every day.
                    </p>
                </div>

                {/* Page Indicators */}
                <div className="flex w-full flex-row items-center justify-center gap-3 py-8">
                    <div className="h-2 w-8 rounded-full bg-primary transition-all duration-300"></div>
                    <div className="h-2 w-2 rounded-full bg-gray-300 dark:bg-[#3b4354] hover:bg-gray-400 dark:hover:bg-gray-600 transition-colors cursor-pointer"></div>
                    <div className="h-2 w-2 rounded-full bg-gray-300 dark:bg-[#3b4354] hover:bg-gray-400 dark:hover:bg-gray-600 transition-colors cursor-pointer"></div>
                </div>
            </div>

            {/* Bottom Action Area */}
            <div className="w-full px-6 pb-10 safe-area-bottom">
                <div className="flex flex-col gap-3 max-w-md mx-auto">
                    {/* Primary Action */}
                    <a
                        href={`${import.meta.env.VITE_API_URL || 'http://localhost:5000'}/auth`}
                        className="group relative flex w-full items-center justify-center rounded-xl bg-primary px-6 py-4 text-white shadow-lg shadow-primary/30 hover:shadow-primary/50 hover:-translate-y-0.5 transition-all duration-200"
                    >
                        <span className="absolute left-6 flex items-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                            <span className="material-symbols-outlined text-[20px]">auto_awesome</span>
                        </span>
                        <span className="text-base font-bold tracking-wide">Continue with Google</span>
                    </a>
                </div>
                <p className="mt-6 text-center text-xs text-gray-400 dark:text-gray-600">
                    AI-Powered • Secure • Efficient
                </p>
            </div>
        </div>
    );
};

export default Onboarding;