import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { JWT_SECRET, JWT_EXPIRES } from './env.js';

export function signJwt(payload) {
    return jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES || '7d' });
}

export function verifyJwt(token) {
    try {
        return jwt.verify(token, JWT_SECRET);
    } catch {
        return null;
    }
}

export async function hashPassword(plain) {
    const salt = await bcrypt.genSalt(10);
    return bcrypt.hash(plain, salt);
}
export async function comparePassword(plain, hash) {
    return bcrypt.compare(plain, hash);
}

export function authRequired(req, res, next) {
    const token = req.cookies?.wla;
    const payload = token ? verifyJwt(token) : null;
    if (!payload) return res.status(401).json({ error: { code: 'UNAUTHORIZED' } });
    req.user = payload;
    next();
}
