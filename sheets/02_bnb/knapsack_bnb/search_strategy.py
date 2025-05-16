"""
Search Strategy Module

The search strategy determines which node you explore next in the BnB tree to
improve your lower or upper bound as quickly as possible. Provide a `priority`
function that ranks open nodes; this class manages a priority queue accordingly.

You can implement breadth-first, depth-first, best-first, or any custom order
by supplying different priority functions.
"""

import queue
from typing import Callable, Iterator, Tuple, Any

from .bnb_nodes import BnBNode


class SearchStrategy:
    """
    Manage open BnB nodes in a priority queue.

    Args:
        priority: callable mapping a BnBNode to a comparable key.
                  Lower keys are explored first.
    """

    def __init__(self, priority: Callable[[BnBNode], Any]) -> None:
        self._priority = priority
        # use a counter to break ties by insertion order
        self._queue: queue.PriorityQueue[Tuple[Any, int, BnBNode]] = (
            queue.PriorityQueue()
        )
        self._counter = 0

    def enqueue(self, node: BnBNode) -> None:
        """
        Add `node` to the open-set with its priority key.
        Ties are broken by the order nodes were added.
        """
        self._queue.put((self._priority(node), self._counter, node))
        self._counter += 1

    def has_next(self) -> bool:
        """
        Return True if there are still nodes to explore.
        """
        return not self._queue.empty()

    def next(self) -> BnBNode:
        """
        Remove and return the next node by priority.

        Raises:
            ValueError: if no nodes remain.
        """
        if not self.has_next():
            raise ValueError("No more nodes to explore.")
        return self._queue.get()[2]

    def __len__(self) -> int:
        """
        Number of nodes currently in the queue.
        """
        return self._queue.qsize()

    def nodes_in_queue(self) -> Iterator[BnBNode]:
        """
        Iterator over nodes still in the queue (no removal).
        """
        return (item[2] for item in self._queue.queue)

    def upper_bound(self) -> float:
        """
        Return the highest upper_bound among queued nodes, or -inf if empty.

        Note: to get the global BnB upper bound, take the max of this
        and your best feasible solution value.
        """
        if not self.has_next():
            return float("-inf")
        return max(
            self.nodes_in_queue(),
            key=lambda n: n.relaxed_solution.upper_bound,
        ).relaxed_solution.upper_bound



"""
def my_search_order(node: BnBNode) -> float:
    # Prioritize nodes with highest upper bound (negated for min-heap), and shallower depth to break ties
    return (-node.relaxed_solution.upper_bound, node.depth)



def my_search_order(node: BnBNode) -> float:
    # Tie-break with depth to prioritize shallow promising nodes
    gap = node.relaxed_solution.upper_bound - node.lower_bound
    return -(node.relaxed_solution.upper_bound - 0.1 * gap)  # encourage narrowing the gap

def my_search_order(node: BnBNode) -> float:
    # Prioritize highest upper bound, break ties with shallow depth
    return (-node.relaxed_solution.upper_bound, node.depth * 0.25)


def my_search_order(node: BnBNode) -> float:
    gap = node.relaxed_solution.upper_bound - node.lower_bound
    return -(node.lower_bound + 0.25 * gap)  # prioritize nodes closer to optimal

""""""
def my_search_order(node: BnBNode) -> float:
    ub = node.relaxed_solution.upper_bound
    return (-ub, node.depth)

"""
def my_search_order(node: BnBNode) -> Tuple[float, int]:
    return (-node.relaxed_solution.upper_bound, node.depth)


