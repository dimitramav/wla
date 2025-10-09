import { useMemo } from 'react';

export function useTopic() {
    const topic = useMemo(() => 'school_anxiety', []);
    return { topic };
}