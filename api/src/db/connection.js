import mongoose from 'mongoose';
import { MONGO_URL } from '../lib/env.js';

let isConnected = false;

export async function connectDB() {
    if (isConnected) return;
    await mongoose.connect(MONGO_URL, {
        autoIndex: true,
    });
    isConnected = true;
    console.log('[mongo] connected:', MONGO_URL);
}
