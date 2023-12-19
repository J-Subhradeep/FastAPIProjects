from typing import List,Dict,Optional
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
import json
from pydantic import BaseModel
app = FastAPI()




class ConnectionManager:
	#initialize list for websockets connections
	def __init__(self):
		self.active_connections: Dict[str, List[WebSocket]] = {}

	#accept and append the connection to the list
	async def connect(self, websocket: WebSocket,room_id:int):
            if room_id not in self.active_connections:
                self.active_connections[room_id] = []

            await websocket.accept()
            self.active_connections[room_id].append(websocket)
            # self.active_connections.append(websocket)

	#remove the connection from list
	def disconnect(self, websocket: WebSocket,room_id:int):
		del self.active_connections[room_id]

	#send personal message to the connection
	async def send_personal_message(self, message: str, websocket: WebSocket):
		await websocket.send_json(message)
		
	#send message to the list of connections
	async def broadcast(self, message: str, websocket: WebSocket,room_id:int):
            if self.active_connections.get(room_id):
                for connection in self.active_connections[room_id]:
                    if connection != websocket:
                        await connection.send_json(message)
            else:
                self.active_connections[room_id] = []
                self.active_connections[room_id].append(websocket)
                websocket.send_json(message)

# instance for hndling and dealing with the websocket connections
manager = ConnectionManager()

# @app.get("/", response_class=HTMLResponse)
# def read_index(request: Request):
# 	# Render the HTML template
# 	return templates.TemplateResponse("index.html", {"request" : request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket,client_id)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.send_personal_message(data, websocket)
            await manager.broadcast(f"Client says: {data}",websocket,client_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket,client_id)
        # await manager.broadcast(f"Client #{client_id} left the chat",websocket)

class User(BaseModel):
     from_client: str
     to_client: int
     message: str

@app.post("/api")
async def post_endpoint(data: Optional[User]):
        client_id = data.to_client if data.to_client else None
        if client_id and manager.active_connections[client_id]:
             websockets = manager.active_connections[client_id]
             for connection in websockets:
                  await connection.send_json(data.message)
        return {"message":"sent"}