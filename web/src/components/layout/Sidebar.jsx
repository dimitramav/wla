import { useLesson } from '../../hooks/useLesson';

export default function Sidebar() {
    const { lesson } = useLesson();
    return (
        <div className="p-3">
            <div className="text-sm text-gray-500 mb-2">Thematic</div>
            <div className="font-medium">School Anxiety</div>
            <div className="text-xs mt-4 text-gray-500">Lesson slug: {lesson}</div>
            <div className="mt-6 text-sm">Level: <span className="font-semibold">1</span></div>
        </div>
    );
}