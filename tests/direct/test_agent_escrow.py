def deploy_case(direct_deploy, direct_alice, direct_bob):
    return direct_deploy(
        "contracts/agent_escrow_judge.py",
        "0x" + direct_alice.hex(),
        "0x" + direct_bob.hex(),
        "Build a landing page",
        "The page must load and contain a working contact form",
    )


def test_initial_case(direct_deploy, direct_alice, direct_bob):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    case = contract.get_case()

    assert case["outcome"] == "PENDING"
    assert case["disputed"] == "false"
    assert case["delivery"] == ""


def test_seller_can_submit_delivery(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery(
        "Landing page completed",
        "https://example.com/demo",
    )

    case = contract.get_case()
    assert case["delivery"] == "Landing page completed"
    assert case["seller_evidence"] == "https://example.com/demo"


def test_only_seller_can_submit(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_charlie

    with direct_vm.expect_revert("Only the registered seller"):
        contract.submit_delivery("Completed", "Evidence")


def test_buyer_can_open_dispute(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Landing page completed", "Demo link")

    direct_vm.sender = direct_alice
    contract.dispute_delivery(
        "Contact form does not work",
        "Screenshot showing the error",
    )

    case = contract.get_case()
    assert case["disputed"] == "true"
    assert case["buyer_objection"] == "Contact form does not work"


def test_only_buyer_can_open_dispute(
    direct_vm, direct_deploy, direct_alice, direct_bob, direct_charlie
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Completed", "Demo")

    direct_vm.sender = direct_charlie

    with direct_vm.expect_revert("Only the registered buyer"):
        contract.dispute_delivery("Not acceptable", "Evidence")


def test_seller_cannot_submit_delivery_twice(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("First delivery", "First evidence")

    with direct_vm.expect_revert("Delivery has already been submitted"):
        contract.submit_delivery("Second delivery", "Second evidence")


def test_buyer_cannot_dispute_without_delivery(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_alice

    with direct_vm.expect_revert("Seller has not submitted a delivery"):
        contract.dispute_delivery("Not acceptable", "Evidence")


def test_buyer_cannot_open_dispute_twice(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Completed", "Demo")

    direct_vm.sender = direct_alice
    contract.dispute_delivery("Not acceptable", "Evidence")

    with direct_vm.expect_revert("A dispute has already been opened"):
        contract.dispute_delivery("Another objection", "Another evidence")


def test_seller_cannot_change_delivery_after_dispute(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Original delivery", "Original evidence")

    direct_vm.sender = direct_alice
    contract.dispute_delivery("Not acceptable", "Evidence")

    direct_vm.sender = direct_bob

    with direct_vm.expect_revert("Delivery cannot be changed after a dispute"):
        contract.submit_delivery("Changed delivery", "Changed evidence")


def test_adjudicate_requires_dispute(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    with direct_vm.expect_revert("The buyer has not opened a dispute"):
        contract.adjudicate()


def test_adjudicate_returns_buyer(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Landing page completed", "Broken form demo")

    direct_vm.sender = direct_alice
    contract.dispute_delivery(
        "Contact form does not work",
        "Screenshot showing the error",
    )

    direct_vm.mock_llm(r".*", "BUYER")

    contract.adjudicate()

    case = contract.get_case()
    assert case["outcome"] == "BUYER"


def test_adjudicate_returns_seller(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Landing page completed", "Working demo")

    direct_vm.sender = direct_alice
    contract.dispute_delivery("Page does not meet requirements", "Objection evidence")

    direct_vm.mock_llm(r".*", "SELLER")

    contract.adjudicate()

    assert contract.get_case()["outcome"] == "SELLER"


def test_adjudicate_returns_undetermined(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Landing page completed", "Demo link")

    direct_vm.sender = direct_alice
    contract.dispute_delivery("The result is unclear", "Conflicting evidence")

    direct_vm.mock_llm(r".*", "UNDETERMINED")

    contract.adjudicate()

    assert contract.get_case()["outcome"] == "UNDETERMINED"


def test_adjudicate_cannot_run_twice(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Landing page completed", "Working demo")

    direct_vm.sender = direct_alice
    contract.dispute_delivery("Contact form is broken", "Screenshot evidence")

    direct_vm.mock_llm(r".*", "BUYER")
    contract.adjudicate()

    with direct_vm.expect_revert("This case has already been adjudicated"):
        contract.adjudicate()


def test_adjudicate_rejects_invalid_result(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Landing page completed", "Demo link")

    direct_vm.sender = direct_alice
    contract.dispute_delivery("Contact form is broken", "Screenshot")

    direct_vm.mock_llm(r".*", "INVALID")

    with direct_vm.expect_revert("Invalid adjudication result"):
        contract.adjudicate()

    assert contract.get_case()["outcome"] == "PENDING"


def test_seller_cannot_submit_after_adjudication(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Completed", "Demo")

    direct_vm.sender = direct_alice
    contract.dispute_delivery("Not acceptable", "Evidence")

    direct_vm.mock_llm(r".*", "BUYER")
    contract.adjudicate()

    direct_vm.sender = direct_bob
    with direct_vm.expect_revert("This case is no longer pending"):
        contract.submit_delivery("Changed delivery", "New evidence")


def test_buyer_cannot_dispute_after_adjudication(
    direct_vm, direct_deploy, direct_alice, direct_bob
):
    contract = deploy_case(direct_deploy, direct_alice, direct_bob)

    direct_vm.sender = direct_bob
    contract.submit_delivery("Completed", "Demo")

    direct_vm.sender = direct_alice
    contract.dispute_delivery("Not acceptable", "Evidence")

    direct_vm.mock_llm(r".*", "SELLER")
    contract.adjudicate()

    with direct_vm.expect_revert("This case is no longer pending"):
        contract.dispute_delivery("New objection", "New evidence")
