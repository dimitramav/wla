import { Router } from 'express';
import { signJwt, verifyJwt } from '../lib/auth.js';
import { UserDB } from '../db/UserDB.js';


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
    const { email, password, username } = req.body || {};

    if (!email || !password || !username) {
        return res.status(400).json({
            error: {
                code: 'BAD_REQUEST',
                message: 'email, password, username required'
            }
        });
    }

    try {
        const user = await UserDB.createUser({ email, username, password });
        const token = signJwt({
            id: user.id.toString(),
            email: user.email,
            username: user.username
        });

        setAuthCookie(res, token);
        res.json({ ok: true, user });
    } catch (error) {
        if (error.message === 'EMAIL_TAKEN') {
            return res.status(409).json({ error: { code: 'EMAIL_TAKEN' } });
        }
        throw error;
    }
});

router.post('/login', async (req, res) => {
    const { email, password } = req.body || {};

    if (!email || !password) {
        return res.status(400).json({ error: { code: 'BAD_REQUEST' } });
    }

    try {
        const user = await UserDB.authenticateUser({ email, password });
        const token = signJwt({
            id: user.id.toString(),
            email: user.email,
            username: user.username
        });

        setAuthCookie(res, token);
        res.json({ ok: true, user });
    } catch (error) {
        return res.status(401).json({ error: { code: 'INVALID_CREDENTIALS' } });
    }
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
