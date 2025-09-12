from redis import Redis
from rq import Queue, SimpleWorker, Connection

if __name__ == "__main__":
    conn = Redis.from_url("redis://localhost:6379/0", decode_responses=True)
    with Connection(conn):
        w = SimpleWorker([Queue("notes_summarize")])
        w.work(with_scheduler=False)
