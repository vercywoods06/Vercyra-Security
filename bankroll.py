import random

RTP = 0.97  # Aviator's published return-to-player; the operator's real figure may differ


def analyse(bankroll, stake, cashout, rounds=100, sims=5000, seed=None):
    """Risk summary for flat-betting `stake` and cashing out at `cashout`x every round.

    Win probability at cashout c is RTP / c (a fair crash-game model), so every
    cashout target has the same expected loss: stake * (1 - RTP) per round.
    """
    p_win = min(RTP / cashout, 1.0)
    ev_round = stake * (p_win * (cashout - 1) - (1 - p_win))
    max_losses = int(bankroll // stake)
    rng = random.Random(seed)
    ruined = 0
    final_total = 0.0
    for _ in range(sims):
        b = bankroll
        for _ in range(rounds):
            if b < stake:
                break
            b += stake * (cashout - 1) if rng.random() < p_win else -stake
        ruined += b < stake
        final_total += b
    return {
        "p_win": p_win,
        "ev_round": ev_round,
        "ev_total": ev_round * rounds,
        "losses_to_bust": max_losses,
        "p_streak": (1 - p_win) ** max_losses,
        "p_ruin": ruined / sims,
        "avg_final": final_total / sims,
        "rounds": rounds,
    }
