# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class AgentEscrowJudge(gl.Contract):
    buyer: Address
    seller: Address
    task: str
    acceptance_criteria: str
    delivery: str
    seller_evidence: str
    buyer_objection: str
    buyer_evidence: str
    outcome: str
    reasoning: str
    disputed: bool

    def __init__(
        self,
        buyer: str,
        seller: str,
        task: str,
        acceptance_criteria: str,
    ) -> None:
        self.buyer = Address(buyer)
        self.seller = Address(seller)
        self.task = task
        self.acceptance_criteria = acceptance_criteria
        self.delivery = ""
        self.seller_evidence = ""
        self.buyer_objection = ""
        self.buyer_evidence = ""
        self.outcome = "PENDING"
        self.reasoning = ""
        self.disputed = False

    @gl.public.view
    def get_case(self) -> dict[str, str]:
        return {
            "buyer": self.buyer.as_hex,
            "seller": self.seller.as_hex,
            "task": self.task,
            "acceptance_criteria": self.acceptance_criteria,
            "delivery": self.delivery,
            "seller_evidence": self.seller_evidence,
            "buyer_objection": self.buyer_objection,
            "buyer_evidence": self.buyer_evidence,
            "outcome": self.outcome,
            "reasoning": self.reasoning,
            "disputed": "true" if self.disputed else "false",
        }

    @gl.public.write
    def submit_delivery(self, delivery: str, evidence: str) -> None:
        if gl.message.sender_address != self.seller:
            raise gl.vm.UserError("Only the registered seller can submit delivery")
        if self.outcome != "PENDING":
            raise gl.vm.UserError("This case is no longer pending")
        if self.disputed:
            raise gl.vm.UserError("Delivery cannot be changed after a dispute")
        if self.delivery != "":
            raise gl.vm.UserError("Delivery has already been submitted")
        if len(delivery.strip()) == 0 or len(evidence.strip()) == 0:
            raise gl.vm.UserError("Delivery and evidence are required")

        self.delivery = delivery
        self.seller_evidence = evidence

    @gl.public.write
    def dispute_delivery(self, objection: str, evidence: str) -> None:
        if gl.message.sender_address != self.buyer:
            raise gl.vm.UserError("Only the registered buyer can dispute delivery")
        if self.outcome != "PENDING":
            raise gl.vm.UserError("This case is no longer pending")
        if len(self.delivery) == 0:
            raise gl.vm.UserError("Seller has not submitted a delivery")
        if self.disputed:
            raise gl.vm.UserError("A dispute has already been opened")
        if len(objection.strip()) == 0 or len(evidence.strip()) == 0:
            raise gl.vm.UserError("Objection and evidence are required")

        self.buyer_objection = objection
        self.buyer_evidence = evidence
        self.disputed = True

    @gl.public.write
    def adjudicate(self) -> None:
        if self.outcome != "PENDING":
            raise gl.vm.UserError("This case has already been adjudicated")
        if not self.disputed:
            raise gl.vm.UserError("The buyer has not opened a dispute")

        # Copy all persistent values into deterministic local strings before
        # entering the non-deterministic equivalence-principle operation.
        task = self.task
        criteria = self.acceptance_criteria
        delivery = self.delivery
        seller_evidence = self.seller_evidence
        objection = self.buyer_objection
        buyer_evidence = self.buyer_evidence

        def evaluate_case() -> str:
            prompt = f"""
You are an impartial adjudicator for a small service-delivery dispute.

Evaluate only the information supplied below. Do not assume facts that are
not present. The buyer and seller agreed to the task and acceptance criteria
before work began.

TASK:
{task}

ACCEPTANCE CRITERIA:
{criteria}

SELLER DELIVERY DESCRIPTION:
{delivery}

SELLER EVIDENCE:
{seller_evidence}

BUYER OBJECTION:
{objection}

BUYER EVIDENCE:
{buyer_evidence}

Return exactly one label and nothing else:
BUYER
SELLER
or UNDETERMINED

Decision rules:
- SELLER: the delivery is supported by evidence and materially satisfies
  the agreed acceptance criteria.
- BUYER: the evidence shows a material failure to satisfy the criteria.
- UNDETERMINED: the evidence is missing, contradictory, or insufficient.
Do not decide based on sympathy, writing style, or claims unsupported by evidence.
"""
            return gl.nondet.exec_prompt(prompt)

        result = gl.eq_principle.prompt_comparative(
            evaluate_case,
            principle=(
                'The returned label must match exactly. It must be BUYER, SELLER, or '
                'UNDETERMINED. Judge the evidence against the agreed criteria. '
                'If evidence is insufficient or contradictory, choose UNDETERMINED.'
            ),
        )

        # Reject any result outside the three permitted outcomes.
        if result not in ("BUYER", "SELLER", "UNDETERMINED"):
            raise gl.vm.UserError("Invalid adjudication result")

        self.outcome = result
        self.reasoning = "Consensus outcome recorded. The detailed evidence remains available in get_case()."
