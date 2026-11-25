# GenLayer Agent Escrow

A testnet prototype exploring dispute resolution for AI-agent service agreements.

## Scope

This repository starts with the GenLayer adjudication layer. It records an agreement, accepts evidence from the buyer and seller, and asks GenLayer validators to assess the evidence against the agreement's criteria.

**This first milestone does not custody tokens or release funds.** The Base Sepolia / Alkahest escrow adapter and manual relay are planned follow-up milestones. Do not use real funds.

## Planned architecture

1. Buyer and seller agree on a task description and objective acceptance criteria.
2. The seller submits a delivery description and evidence.
3. The buyer may accept or dispute the delivery with evidence.
4. A GenLayer Intelligent Contract evaluates the submitted material and records one of:
   - `BUYER`: the seller did not satisfy the agreed criteria.
   - `SELLER`: the submitted work satisfies the agreed criteria.
   - `UNDETERMINED`: evidence is insufficient or contradictory.
5. In a later milestone, an operator manually relays the finalized result to a test escrow on Base Sepolia.

## Initial contract

See [contracts/agent_escrow_judge.py](contracts/agent_escrow_judge.py).

The contract is an adjudication record, not an automatic payment system. Its decision is an input to a separately audited escrow adapter.

## Development notes

- Target: GenLayer Bradbury testnet (chain ID 4221, subject to verification against the active network configuration before deployment).
- Escrow target: Base Sepolia (chain ID 84532).
- Token: test token only.
- Relay: manual in the prototype.
- Never submit private keys, seed phrases, or real wallet credentials to this repository.

## Status

Milestone 1: contract source and review.
Milestone 2: local linting and tests.
Milestone 3: Bradbury deployment and test transactions.
Milestone 4: Base Sepolia test escrow integration.
Milestone 5: demo UI and documentation.

## References

- [GenLayer Intelligent Contracts](https://docs.genlayer.com/developers/intelligent-contracts/introduction)
- [GenLayer storage](https://docs.genlayer.com/developers/intelligent-contracts/storage)
- [GenLayer first Intelligent Contract](https://docs.genlayer.com/developers/intelligent-contracts/first-intelligent-contract)
- [Alkahest](https://github.com/arkhai-io/alkahest)
