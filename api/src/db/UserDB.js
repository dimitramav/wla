import User from '../models/User.js';
import { hashPassword, comparePassword } from '../lib/auth.js';

export class UserDB {
    static async createUser({ email, username, password }) {
        const exists = await User.findOne({ email });
        if (exists) {
            throw new Error('EMAIL_TAKEN');
        }

        const passwordHash = await hashPassword(password);
        const user = await User.create({
            email,
            username,
            passwordHash,
            seed: ''
        });

        return {
            id: user._id,
            email: user.email,
            username: user.username
        };
    }

    static async authenticateUser({ email, password }) {
        const user = await User.findOne({ email });
        if (!user) {
            throw new Error('INVALID_CREDENTIALS');
        }

        const isValid = await comparePassword(password, user.passwordHash);
        if (!isValid) {
            throw new Error('INVALID_CREDENTIALS');
        }

        return {
            id: user._id,
            email: user.email,
            username: user.username
        };
    }

    static async findUserByEmail(email) {
        return User.findOne({ email });
    }
}