import hashlib
m = hashlib.sha256()
m.update(b"O macaco faz suas macaquices por puro divertimento")
print(m.hexdigest())