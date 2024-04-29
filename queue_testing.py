from queue import Queue

q = Queue()

q.put(1)
q.put(2)
q.put(3)

print("the size of our queue: ", q.qsize())

first_in_queue = q.get()

print(first_in_queue)

print("the size of our queue: ", q.qsize())

second_in_queue = q.get()

print(second_in_queue)

print("the size of our queue: ", q.qsize())
