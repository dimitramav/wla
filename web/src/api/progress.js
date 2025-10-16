// web/src/api/progress.js
import { apiPost } from "./client";

export async function getProgress(topic, userId) {
    return apiPost(`/api/${topic}/progress`, { userId });
}
