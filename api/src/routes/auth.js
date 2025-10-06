import { Router } from 'express';
import User from '../models/User.js';
import { connectDB } from '../lib/db.js';
import { hashPassword, comparePassword, signJwt, verifyJwt } from '../lib/auth.js';

const router = Router();

function setAuthCookie(res, token) {
    res.cookie('wla', token, {
        httpOnly: true,
        sameSite: 'lax',
        secure: false, //set true if you serve over HTTPS
        maxAge: 7 * 24 * 60 * 60 * 1000,
        path: '/',
    });
}

router.post('/signup', async (req, res) => {
    await connectDB();
    const { email, password, username } = req.body || {};
    if (!email || !password || !username) {
        return res.status(400).json({ error: { code: 'BAD_REQUEST', message: 'email, password, username required' } });
    }
    const exists = await User.findOne({ email });
    if (exists) return res.status(409).json({ error: { code: 'EMAIL_TAKEN' } });

    const passwordHash = await hashPassword(password);
    const user = await User.create({ email, username, passwordHash, seed: '' });
    const token = signJwt({ id: user._id.toString(), email: user.email, username: user.username });

    setAuthCookie(res, token);
    res.json({ ok: true, user: { id: user._id, email: user.email, username: user.username } });
});

router.post('/login', async (req, res) => {
    await connectDB();
    const { email, password } = req.body || {};
    if (!email || !password) return res.status(400).json({ error: { code: 'BAD_REQUEST' } });

    const user = await User.findOne({ email });
    if (!user) return res.status(401).json({ error: { code: 'INVALID_CREDENTIALS' } });

    const ok = await comparePassword(password, user.passwordHash);
    if (!ok) return res.status(401).json({ error: { code: 'INVALID_CREDENTIALS' } });

    const token = signJwt({ id: user._id.toString(), email: user.email, username: user.username });
    setAuthCookie(res, token);
    res.json({ ok: true, user: { id: user._id, email: user.email, name: user.username } });
});

router.post('/logout', (req, res) => {
    res.clearCookie('wla', { path: '/' });
    res.status(204).end();
});

router.get('/me', async (req, res) => {
    //just validate cookie; if valid return payload
    const token = req.cookies?.wla;
    if (!token) return res.status(401).json({ error: { code: 'UNAUTHORIZED' } });
    const payload = verifyJwt(token);
    if (!payload) return res.status(401).json({ error: { code: 'UNAUTHORIZED' } });
    // payload: { id, email, name }
    res.json({ ok: true, user: { id: payload.id, email: payload.email, name: payload.name } });
});

export default router;
