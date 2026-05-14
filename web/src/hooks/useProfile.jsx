import { useState, useEffect } from 'react';
import { getProfile } from '../api/profile';
export const useProfile = (topic, userId) => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [unlockedLevel, setUnlockedLevel] = useState(1);
    const [perLevel, setPerLevel] = useState([]);

    useEffect(() => {
        const fetchProfile = async () => {
            if (!topic || !userId) return;
            setLoading(true);
            setError(null);
            try {
                const data = await getProfile(topic, userId);
                setUnlockedLevel(data.unlockedLevel || 1);
                setPerLevel(Array.isArray(data.perLevel) ? data.perLevel : []);
            } catch (err) {
                console.error("Error loading  profile:", err);
                setError(err.message || "Failed to load profile");
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, [topic, userId]);

    return {
        loading,
        error,
        unlockedLevel,
        perLevel,
    };
};
