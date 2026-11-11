import math
import random

n_trial = 200
rounds = 1000
legend = 0.98225
gain = 0.001121
target_congestion = 0.2149
initial = [16000, 18000, 20000, 22000, 24000]
p = len(initial)
s = sum(initial)
window = [0 for i in range(p)]            #내가 class 쓸줄 모름...
total_score = 0

for j in range(n_trial):
    score = [0 for i in range(p)]
    last_bid = [0 for i in range(p)]
    last_loss = [0 for i in range(p)]
    last_penalty = [0 for i in range(p)]
    for n in range(p):
        window[n] = legend * initial[n] / s * 100

    for i in range(rounds):
        bandwidth = round(random.gauss(100,5.17))
        for n in range(p):
            if last_bid[n] > 0:
                #곱연산
                congested = int(last_loss[n] > 0 or last_penalty[n] > 0)
                # 핵심: +0.06 같은 절대 증가 대신 window에 같은 비율을 곱한다.
                # 같은 혼잡 신호를 받으면 window가 10인 사람과 30인 사람의
                # 약 1:3 비중을 유지하면서 함께 조절할 수 있다.
                step = gain * (target_congestion - congested)
                # 초기 과부하/대역폭 급감 등 큰 피해에는 더 빠르게 물러선다.
                damage = (last_loss[n] + last_penalty[n]) / last_bid[n]
                extra_backoff = min(0.08, 0.10 * max(0.0, damage - 0.35))
                if extra_backoff != 0:
                    print(damage)
                    print(f"{extra_backoff}")
                window[n] = max(0.001, window[n] * math.exp(step - extra_backoff))
            #loss가 있었을 때 할거.
            amount = max(0.0,window[n])
            lower = math.floor(amount)
            bid = int(lower + int(random.random() < amount - lower))
            last_bid[n] = bid
        if sum(last_bid) <= bandwidth:
            for n in range(p):
                score[n] += last_bid[n]
                last_loss[n] = 0
                last_penalty[n] = 0
            print("대역폭보다 낮습니다 ㅅㅅ")
        else:
            for n in range(p):
                last_loss[n] = (last_bid[n] - int(last_bid[n] * bandwidth / sum(last_bid)))
                # print(last_bid[n])
                # print(last_loss[n])
                # print(sum(last_bid))
            for n in range(p):
                last_penalty[n] = round(sum(last_loss) * 1.5 * last_bid[n] / sum(last_bid))
                score[n] += last_bid[n] - last_loss[n] - last_penalty[n]
            print(f"좃댓습니다 ㅜㅜ bandwidth: {bandwidth} 총 bid: {sum(last_bid)} loss: {sum(last_loss)} panelty: {sum(last_penalty)}")
        print(score)
    for i in range(p):
        if initial[i] < score[i]:
            print("이건 무효입니다. 그리고 코드 고쳐야합니다.!!!!!!!!!!!!!!!!!!!!!!!!!")
    # print(f"총 {rounds}라운드 동안 remaining은 {s - sum(score)} 입니다.")
    total_score += s - sum(score)
print(f"remaining 평균: {total_score/n_trial}")