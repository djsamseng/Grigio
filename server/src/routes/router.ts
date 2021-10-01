import { Router } from "express";

const router = Router();

router.get("/", (req, resp) => {
    resp.send(`<html>
    <body>
    <div>
        Please go to <a href="http://192.168.1.220:3000">http://192.168.1.220:3000</a>
    </div>
</body>
</html>
    `);
});

export default router;