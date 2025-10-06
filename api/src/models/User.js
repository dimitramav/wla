import mongoose from 'mongoose';

const UserSchema = new mongoose.Schema(
    {
        email: { type: String, unique: true, index: true, required: true },
        username: { type: String, required: true },
        passwordHash: { type: String, required: true },
        seed: { type: String, default: '' },
    },
    { timestamps: true }
);

export default mongoose.model('User', UserSchema);
