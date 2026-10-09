import hashlib
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI()

EMAIL = "22f3000320@ds.study.iitm.ac.in".strip().lower()

TOOL = {
    "name": "solve_challenge",
    "description": "Returns the exam answer for the challenge sent in the HTTP headers.",
    "inputSchema": {"type": "object", "properties": {}},
}


def handle(msg: dict, headers):
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    # Notifications (no id) get no JSON reply
    if msg_id is None:
        return None

    def ok(result):
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def err(code, text):
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": text}}

    if method == "initialize":
        return ok({
            "protocolVersion": params.get("protocolVersion", "2025-03-26"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "exam-mcp-server", "version": "1.0.0"},
        })

    if method == "ping":
        return ok({})

    if method == "tools/list":
        return ok({"tools": [TOOL]})

    if method == "tools/call":
        if params.get("name") != "solve_challenge":
            return err(-32602, "Unknown tool")
        challenge = headers.get("x-exam-challenge", "")
        answer = hashlib.sha256(f"{challenge}:{EMAIL}".encode()).hexdigest()[:16]
        return ok({"content": [{"type": "text", "text": answer}]})

    return err(-32601, "Method not found")


@app.post("/")
@app.post("/mcp")
async def mcp(request: Request):
    body = await request.json()
    if isinstance(body, list):
        replies = [r for r in (handle(m, request.headers) for m in body) if r]
        return JSONResponse(replies) if replies else Response(status_code=202)
    reply = handle(body, request.headers)
    if reply is None:
        return Response(status_code=202)
    return JSONResponse(reply)
