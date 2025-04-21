import asyncio

def sqrootsserver(coeffs: str) -> str:
    try:
        a, b, c = map(float, coeffs.split())
        test = b / a

        d = b ** 2 - 4 * a * c
        if d < 0:
            return "\n"
        if d == 0:
            return str(-b / (2 * a)) + "\n"

        d = d ** 0.5

        return str((-b - d) / (2 * a)) + ' ' + str((-b + d) / (2 * a)) + '\n'
    except Exception:
        return "Incorrect input.\n"

async def echo(reader, writer):
    while data := await reader.readline():
        writer.write(sqrootsserver(data.decode()).encode())

    writer.close()
    await writer.wait_closed()

async def main():
    server = await asyncio.start_server(echo, '0.0.0.0', 1337)
    async with server:
        await server.serve_forever()

def serve():
    asyncio.run(main())