"""Saga orchestration: a long transaction split into local steps. Each step has a forward
action and a compensating action. If a step fails, already-completed steps are compensated
in reverse order."""


class SagaStep:
    def __init__(self, name, forward, compensate):
        self.name = name
        self.forward = forward        # fn(ctx) -> None (may raise)
        self.compensate = compensate  # fn(ctx) -> None


class Saga:
    def __init__(self, name):
        self.name = name
        self.steps = []

    def add(self, step: SagaStep):
        self.steps.append(step)
        return self

    def execute(self, ctx=None):
        ctx = ctx or {}
        executed = []
        for step in self.steps:
            try:
                step.forward(ctx)
                executed.append(step)
            except Exception as e:
                ctx["error"] = str(e)
                ctx["failed_at"] = step.name
                # reverse-compensate already executed steps
                for done in reversed(executed):
                    try:
                        done.compensate(ctx)
                        ctx.setdefault("compensated", []).append(done.name)
                    except Exception as ce:
                        ctx.setdefault("compensate_errors", []).append(f"{done.name}: {ce}")
                ctx["status"] = "compensated"
                return ctx
        ctx["status"] = "committed"
        return ctx
