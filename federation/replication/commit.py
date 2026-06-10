from typing import Any
from federation.consensus.leader import LeaderState

def process_majority_commit(replica: Any) -> bool:
    """
    Leader-side majority commit coordinator.
    Finds N > commit_index such that a majority of replicas have match_index >= N, 
    verifies N belongs to current leader term, commits in log, and applies to state machine.
    Uses membership_config to support Joint Consensus quorum rules.
    """
    if replica.leader_election.state != LeaderState.LEADER:
        return False

    log = replica.consensus_log
    current_term = replica.leader_election.current_term
    advanced = False

    # Check N descending from latest log entry index down to commit_index + 1
    for N in range(len(log.entries), replica.commit_index, -1):
        entry = log.entries[N - 1]
        if entry is None:
            continue

        # Commit Safety: Only commit logs from the current term directly
        if entry.term != current_term:
            continue

        # Compile list of nodes that have acknowledged/replicated up to index N
        replicated_nodes = [replica.node_id]
        for peer_id, match_idx in replica.match_index.items():
            if match_idx >= N:
                replicated_nodes.append(peer_id)

        # Quorum validation including joint consensus checks
        if replica.membership_config.calculate_quorum_reached(replicated_nodes):
            replica.commit_index = N
            log.commit(N)

            # Apply committed logs to state machine
            for i in range(replica.last_applied + 1, N + 1):
                committed_entry = log.entries[i - 1]
                if committed_entry and hasattr(replica, "apply_command"):
                    replica.apply_command(committed_entry.command)
                replica.last_applied = i

            advanced = True
            break

    return advanced
