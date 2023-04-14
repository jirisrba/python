#!/usr/bin/env python3

import asyncio

# A co-routine
async def add(x: int, y: int):
    return x + y


# Create a function to schedule co-routines on the event loop
# then print results and stop the loop
async def get_results():
    result1 = await add(3, 4)
    result2 = await add(5, 5)

    print(result1, result2)  # Prints 7 10


asyncio.run(get_results())
