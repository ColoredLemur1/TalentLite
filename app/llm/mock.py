class MockLLM:
    """Default provider: deterministic, offline and free. Task 5.3 fills in the rubric."""

    provider = "mock"
    model = "mock-keyword-v1"

    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError("MockLLM.complete is implemented in Task 5.3")
