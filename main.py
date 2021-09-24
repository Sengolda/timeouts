import asyncio
import enum
import sys


class _State(enum.Enum): # The current state.
    init = 0
    enter = 1
    timeout = 3
    exit = 4

class Timeout:
    def __init__(
        self, deadline: float, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._state = _State.init
        try:
            task = asyncio.Task.current_task(loop=loop)
        except AttributeError:
            task = asyncio.current_task(loop=loop)
        self._task = task
        self._timeout_handler = None
        self.shift_to(deadline)
    

    async def __aenter__(self):
        if self._state != _State.init:
            raise RuntimeError(f"invalid state: {self._state.value}")
        self._state = _State.enter
        return self
    

    async def __aexit__(
        self,
        exc_type,
        exc_val,
        exc_tb,
    ):
        if exc_type is asyncio.CancelledError and self._state == _State.timeout:
            self._timeout_handler = None
            raise asyncio.TimeoutError

        self._state = _State.exit
        self._reject()
        return None
    

    def shift_to(self, deadline: float):
        if self._state == _State.exit:
            raise RuntimeError("You cannot set new deadline while exiting.")
        if self._state == _State.timeout:
            raise RuntimeError("You cannot set new deadline while it already timed out.")
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
        self._deadline = deadline
        now = self._loop.time()
        if deadline <= now:
            self._timeout_handler = None
            if self._state == _State.init:
                raise asyncio.TimeoutError
            else:
                raise asyncio.CancelledError
        self._timeout_handler = self._loop.call_at(
            deadline, self._on_timeout, self._task
        )
    

    def _on_timeout(self, task: asyncio.Task):
        if task._fut_waiter and task._fut_waiter.cancelled():
            return
        task.cancel()
        self._state = _State.timeout
    

    def get_state(self):
        return self._state
    

    def _reject(self):
        if self._timeout_handler is not None:
            self._timeout_handler.cancel()
            self._timeout_handler = None
