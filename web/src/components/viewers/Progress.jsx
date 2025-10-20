import { useEffect, useState } from "react";
import { Doughnut } from "react-chartjs-2";
import "chart.js/auto";
import { FaLock, FaLockOpen } from "react-icons/fa";
import { getProgress } from "../../api/progress";
import Loader from "../layout/widgets/Loader";
import Header from "../layout/Header";
import { FaCheckCircle } from "react-icons/fa";

const Progress = ({ topic, userId, PASS_THRESHOLD }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        async function fetchProgress() {
            try {
                setLoading(true);
                const res = await getProgress(topic, userId);
                setData(res);
            } catch (err) {
                console.error("Error fetching progress:", err);
                setError(err.message || "Failed to fetch progress.");
            } finally {
                setLoading(false);
            }

        }
        if (topic && userId) fetchProgress();
    }, [topic, userId]);

    if (error) return <div className="error">{error}</div>;
    if (loading) return <Loader message="Calculating progress..." />;

    const unlockedLevel = data?.unlockedLevel ?? 0;

    const byLevel = new Map((data?.perLevel || []).map((l) => [l.level, l]));
    const perLevel = [1, 2, 3].map((lvl) => {
        return byLevel.get(lvl) || {
            level: lvl,
            attempts: 0,
            passes: 0,
            lastScore: 0,
            lastAt: null,
            keywordStats: [],
        };
    });


    const fmtDate = (isoOrNull) => {
        if (!isoOrNull) return "—";
        try {
            const iso =
                typeof isoOrNull === "string" ? isoOrNull : isoOrNull.$date || null;
            if (!iso) return "—";
            const d = new Date(iso);
            return d.toLocaleString();
        } catch {
            return "—";
        }
    };

    const pieOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
    };


    const barClass = (p) => {
        if (p >= 0.75) return "keyword-bar keyword-bar--g80";
        if (p >= 0.5) return "keyword-bar keyword-bar--g60";
        if (p >= 0.25) return "keyword-bar keyword-bar--g40";
        return "keyword-bar keyword-bar--g00";
    };

    return (
        <div className="progress-panel">
            <Header title="Progress" panel="progress" topic={topic} />
            <div className="progress-grid">
                {perLevel.map((lv) => {
                    const isUnlocked = lv.level <= unlockedLevel;
                    const attempts = lv.attempts || 0;
                    const passes = lv.passes || 0;
                    const fails = Math.max(0, attempts - passes);
                    const pieData = {
                        labels: ["Passes", "Fails"],
                        datasets: [{
                            data: [passes, fails],
                            backgroundColor: ['#22c55e', '#ef4444'], // green for passes, red for fails
                        }],
                    };
                    return (
                        <div key={lv.level} className="progress-card">
                            <div className="progress-card-header">
                                <div
                                    className={`progress-card-icon ${isUnlocked
                                        ? "progress-card-icon unlocked"
                                        : "progress-card-icon locked"
                                        }`}
                                >
                                    {isUnlocked ? <FaLockOpen /> : <FaLock />}
                                </div>
                                <div className="progress-card-meta">
                                    <div className="value">Level {lv.level}</div>
                                </div>
                                <div className="progress-card-stats">
                                    <div>
                                        Last Attempt: <b>{fmtDate(lv.lastAt)}</b>
                                    </div>
                                    <div>
                                        Last Score: <b>{lv.lastScore ?? 0}</b>
                                    </div>
                                </div>
                            </div>

                            <div className="level-card-body">
                                <div className="level-card-chart">
                                    <Doughnut data={pieData} options={pieOptions} />
                                </div>

                                <div className="stat-box">
                                    {[
                                        { label: "Total attempts", value: attempts },
                                        { label: "Passes", value: passes, className: "success" },
                                        { label: "Fails", value: fails, className: "fail" },
                                        {
                                            label: "Pass rate",
                                            value: attempts > 0 ? `${Math.round((passes / attempts) * 100)}%` : "—"
                                        },
                                    ].map((stat, idx) => (
                                        <div className="stat-box-row" key={idx}>
                                            <span className={stat.className || ""}>{stat.label}</span>
                                            <strong>{stat.value}</strong>
                                        </div>
                                    ))}
                                    <div className="stat-box-hint">
                                        (Pass threshold: {PASS_THRESHOLD}/10)
                                    </div>
                                </div>
                            </div>

                            <div className="keywords">
                                <h3>Focus points</h3>
                                {lv.keywordStats?.length ? (
                                    lv.keywordStats.map((k) => {
                                        const attemptsK = k.attempts || 0;
                                        const missRate =
                                            typeof k.miss_rate === "number"
                                                ? k.miss_rate
                                                : (k.misses || 0) / Math.max(1, attemptsK);
                                        const proficiency = 1 - Math.max(0, Math.min(1, missRate));
                                        const widthPct = `${Math.max(
                                            0,
                                            Math.min(100, Math.round(proficiency * 100))
                                        )}%`;

                                        return (
                                            <div key={k.keyword} className="keyword">
                                                <div className="keyword-row">
                                                    <span>{k.keyword}</span>
                                                    <span className="keyword-meta">
                                                        <span>{attemptsK} tries • {Math.round(proficiency * 100)}%</span>
                                                        <FaCheckCircle />

                                                    </span>
                                                </div>
                                                <div className="keyword-track">
                                                    <div
                                                        className={barClass(proficiency)}
                                                        style={{ width: widthPct }}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })
                                ) : (
                                    <p className="empty"> No keyword attempts yet.</p>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default Progress;
