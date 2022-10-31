import requests
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis_om import get_redis_connection, HashModel
from starlette.requests import Request
from fastapi.background import BackgroundTasks
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:3001'],
    allow_methods=['*'],
    allow_headers=['*']
)
# This should be a different database
redis = get_redis_connection(
    host="redis-10343.c90.us-east-1-3.ec2.cloud.redislabs.com",
    port=10343,
    password="jVpQZ2HxAgYO9KYlfUmM0FfDKyCPY8em",
    decode_responses=True
)


class Order(HashModel):
    product_id: str
    price: float
    fee: float
    total_amount: float
    quantity: int
    status: str

    class Meta:
        database = redis


@app.get("/orders/{pk}")
def get(pk: str):
    return Order.get(pk)


@app.post('/orders')
async def create(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()

    req = requests.get('http://127.0.0.1:8000/products/%s' % body['id'])
    product = req.json()
    order = Order(
        product_id=body['id'],
        price=product['price'],
        fee=0.2 * product['price'],
        total_amount=1.2 * product['price'],
        quantity=body['quantity'],
        status='pending',
    )
    order.save()
    background_tasks.add_task(order_complete, order)

    return order


def order_complete(order: Order):
    time.sleep(5)
    order.status = 'completed'
    order.save()
    redis.xadd('order_completed', order.dict(), '*')
