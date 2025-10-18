/*
 *
 * Routes for user authentication and session management.
 *
 * Exposes:
 * - POST /signup : create a new user, set an auth cookie
 * - POST /login  : authenticate and set auth cookie
 * - POST /logout : clear the auth cookie
 * - GET  /me     : validate auth cookie and return user payload
 *
 * Implementation notes:
 * - The auth cookie name is `wla`.
 */

import { Router } from 'express';
import { signJwt, verifyJwt } from '../lib/auth.js';
import { UserDB } from '../db/UserDB.js';


const router = Router();


function setAuthCookie(res, token) {
    // Set a secure HTTP-only cookie that stores the JWT used for session auth.
    res.cookie('wla', token, {
        httpOnly: true,
        sameSite: 'lax',
        secure: false, // set true if you serve over HTTPS
        maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
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

        // on success, set the auth cookie and return created user
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
    // Clear the auth cookie to log the user out
    res.clearCookie('wla', { path: '/' });
    res.status(204).end();
});

router.get('/me', async (req, res) => {
    // Validate the auth cookie and return the decoded payload if valid.
    const token = req.cookies?.wla;
    if (!token) return res.status(401).json({ error: { code: 'UNAUTHORIZED' } });

    const payload = verifyJwt(token);
    if (!payload) return res.status(401).json({ error: { code: 'UNAUTHORIZED' } });

    // payload typically contains: { id, email, username }
    res.json({ ok: true, user: { id: payload.id, email: payload.email, username: payload.username } });
});

export default router;
