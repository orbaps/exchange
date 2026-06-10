from dataclasses import dataclass
from enum import Enum
from typing import Optional, List

class LeaderState(str, Enum):
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"

@dataclass
class ElectionVoteRequest:
    candidate_id: str
    term: int
    last_log_index: int
    last_log_term: int

@dataclass
class ElectionVoteResponse:
    term: int
    vote_granted: bool

@dataclass
class HeartbeatRequest:
    leader_id: str
    term: int
    commit_index: int

@dataclass
class HeartbeatResponse:
    term: int
    success: bool
    match_index: int

class ConsensusLeaderElection:
    """Handles deterministic leader election state and transitions using monotonic terms and lexicographical tie-breaking."""

    def __init__(self, node_id: str):
        self.node_id: str = node_id
        self.current_term: int = 0
        self.state: LeaderState = LeaderState.FOLLOWER
        self.voted_for: Optional[str] = None
        self.current_leader: Optional[str] = None
        self.last_log_index: int = 0
        self.last_log_term: int = 0
        self.election_count: int = 0

    def start_election(self, active_nodes: List[str]) -> ElectionVoteRequest:
        """Initiate an election term transition."""
        self.state = LeaderState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.current_leader = None
        self.election_count += 1
        return ElectionVoteRequest(
            candidate_id=self.node_id,
            term=self.current_term,
            last_log_index=self.last_log_index,
            last_log_term=self.last_log_term
        )

    def handle_vote_request(self, req: ElectionVoteRequest) -> ElectionVoteResponse:
        """Evaluate a vote request from a candidate node."""
        # Update current term if request term is newer
        if req.term > self.current_term:
            self.current_term = req.term
            self.state = LeaderState.FOLLOWER
            self.voted_for = None
            self.current_leader = None

        log_up_to_date = (
            req.last_log_term > self.last_log_term or
            (req.last_log_term == self.last_log_term and req.last_log_index >= self.last_log_index)
        )
        
        # Lexicographical tie break: candidate_id <= self.node_id
        is_lex_priority = req.candidate_id <= self.node_id
        
        vote_granted = (
            req.term == self.current_term and
            (self.voted_for is None or self.voted_for == req.candidate_id) and
            log_up_to_date and
            is_lex_priority
        )

        if vote_granted:
            self.voted_for = req.candidate_id

        return ElectionVoteResponse(
            term=self.current_term,
            vote_granted=vote_granted
        )

    def handle_heartbeat(self, req: HeartbeatRequest) -> HeartbeatResponse:
        """Process a heartbeat/append entry request from a leader."""
        if req.term > self.current_term:
            self.current_term = req.term
            self.state = LeaderState.FOLLOWER
            self.voted_for = None
            self.current_leader = None

        if req.term >= self.current_term:
            self.state = LeaderState.FOLLOWER
            self.current_leader = req.leader_id
            return HeartbeatResponse(
                term=self.current_term,
                success=True,
                match_index=self.last_log_index
            )
        else:
            return HeartbeatResponse(
                term=self.current_term,
                success=False,
                match_index=self.last_log_index
            )
