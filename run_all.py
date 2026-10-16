"""Demo: order saga - create order, charge balance, deduct stock.
If stock deduction fails, compensate: refund balance + cancel order."""
from framework.saga import Saga, SagaStep


def main():
    # shared state context
    def new_ctx(order_id, balance, stock, fail_stock=False):
        return {
            "order_id": order_id, "balance": balance, "stock": stock,
            "fail_stock": fail_stock,
        }

    def create_order(ctx):
        ctx["order_status"] = "CREATED"
        print(f"  [step] create order {ctx['order_id']}")
    def cancel_order(ctx):
        ctx["order_status"] = "CANCELLED"
        print(f"  [compensate] cancel order {ctx['order_id']}")

    def charge_balance(ctx):
        if ctx["balance"] < 100:
            raise ValueError("insufficient balance")
        ctx["balance"] -= 100
        print(f"  [step] charge balance, remaining {ctx['balance']}")
    def refund_balance(ctx):
        ctx["balance"] += 100
        print(f"  [compensate] refund balance, back to {ctx['balance']}")

    def deduct_stock(ctx):
        if ctx["fail_stock"] or ctx["stock"] <= 0:
            raise RuntimeError("out of stock")
        ctx["stock"] -= 1
        print(f"  [step] deduct stock, remaining {ctx['stock']}")
    def restore_stock(ctx):
        ctx["stock"] += 1
        print(f"  [compensate] restore stock, back to {ctx['stock']}")

    saga = Saga("order-saga")
    saga.add(SagaStep("create_order", create_order, cancel_order))
    saga.add(SagaStep("charge_balance", charge_balance, refund_balance))
    saga.add(SagaStep("deduct_stock", deduct_stock, restore_stock))

    print("--- Case 1: all steps succeed ---")
    ctx = saga.execute(new_ctx("o_1", balance=200, stock=5))
    print(f"  result: status={ctx['status']}, order={ctx['order_status']}, balance={ctx['balance']}, stock={ctx['stock']}")

    print("\n--- Case 2: stock step fails, reverse compensation runs ---")
    ctx = saga.execute(new_ctx("o_2", balance=200, stock=0, fail_stock=True))
    print(f"  result: status={ctx['status']}, failed_at={ctx['failed_at']}")
    print(f"  compensated: {ctx.get('compensated')}")
    print(f"  final: order={ctx['order_status']}, balance={ctx['balance']}, stock={ctx['stock']}")

    print("\n--- Case 3: balance step fails (insufficient), only order cancelled ---")
    ctx = saga.execute(new_ctx("o_3", balance=50, stock=5))
    print(f"  result: status={ctx['status']}, failed_at={ctx['failed_at']}")
    print(f"  compensated: {ctx.get('compensated')}")
    print(f"  final: order={ctx['order_status']}, balance={ctx['balance']}, stock={ctx['stock']}")

    print("\n== all cases done ==")


if __name__ == "__main__":
    main()
