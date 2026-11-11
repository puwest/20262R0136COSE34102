import math
import random

def evaluate(legend, gain, target_congestion, n_trial=50, rounds=1000):
    initial = [13333, 14667, 16000, 17333, 18677, 20000]
    p = len(initial)
    s = sum(initial)
    total_remaining = 0

    for _ in range(n_trial):
        score = [0] * p
        last_bid = [0] * p
        last_loss = [0] * p
        last_penalty = [0] * p
        window = [legend * initial[n] / s * 100 for n in range(p)]

        for _ in range(rounds):
            bandwidth = round(random.gauss(100, 5.17))
            
            for n in range(p):
                if last_bid[n] > 0:
                    congested = int(last_loss[n] > 0 or last_penalty[n] > 0)
                    step = gain * (target_congestion - congested)
                    damage = (last_loss[n] + last_penalty[n]) / last_bid[n]
                    extra_backoff = min(0.08, 0.10 * max(0.0, damage - 0.35))
                    window[n] = max(0.001, window[n] * math.exp(step - extra_backoff))

                amount = max(0.0, window[n])
                lower = math.floor(amount)
                bid = int(lower + int(random.random() < amount - lower))
                last_bid[n] = bid

            tot_bid = sum(last_bid)
            if tot_bid <= bandwidth:
                for n in range(p):
                    score[n] += last_bid[n]
                    last_loss[n] = 0
                    last_penalty[n] = 0
            else:
                for n in range(p):
                    last_loss[n] = last_bid[n] - int(last_bid[n] * bandwidth / tot_bid)
                
                tot_loss = sum(last_loss)
                for n in range(p):
                    last_penalty[n] = round(tot_loss * 1.5 * last_bid[n] / tot_bid)
                    score[n] += last_bid[n] - last_loss[n] - last_penalty[n]

        total_remaining += (s - sum(score))

    return total_remaining / n_trial

import optuna

# Optuna 출력을 최소화
optuna.logging.set_verbosity(optuna.logging.WARNING)

def objective(trial):
    # 탐색 범위 지정
    lg = trial.suggest_float("legend", 0.80, 1.05)
    gn = trial.suggest_float("gain", 0.001, 0.02, log=True)
    tc = trial.suggest_float("target_congestion", 0.10, 0.35)
    
    # 30회 시행 후 평균 remaining 반환
    return evaluate(lg, gn, tc, n_trial=50)

# 최저 점수(remaining)를 찾는 시도 100회 실행
study = optuna.create_study(direction="minimize")
study.optimize(objective, n_trials=100)

print("--- Optuna 최적화 결과 ---")
print(f"Best Value (remaining): {study.best_value:.2f}")
print("Best Params:", study.best_params)
