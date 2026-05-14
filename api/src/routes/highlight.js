import { Router } from "express";
import { highlight } from "../ragClient.js";

const router = Router({ mergeParams: true });

router.post("/:topic/highlight", async (req, res) => {
    try {
        const { topic } = req.params;
        const { doc, text } = req.body || {};
        if (!doc || !text) {
            return res.status(400).json({ error: { message: "Missing doc or text" } });
        }
        const data = await highlight({ topic, doc, text });
        return res.json(data);
    } catch (e) {
        console.error("highlight error:", e);
        return res.status(502).json({ error: { message: "Highlight lookup failed" } });
    }
});

export default router;
