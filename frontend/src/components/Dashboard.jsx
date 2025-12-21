import React, { useState, useEffect, useRef } from 'react';

export default function Dashboard({ user, navigate, accessToken, userEmail }) {
    const displayName = user?.search_name || user?.given_name || user?.name || "Alex";
    const profilePic = user?.picture || "https://lh3.googleusercontent.com/aida-public/AB6AXuDsaIY-rrWv3iY4SOq8FXdMQDPvBWlWzH7D1rk_2pQaftvsT-nDtFIPc71Y4olgtmoojaQtxna7e4akwz1kM87LrQOVqTYOgY6VcaNIehm36hlnfs5L6WNamcLTrrXZulm_WC79L2xtndUPxWUIHxiiM3A4-HYX_i9ju76jyDr6OH-s2xUOOTfMe_8weDIdZof76l_QtQlt_miuf9aj_WSOaprctkwOvi_X4nVKGqYhwBj2Pz3OAiLVQCOBuD-FfWnYX4LKkYwT_Nk";

    const [tasks, setTasks] = useState([]);
    const [completedTasks, setCompletedTasks] = useState([]);
    const [events, setEvents] = useState([]);
    const [loadingData, setLoadingData] = useState(false);
    const [loadingEvents, setLoadingEvents] = useState(false);
    const [loadingTasks, setLoadingTasks] = useState(false);
    const [completingTasks, setCompletingTasks] = useState(new Set());
    const [taskError, setTaskError] = useState(null);
    const [insight, setInsight] = useState(null);
    const [loadingInsight, setLoadingInsight] = useState(false);
    const [insightError, setInsightError] = useState(null);
    const [homeQuery, setHomeQuery] = useState('');
    const [priorityTasks, setPriorityTasks] = useState([]);
    const [loadingPriorityTasks, setLoadingPriorityTasks] = useState(false);
    const [priorityTasksCollapsed, setPriorityTasksCollapsed] = useState(false);
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';


    const fetchInProgress = useRef(false);

    const formatMessage = (content) => {
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
            .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
            .replace(/\n/g, '<br>') // Line breaks
            .replace(/• /g, '• ') // Bullet points
            .replace(/\d+\. /g, (match) => `<br>${match}`) // Numbered lists
            .replace(/<br><br>/g, '<br>'); // Remove double breaks
    };

    const completeTask = async (taskId) => {
        if (!accessToken || completingTasks.has(taskId)) return;

        setCompletingTasks(prev => new Set(prev).add(taskId));
        setTaskError(null);
        try {
            const res = await fetch(`https://tasks.googleapis.com/tasks/v1/lists/@default/tasks/${taskId}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: 'completed' })
            });

            if (res.ok) {
                // Optimistic UI update: remove from tasks and add to completed
                const taskToComplete = tasks.find(t => t.id === taskId);
                setTasks(prev => prev.filter(t => t.id !== taskId));
                if (taskToComplete) {
                    setCompletedTasks(prev => [taskToComplete, ...prev]);
                }
                // Sync with server after a short delay to ensure Google's database is updated
                setTimeout(() => fetchTasks(true), 1500);
            } else {
                const errData = await res.json();
                console.error("Failed to complete task:", errData);
                setTaskError("Failed to update task. Please re-login to grant permissions.");
            }
        } catch (error) {
            console.error("Error completing task:", error);
            setTaskError("Network error. Please try again.");
        } finally {
            setCompletingTasks(prev => {
                const next = new Set(prev);
                next.delete(taskId);
                return next;
            });
        }
    };

    const fetchEvents = async (silent = false) => {
        if (!accessToken) return [];
        if (!silent) setLoadingEvents(true);
        try {
            const now = new Date().toISOString();
            const calendarRes = await fetch(`https://www.googleapis.com/calendar/v3/calendars/primary/events?orderBy=startTime&singleEvents=true&timeMin=${now}&maxResults=5`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            const calendarData = await calendarRes.json();
            const fetchedEvents = calendarData.items || [];
            setEvents(fetchedEvents);
            return fetchedEvents;
        } catch (error) {
            console.error("Error fetching events:", error);
            return [];
        } finally {
            if (!silent) setLoadingEvents(false);
        }
    };

    const fetchTasks = async (silent = false) => {
        if (!accessToken) return [];
        if (!silent) setLoadingTasks(true);
        try {
            // Pending Tasks
            const tasksRes = await fetch(`https://tasks.googleapis.com/tasks/v1/lists/@default/tasks?showCompleted=false&maxResults=50`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            const tasksData = await tasksRes.json();
            const fetchedTasks = tasksData.items || [];
            setTasks(fetchedTasks);

            // Completed Tasks
            const compTasksRes = await fetch(`https://tasks.googleapis.com/tasks/v1/lists/@default/tasks?showCompleted=true&showHidden=true&maxResults=100`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            const compTasksData = await compTasksRes.json();
            const fetchedCompTasks = compTasksData.items || [];
            setCompletedTasks(fetchedCompTasks);

            return fetchedTasks;
        } catch (error) {
            console.error("Error fetching tasks:", error);
            return [];
        } finally {
            if (!silent) setLoadingTasks(false);
        }
    };

    useEffect(() => {
        if (!accessToken || fetchInProgress.current) return;

        const initLoad = async () => {
            fetchInProgress.current = true;
            setLoadingData(true);
            try {
                const [evts, tsks] = await Promise.all([
                    fetchEvents(true),
                    fetchTasks(true)
                ]);

                // Fetch priority tasks
                fetchPriorityTasks();

                if (evts.length > 0 || tsks.length > 0) {
                    await fetchInsight(tsks, evts);
                }
            } catch (error) {
                console.error("Initialization error:", error);
            } finally {
                setLoadingData(false);
                fetchInProgress.current = false;
            }
        };

        initLoad();
    }, [accessToken]);

    const fetchInsight = async (currentTasks = tasks, currentEvents = events) => {
        if (currentTasks.length === 0 && currentEvents.length === 0) return;

        setLoadingInsight(true);
        setInsightError(null);
        try {
            const optimizeRes = await fetch(`${API_URL}/optimize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tasks: currentTasks.map(t => ({ title: t.title, due: t.due })),
                    events: currentEvents.map(e => ({ summary: e.summary, start: e.start, end: e.end })),
                    user_email: userEmail
                })
            });

            const data = await optimizeRes.json();

            if (optimizeRes.status === 429) {
                throw new Error(data.message || "AI Quota Limit Reached. Try again later.");
            }

            if (!data.error) {
                setInsight(data);
            } else {
                throw new Error(data.error || "Failed to generate insight");
            }
        } catch (err) {
            console.error("Error fetching insight:", err);
            setInsightError(err.message);
        } finally {
            setLoadingInsight(false);
        }
    };

    const fetchPriorityTasks = async () => {
        if (!userEmail) return;
        setLoadingPriorityTasks(true);
        try {
            const res = await fetch(`${API_URL}/priority_tasks/${userEmail}`);
            const data = await res.json();
            if (data.tasks) {
                setPriorityTasks(data.tasks);
            }
        } catch (error) {
            console.error("Error fetching priority tasks:", error);
        } finally {
            setLoadingPriorityTasks(false);
        }
    };

    const handleHomeSubmit = (e) => {
        e.preventDefault();
        if (!homeQuery.trim()) return;
        navigate('solve', homeQuery);
    };

    // Derived Stats
    const pendingTasksCount = tasks.length;
    const completedTasksCount = completedTasks.length;
    const totalTasks = pendingTasksCount + completedTasksCount;

    // Efficiency Score: Base 50% + dynamic (completed/total * 50)
    const efficiencyScore = totalTasks > 0
        ? Math.min(100, 50 + Math.round((completedTasksCount / totalTasks) * 50))
        : 50;

    const nextDeadline = events.length > 0 ? events[0] : null;

    // Helper to format date and time
    const formatDate = (event) => {
        const start = event.start.dateTime || event.start.date;
        if (!start) return { month: 'NA', day: '--', time: '', daysLeft: 0 };

        const date = new Date(start);
        const now = new Date();

        // Normalize to midnight for days calculation
        const dateMidnight = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        const nowMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const daysDiff = Math.ceil((dateMidnight - nowMidnight) / (1000 * 60 * 60 * 24));

        // Format time
        let timeStr = 'All Day';
        if (event.start.dateTime) {
            timeStr = date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
            if (event.end?.dateTime) {
                const end = new Date(event.end.dateTime);
                timeStr += ' - ' + end.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
            }
        }

        return {
            month: date.toLocaleString('default', { month: 'short' }),
            day: date.getDate(),
            time: timeStr,
            daysLeft: daysDiff
        };
    };

    return (
        <div className="h-full overflow-y-auto bg-background-light dark:bg-background-dark text-slate-900 dark:text-white font-display">
            <div className="p-6 md:p-10">

                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-center justify-between mb-8">
                    <div>
                        <h2 className="text-slate-900 dark:text-white text-[32px] font-bold leading-tight">Good morning, {displayName}</h2>
                        <p className="text-slate-500 dark:text-[#9da6b9] text-base mt-2">Here's your daily SmartSolve briefing and performance overview.</p>
                    </div>
                    <div className="hidden md:flex items-center gap-4 mt-4 md:mt-0">
                        <button className="flex items-center justify-center size-10 rounded-full bg-white dark:bg-[#1e2532] border border-slate-200 dark:border-[#2e3646] text-slate-500 hover:text-primary transition-colors relative">
                            <span className="material-symbols-outlined">notifications</span>
                            <span className="absolute top-2 right-2.5 size-2 bg-red-500 rounded-full ring-2 ring-white dark:ring-[#1e2532]"></span>
                        </button>
                    </div>
                </div>

                {/* High Priority Tasks Table */}
                <div className="mb-8">
                    <div className="bg-white dark:bg-[#1e2532] rounded-2xl border border-slate-200 dark:border-[#2e3646] shadow-sm overflow-hidden">
                        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-[#2e3646]">
                            <h3 className="text-slate-900 dark:text-white text-lg font-bold">High Priority Tasks</h3>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={fetchPriorityTasks}
                                    disabled={loadingPriorityTasks}
                                    className="p-2 text-slate-400 hover:text-primary transition-colors disabled:opacity-50"
                                    title="Refresh"
                                >
                                    <span className={`material-symbols-outlined text-[18px] ${loadingPriorityTasks ? 'animate-spin' : ''}`}>refresh</span>
                                </button>
                                <button
                                    onClick={() => setPriorityTasksCollapsed(!priorityTasksCollapsed)}
                                    className="p-2 text-slate-400 hover:text-primary transition-colors"
                                >
                                    <span className={`material-symbols-outlined text-[18px] transition-transform ${priorityTasksCollapsed ? 'rotate-180' : ''}`}>expand_more</span>
                                </button>
                            </div>
                        </div>

                        {!priorityTasksCollapsed && (
                            <div className="overflow-x-auto">
                                {loadingPriorityTasks ? (
                                    <div className="p-4 text-center text-slate-500">Loading priority tasks...</div>
                                ) : priorityTasks.length === 0 ? (
                                    <div className="p-4 text-center text-slate-500">No priority tasks found.</div>
                                ) : (
                                    <table className="w-full">
                                        <thead className="bg-slate-50 dark:bg-[#151b21]">
                                            <tr>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Priority</th>
                                                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Task</th>
                                                <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Action</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-200 dark:divide-[#2e3646]">
                                            {priorityTasks.map((task, index) => (
                                                <tr key={index} className="hover:bg-slate-50 dark:hover:bg-[#151b21] transition-colors">
                                                    <td className="px-4 py-3">
                                                        <div className="flex items-center gap-2">
                                                            <div className={`size-2 rounded-full ${task.priority === 'high' ? 'bg-red-500' :
                                                                task.priority === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                                                                }`}></div>
                                                            <span className="text-sm font-medium text-slate-900 dark:text-white capitalize">{task.priority}</span>
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        <div>
                                                            <p className="text-sm font-medium text-slate-900 dark:text-white">{task.title}</p>
                                                            {task.notes && (
                                                                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">{task.notes}</p>
                                                            )}
                                                        </div>
                                                    </td>
                                                    <td className="px-4 py-3 text-center">
                                                        <button
                                                            onClick={() => navigate('solve', `Help me with this priority task: ${task.title}`)}
                                                            className="p-2 text-slate-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors"
                                                            title="Solve with SmartSolve"
                                                        >
                                                            <span className="material-symbols-outlined text-[18px]">smart_toy</span>
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    {/* Pending Tasks */}
                    <div className="flex flex-col gap-2 rounded-2xl p-6 bg-white dark:bg-[#1e2532] border border-slate-200 dark:border-[#2e3646] shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between">
                            <span className="material-symbols-outlined text-primary text-[28px]">pending_actions</span>
                            {/* <p className="text-[#fa6238] text-xs font-bold leading-normal bg-[#fa6238]/10 px-2.5 py-1 rounded-full">-2% vs last week</p> */}
                        </div>
                        <div className="mt-4">
                            <p className="text-slate-900 dark:text-white tracking-tight text-4xl font-bold leading-tight">
                                {loadingData ? '...' : pendingTasksCount}
                            </p>
                            <p className="text-slate-500 dark:text-[#9da6b9] text-sm font-medium mt-1">Pending Google Tasks</p>
                        </div>
                    </div>

                    {/* Completed */}
                    <div className="flex flex-col gap-2 rounded-2xl p-6 bg-white dark:bg-[#1e2532] border border-slate-200 dark:border-[#2e3646] shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between">
                            <span className="material-symbols-outlined text-[#0bda5e] text-[28px]">check_circle</span>
                            <p className="text-[#0bda5e] text-xs font-bold leading-normal bg-[#0bda5e]/10 px-2.5 py-1 rounded-full">+15% vs last week</p>
                        </div>
                        <div className="mt-4">
                            <p className="text-slate-900 dark:text-white tracking-tight text-4xl font-bold leading-tight">{completedTasksCount}</p>
                            <p className="text-slate-500 dark:text-[#9da6b9] text-sm font-medium mt-1">Completed Tasks</p>
                        </div>
                    </div>

                    {/* Efficiency */}
                    <div className="flex flex-col gap-2 rounded-2xl p-6 bg-white dark:bg-[#1e2532] border border-slate-200 dark:border-[#2e3646] shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between">
                            <span className="material-symbols-outlined text-primary text-[28px]">bolt</span>
                            <p className="text-[#0bda5e] text-xs font-bold leading-normal bg-[#0bda5e]/10 px-2.5 py-1 rounded-full">+5% vs last week</p>
                        </div>
                        <div className="mt-4">
                            <p className="text-slate-900 dark:text-white tracking-tight text-4xl font-bold leading-tight">
                                {efficiencyScore}%
                            </p>
                            <p className="text-slate-500 dark:text-[#9da6b9] text-sm font-medium mt-1">Efficiency Score</p>
                        </div>
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                    {/* Left Column (2/3) */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* AI Composer */}
                        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-transparent p-1">
                            <div className="bg-white dark:bg-[#1e2532] rounded-xl p-6">
                                <div className="flex items-center gap-2 mb-4">
                                    <span className="material-symbols-outlined text-primary">auto_awesome</span>
                                    <h3 className="text-base font-semibold text-slate-900 dark:text-white">Ask SmartSolve to analyze or plan</h3>
                                </div>
                                <form
                                    onSubmit={handleHomeSubmit}
                                    className="flex w-full items-center rounded-xl bg-slate-100 dark:bg-[#282e39] border border-transparent transition-all"
                                >
                                    <input
                                        value={homeQuery}
                                        onChange={(e) => setHomeQuery(e.target.value)}
                                        className="w-full bg-transparent border-none text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-[#9da6b9] px-4 py-4 text-base focus:ring-0 focus:outline-none"
                                        placeholder="Analyze my schedule for next week..."
                                    />
                                    <button type="button" className="p-3 mr-1 text-slate-400 dark:text-[#9da6b9] hover:text-primary transition-colors">
                                        <span className="material-symbols-outlined text-[24px]">mic</span>
                                    </button>
                                    <button type="submit" className="bg-primary text-white rounded-lg p-2.5 mr-2 hover:bg-blue-700 transition-colors shadow-lg shadow-primary/30">
                                        <span className="material-symbols-outlined text-[24px]">arrow_upward</span>
                                    </button>
                                </form>
                            </div>
                        </div>

                        {/* Upcoming Deadlines (Google Calendar Events) */}
                        <div>
                            <div className="flex items-center justify-between pb-4">
                                <h3 className="text-slate-900 dark:text-white text-xl font-bold leading-tight tracking-[-0.015em]">Upcoming Events</h3>
                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={() => fetchEvents()}
                                        disabled={loadingEvents}
                                        className="p-2 text-slate-400 hover:text-primary transition-colors disabled:opacity-50"
                                        title="Refresh Events"
                                    >
                                        <span className={`material-symbols-outlined text-[20px] ${loadingEvents ? 'animate-spin' : ''}`}>refresh</span>
                                    </button>
                                    <button className="text-primary text-sm font-medium hover:underline">View Calendar</button>
                                </div>
                            </div>
                            <div className="flex flex-col gap-4">
                                {loadingData && <p className="text-sm text-slate-500">Loading your calendar...</p>}
                                {!loadingData && events.length === 0 && <p className="text-sm text-slate-500">No upcoming events found.</p>}

                                {events.map((event) => {
                                    const dateInfo = formatDate(event);
                                    return (
                                        <div key={event.id} className="flex items-center gap-6 p-4 rounded-2xl bg-white dark:bg-[#1e2532] border border-slate-200 dark:border-[#2e3646] shadow-sm hover:border-primary/50 transition-colors cursor-pointer group">
                                            <div className="shrink-0 flex flex-col items-center justify-center size-14 rounded-xl bg-primary/10 text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                                                <span className="text-xs font-bold uppercase">{dateInfo.month}</span>
                                                <span className="text-xl font-bold">{dateInfo.day}</span>
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <h4 className="text-slate-900 dark:text-white text-lg font-semibold truncate">{event.summary}</h4>
                                                <p className="text-slate-500 dark:text-[#9da6b9] text-sm mt-1 truncate">
                                                    {dateInfo.time}
                                                </p>
                                            </div>
                                            <div className="shrink-0 flex items-center gap-4">
                                                <div className="text-right hidden sm:block">
                                                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                                                        {dateInfo.daysLeft === 0 ? 'Today' : dateInfo.daysLeft === 1 ? 'Tomorrow' : `${dateInfo.daysLeft} days left`}
                                                    </p>
                                                </div>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        navigate('solve', `Help me plan for this event: ${event.summary} on ${dateInfo.month} ${dateInfo.day} at ${dateInfo.time}`);
                                                    }}
                                                    className="shrink-0 p-2 text-slate-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                                    title="Analyze with SmartSolve"
                                                >
                                                    <span className="material-symbols-outlined">smart_toy</span>
                                                </button>
                                                <span className={`inline-flex size-3 rounded-full ${dateInfo.daysLeft <= 1 ? 'bg-[#fa6238]' : 'bg-primary'}`}></span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Pending Tasks List */}
                        <div className="mt-8">
                            <div className="flex items-center justify-between pb-4">
                                <h3 className="text-slate-900 dark:text-white text-xl font-bold leading-tight tracking-[-0.015em]">Pending Tasks</h3>
                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={() => fetchTasks()}
                                        disabled={loadingTasks}
                                        className="p-2 text-slate-400 hover:text-primary transition-colors disabled:opacity-50"
                                        title="Refresh Tasks"
                                    >
                                        <span className={`material-symbols-outlined text-[20px] ${loadingTasks ? 'animate-spin' : ''}`}>refresh</span>
                                    </button>
                                    <button className="text-primary text-sm font-medium hover:underline">View All</button>
                                </div>
                            </div>
                            <div className="flex flex-col gap-3">
                                {taskError && (
                                    <div className="p-3 mb-2 text-xs bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg flex items-center gap-2">
                                        <span className="material-symbols-outlined text-[16px]">error</span>
                                        {taskError}
                                    </div>
                                )}
                                {loadingData && <p className="text-sm text-slate-500">Loading your tasks...</p>}
                                {!loadingData && tasks.length === 0 && <p className="text-sm text-slate-500">No pending tasks found.</p>}

                                {tasks.map((task) => (
                                    <div
                                        key={task.id}
                                        onClick={() => completeTask(task.id)}
                                        className={`flex items-center gap-4 p-4 rounded-xl bg-white dark:bg-[#1e2532] border border-slate-200 dark:border-[#2e3646] shadow-sm hover:border-primary transition-all group cursor-pointer ${completingTasks.has(task.id) ? 'opacity-50 pointer-events-none' : ''}`}
                                    >
                                        <div className="shrink-0 flex items-center justify-center size-7 rounded-full border-2 border-slate-300 dark:border-slate-600 group-hover:border-primary group-hover:bg-primary/5 transition-all relative">
                                            {completingTasks.has(task.id) ? (
                                                <span className="material-symbols-outlined text-[16px] animate-spin text-primary">progress_activity</span>
                                            ) : (
                                                <span className="material-symbols-outlined text-[18px] text-primary opacity-0 group-hover:opacity-100 transition-opacity">check</span>
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className="text-slate-900 dark:text-white text-base font-semibold group-hover:text-primary transition-colors truncate">{task.title}</h4>
                                            {task.due && (
                                                <p className="text-slate-500 dark:text-[#9da6b9] text-xs mt-0.5 flex items-center gap-1">
                                                    <span className="material-symbols-outlined text-[14px]">event</span>
                                                    Due: {new Date(task.due).toLocaleDateString()}
                                                </p>
                                            )}
                                        </div>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                navigate('solve', `I need help with this task: ${task.title}`);
                                            }}
                                            className="shrink-0 p-2 text-slate-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                            title="Solve with SmartSolve"
                                        >
                                            <span className="material-symbols-outlined">smart_toy</span>
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Right Column (1/3) - Insights */}
                    <div className="lg:col-span-1">
                        <h3 className="text-slate-900 dark:text-white text-xl font-bold leading-tight tracking-[-0.015em] mb-4">Recent Insights</h3>
                        <div className="bg-white dark:bg-[#1e2532] border border-slate-200 dark:border-[#2e3646] rounded-2xl p-6 shadow-sm relative overflow-hidden group h-full">
                            <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
                                <span className="material-symbols-outlined text-[140px] text-primary rotate-12">psychology</span>
                            </div>
                            <div className="relative z-10 flex flex-col h-full">
                                {/* Insight Content */}
                                {!insight && !loadingInsight && !insightError && (
                                    <div className="flex flex-col items-center justify-center flex-1 text-center opacity-60">
                                        <span className="material-symbols-outlined text-[48px] mb-2">auto_awesome</span>
                                        <p className="text-sm">Gathering insights...</p>
                                    </div>
                                )}

                                {insightError && (
                                    <div className="flex flex-col items-center justify-center flex-1 text-center">
                                        <span className="material-symbols-outlined text-[48px] mb-2 text-yellow-500">warning</span>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 px-4">{insightError}</p>
                                        <button
                                            type="button"
                                            onClick={() => fetchInsight()}
                                            className="mt-4 text-xs bg-slate-100 dark:bg-slate-700 px-3 py-2 rounded-lg hover:bg-slate-200 transition-colors"
                                        >
                                            Retry
                                        </button>
                                    </div>
                                )}

                                {loadingInsight && (
                                    <div className="flex flex-col items-center justify-center flex-1 text-center animate-pulse">
                                        <span className="material-symbols-outlined text-[48px] mb-2">lightbulb</span>
                                        <p className="text-sm">Analyzing your schedule...</p>
                                    </div>
                                )}

                                {insight && (
                                    <>
                                        <div className="flex items-center gap-2 mb-4">
                                            <div className="bg-primary/20 rounded-lg p-1.5">
                                                <span className="material-symbols-outlined text-primary text-[20px]">lightbulb</span>
                                            </div>
                                            <span className="text-xs font-bold text-primary uppercase tracking-wider">{insight.type || "Optimization Suggestion"}</span>
                                        </div>
                                        <p className="text-slate-800 dark:text-slate-200 text-base leading-relaxed mb-6 flex-1" dangerouslySetInnerHTML={{ __html: formatMessage(insight.message) }}>
                                        </p>
                                        <div className="flex flex-col gap-3">
                                            <button
                                                type="button"
                                                onClick={() => fetchInsight()}
                                                disabled={loadingInsight}
                                                className="w-full flex items-center justify-center gap-2 text-sm bg-primary hover:bg-primary/90 text-white px-4 py-3 rounded-xl transition-all font-bold shadow-lg shadow-primary/20 disabled:opacity-50 disabled:cursor-not-allowed group"
                                            >
                                                <span className={`material-symbols-outlined text-[20px] ${loadingInsight ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`}>refresh</span>
                                                {loadingInsight ? 'Refreshing...' : 'Get New Insight'}
                                            </button>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}