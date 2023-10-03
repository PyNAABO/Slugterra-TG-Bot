# DR
import uvicorn
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

import time
from threading import Thread
from Scraper import driver, imgScraper, get_inQueue, get_completed

inQueue, data1 = get_inQueue()
completed, data2 = get_completed()


def restart(driver):
    while len(driver.window_handles) != 1:
        driver.switch_to.window(driver.window_handles[-1])
        driver.close()
    driver.switch_to.window(driver.window_handles[0])
    driver.refresh()
    driver.get("https://www.google.com/")


def complete():
    while True:
        try:
            inQueue, data1 = get_inQueue()
            qs = [item["query"] for item in inQueue]
            time.sleep(5)
            if len(qs) != 0:
                for query in qs:
                    imgScraper(driver, query)
                    inQueue.remove(data1.query == query)
            else:
                continue
        except Exception as e:
            print("ERROR:", e)
            restart(driver)


restart(driver)
t = Thread(target=complete)
t.start()

app = FastAPI()


@app.get("/")
def home():
    return {"msg": "Hello, I'm Alive"}


@app.post("/get")
def add(query: Optional[str] = None):
    if query == None:
        return {"msg": "No query provided!!"}
    else:
        inQueue, data1 = get_inQueue()
        completed, data2 = get_completed()
        if query not in [item["query"] for item in inQueue]:
            if query in [item["query"] for item in completed]:
                completed.remove(data2.query == query)
            inQueue.insert({
                "query": query,
                "status": "pending",
                "quantity": 0,
                "links": []
            })
            print(f"[ ADDED - {query} ]")
            return {"msg": f"query - {query} : ADDED"}
        return {"msg": f"query - {query} : Already exists!!"}


@app.get("/status")
def status(query: Optional[str] = None):
    if query == None:
        return {"msg": "No query provided!!"}
    else:
        inQueue, data1 = get_inQueue()
        completed, data2 = get_completed()

        if query in [item["query"] for item in inQueue]:
            res = inQueue.search(data1.query == query)
            if len(res) != 0:
                return res[0]
        if query in [item["query"] for item in completed]:
            res = completed.search(data2.query == query)
            if len(res) != 0:
                return res[0]
        return {"msg": "query doesn't EXIST!!"}


@app.get("/delete")
def delete(query: Optional[str] = None):
    if query == None:
        return {"msg": "No query provided!!"}
    else:
        inQueue, data1 = get_inQueue()
        completed, data2 = get_completed()
        if query in [item["query"] for item in inQueue]:
            res = inQueue.search(data1.query == query)
            if len(res) != 0:
                inQueue.remove(data1.query == query)
                return {"msg": f"query - {query} : Deleted"}
        if query in [item["query"] for item in completed]:
            res = completed.search(data2.query == query)
            if len(res) != 0:
                completed.remove(data2.query == query)
                return {"msg": f"query - {query} : Deleted"}
        return {"msg": "query doesn't EXIST!!"}


@app.get("/history")
def history():
    res = {"history": []}
    inQueue, data1 = get_inQueue()
    completed, data2 = get_completed()
    queue = [f"{item['query']} ({item['quantity']})" for item in inQueue]
    complete = [f"{item['query']} ({item['quantity']})" for item in completed]
    res["history"].extend(queue)
    res["history"].extend(complete)
    return res


@app.get("/clear_history")
def clear_history():
    inQueue, data1 = get_inQueue()
    completed, data2 = get_completed()
    inQueue.truncate()
    completed.truncate()
    return RedirectResponse("/history", status_code=303)


uvicorn.run(app, host="0.0.0.0", port=3291)
