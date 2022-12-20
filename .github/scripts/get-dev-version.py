from datetime import datetime

time = datetime.now()
version = time.strftime("%Y%m%d%H%M%S")
print(f"dev{version}")
