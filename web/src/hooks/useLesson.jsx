import { useMemo } from 'react';

export function useLesson() {
    const lesson = useMemo(() => 'school_anxiety', []);
    return { lesson };
}