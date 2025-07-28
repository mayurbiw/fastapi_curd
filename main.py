import time

from collections import defaultdict
from fastapi import FastAPI, HTTPException, Request
from models import ItemCreate, ItemResponse
from servive import MAX_REQUEST_PER_IP_PER_MIN

app = FastAPI()

items = []
ids = []

request_times = defaultdict(list)


def check_rate_limit(request: Request):
    client_ip = request.client.host
    current_time = time.time()
    request_times[client_ip] = [
        req_time
        for req_time in request_times[client_ip]
        if current_time - req_time < 60
    ]

    if len(request_times[client_ip]) >= MAX_REQUEST_PER_IP_PER_MIN:
        raise HTTPException(
            status_code=429, detail="Rate limit exceeded: 5 requests per 60 seconds"
        )

    request_times[client_ip].append(current_time)


@app.get("/items/{target_id}", response_model=ItemResponse)
async def get_item(request: Request, target_id):
    check_rate_limit(request)
    items_filtered = list(filter(lambda x: x["id"] == int(target_id), items))
    if items_filtered:
        return ItemResponse(**items_filtered[0])

    # item with id not found.
    raise HTTPException(status_code=404, detail=f"Item with ID {target_id} not found")


@app.post("/items", response_model=ItemResponse)
async def create_item(request: Request, itemCreate: ItemCreate):
    check_rate_limit(request)
    item = itemCreate.model_dump()
    target_id = 0
    if ids:
        target_id = int(ids[-1]) + 1
    item["id"] = int(target_id) + 1
    item["description"] = item.get("description", "")
    items.append(item)
    ids.append(target_id)
    return ItemResponse(**item)


@app.put("/items/{target_id}", response_model=ItemResponse)
async def update_item(request: Request, target_id: int, itemCreate: ItemCreate):
    check_rate_limit(request)
    items_filtered = list(filter(lambda x: x["id"] == int(target_id), items))
    if items_filtered:
        item = items_filtered[0]
        item["name"] = itemCreate.name
        item["description"] = itemCreate.description
        item["price"] = itemCreate.price
        return ItemResponse(**item)

    raise HTTPException(status_code=404, detail=f"Item with ID {target_id} not found")


@app.delete("/items/{target_id}")
async def delete_item(request: Request, target_id: int):
    check_rate_limit(request)
    global items
    new_items = [item for item in items if item["id"] != target_id]
    items = new_items
    return {"msg": f"Item with id {target_id} deleted"}
