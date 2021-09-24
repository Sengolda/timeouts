# timeouts
A way of managing long running tasks.


## use now!
`git clone https://github.com/Sengolda/timeouts`

## Make sure the main.py is in the same directory
```py
from main import Timeout

import asyncio


loop = asyncio.get_event_loop()

async def long_running_task():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            canceled_raised = True
            print(canceled_raised)

async def main():
    async with Timeout(3.0, loop=loop): # If the function executes within 3 seconds, nothing will happen and function will run as normal, if not. it will raise asyncio.CancelledError
    
        await long_running_task()


loop.run_until_complete(main())
```
