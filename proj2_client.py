#!/usr/bin/env python3
"""Proj2 student skeleton: one program, one student account.

    python -m pip install requests
    python proj2_client.py --student-id YOUR_STUDENT_ID
    python proj2_client.py --student-id YOUR_STUDENT_ID --week 2

Week 1 is the default. Week 2 opens on 23 October 2026, 00:00 KST.
To test both networks, run the same file in two terminals, one per week.

Edit only the Algorithm class. Each teammate runs their own copy on their own
computer, and teammates may use different algorithms. All teammates must keep
running their programs until the 1,000-round attempt finishes.

For each round, the client calls choose_bid(observation), submits your bid,
waits for all teammates, then calls on_result(result) with your feedback.
The same Algorithm object is reused: store values on self to remember them
between rounds. Login, requests, waiting and retries are handled for you.
"""
import argparse
import time
import random

import requests


# ---------- Your work: edit the methods in this class ----------
class Algorithm:
    def __init__(self):
        self.initial = 0
        self.prop = 0.0                 #아마 안쓸듯?
        self.window = 0.0
        self.bound = 0                  #현재 클라이언트가 보낼 수 있는 최대 bound. 갑자기 확 깎이면 week2로 간주, 조금 늘어나면 다른 클라이언트가 일을 다해서 좀 여유가 생겼다고 생각할 수 있음.
        self.bound_decision_row = 6     #얼마나 loss 0이 유지되었을 때 bound를 늘릴 것인가
        self.decrease = 0.6
        self.last_bid_queue = [0 for i in range(10)]        #append로 마지막에 삽입 + pop(0)으로 가장 오래된거 pop. [older...newer] 일단 10줄로 생각.
        self.last_delivery_queue = [0 for i in range(10)]   #append로 마지막에 삽입 + pop(0)으로 가장 오래된거 pop. [older...newer] 일단 10줄로 생각.
        self.last_loss_queue = [0 for i in range(10)]       #append로 마지막에 삽입 + pop(0)으로 가장 오래된거 pop. [older...newer] 일단 10줄로 생각.
        self.last_panelty_queue = [0 for i in range(10)]       #append로 마지막에 삽입 + pop(0)으로 가장 오래된거 pop. [older...newer] 일단 10줄로 생각.
        self.total_bid = 0
        self.total_delivered = 0
        self.total_loss = 0
        self.total_panelty = 0
        # Called once when this program prepares or joins an attempt.
        # Initialize values you want to remember between rounds on self
        # (for example, self.last_loss = 0). Local variables do not persist.
        pass

    def choose_bid(self, observation: dict) -> int:
        import math
        import random

        remaining = int(observation["player"]["remaining"])
        round_no = int(observation["round"])
        rounds_left = 1000 - round_no + 1

        # 첫 호출: 동일 코드지만 클라이언트마다 독립적인 난수열 사용
        if not hasattr(self, "_window_rng"):
            self._window_rng = random.Random()  # 고정 seed 사용하지 않기
            self.initial = remaining

            # 6명이 활동할 때 기대 총합 97을 위한 시작 기준값
            self.window = remaining / rounds_left*0.963

            self.increase = 0.0
            self.decrease = 0.0  # 기존 0.6보다 완만하게 감소

        if remaining <= 0 or rounds_left <= 0:
            self.bound = 0
            return 0

        last_bid = self.last_bid_queue[-1]
        last_loss = self.last_loss_queue[-1]
        last_penalty = self.last_panelty_queue[-1]

        # 2. 최근 기록으로 입찰 대비 실제 작업 감소 효율 추정
        # 서버 규칙: after = before - delivered + penalty
        recent_bid = sum(self.last_bid_queue)
        recent_net = (
            sum(self.last_delivery_queue)
            - sum(self.last_panelty_queue)
        )

        if recent_bid > 0:
            net_efficiency = max(
                0.25,
                min(1.0, recent_net / recent_bid)
            )
        else:
            net_efficiency = 1.0

        # 3. 남은 작업을 남은 라운드에 보내기 위한 속도
        # 1.02는 약간의 여유. 완송을 보장하는 값은 아님.
        pace = (
            1.02
            * remaining
            / rounds_left
            / net_efficiency
        )

        amount = max(
            0.0,
            min(float(remaining), self.window, pace)
        )
        if pace<self.window:
            print("페이스도 고려하셈 ㅇㅇ")

        # 기존 on_result() 출력과의 호환용

        # 4. 내부 실수 목표를 실제 정수 입찰로 변환
        lower = math.floor(amount)
        bid = lower + int(
            self._window_rng.random() < amount - lower
        )

        return int(max(0, min(remaining, bid)))

        
        # return min(500, observation["player"]["remaining"])
        # Starter behavior: send 5 each round (or the smaller remaining amount).
        

    def on_result(self, result: dict) -> None:
            """Update your controller after each completed round.

            result is a dictionary describing ONE completed round:
                result["round"]:     round that just completed
                result["bid"]:       amount you requested in that round
                result["delivered"]: amount actually delivered in that round
                result["lost"]:      undelivered part of your bid (bid - delivered)
                result["penalty"]:   extra data added to your remaining workload
                result["before"]:    your remaining data before that round
                result["after"]:     your remaining data after that round

            after = before - delivered + penalty
            Lost data is already in remaining; do not add lost again.
            For example, before=100, bid=5, delivered=3, lost=2, penalty=3
            gives after=100. The delivered value here is for this round only;
            observation["player"]["delivered"] is the cumulative total.`

            Save any feedback you need on self; this method returns nothing.
            Current bandwidth and other students' workloads or bids are not provided.
            """
            self.last_bid_queue.pop(0)
            self.last_bid_queue.append(result["bid"])
            self.last_delivery_queue.pop(0)
            self.last_delivery_queue.append(result["delivered"])
            self.last_loss_queue.pop(0)
            self.last_loss_queue.append(result["lost"])
            self.last_panelty_queue.pop(0)
            self.last_panelty_queue.append(result["penalty"])
            self.total_bid += result["bid"]
            self.total_delivered += result["delivered"]
            self.total_loss += result["lost"]
            self.total_panelty += result["penalty"]
            print(f"{result["round"]} round / bound: {self.bound} / {self.last_bid_queue[-1]} bid / {self.last_delivery_queue[-1]} delivered / {self.last_loss_queue[-1]} loss / {self.last_panelty_queue[-1]} panelty")
            if round(self.last_loss_queue[-1] * 1.5) >  self.last_panelty_queue[-1]:       #round(4.5) == 4?????
                print("[!] panelty 이득")
            if round(self.last_loss_queue[-1] * 1.5) <  self.last_panelty_queue[-1]: 
                print("[!] panelty 손해")
            if result["round"] % 100 == 0:
                print(f"중간점검: {self.total_bid} 할당됨 {self.total_delivered} 전달됨 / {self.total_loss} 손실 / {self.total_panelty} 패널티")

            # Use this feedback to update your controller's state.
            # print(result["round"],"단계 high", self.high_stack,"low:",self.low_stack,"이고 총 bid / loss:",self.total_bid,"/",self.total_loss, "high->low loss:",self.shrink_loss)
            # if result["round"] == 1000:
            #     print("끝. HH:",self.hh,"HL:",self.hl,"LH:",self.lh,"LL:",self.ll,"total_bid:",self.total_bid,"total_panelty:",self.total_loss*1.5,"shrink_panelty:",self.shrink_loss*1.5,"high_panelty:",self.high_loss*1.5,"+low panelty:",self.low_loss_by50*1.5)
            
            pass


# ---------- HTTP client: leave the code below unchanged ----------
# You can implement your controller using only the class above.
# This section logs in, submits one bid per round and retrieves your feedback.
# When remaining reaches 0, it skips choose_bid() and submits 0 automatically;
# keep the program running so your team can complete all 1,000 rounds.
def run(base, student_id, password, poll_seconds=0.1, week=1):
    url = base.rstrip("/")
    if not url.endswith("/proj2"):
        url += "/proj2"
    with requests.Session() as http:
        def request(method, path, **kwargs):
            # Select the week on every request; two programs can use the same ID.
            kwargs["params"] = {**kwargs.get("params", {}), "week": week}
            # If a response is lost, retry the exact same request safely.
            while True:
                try:
                    response = http.request(method, url + path, timeout=(3, 10), **kwargs)
                    if response.status_code >= 500:
                        response.raise_for_status()
                    if not response.ok:
                        raise RuntimeError(response.json().get("error", "Request failed."))
                    return response.json()
                except (requests.Timeout, requests.ConnectionError, requests.HTTPError):
                    print(f"[{student_id}] Connection interrupted; retrying.")
                    time.sleep(1)

        request("POST", "/login", json={"student_id": student_id, "password": password})
        state = request("GET", "/api/me")
        if not state["player"]:
            raise RuntimeError("Your student ID has not been assigned to a team.")
        run_id = request("POST", "/api/ready", json={"run_id": state["run_id"]})["run_id"]
        algorithm, seen_round = Algorithm(), 0
        print(f"[{student_id}] Week {week} connected. Waiting for every teammate's own program.")

        def feedback(result):
            nonlocal seen_round
            # Polling/retries can return the same result; process it only once.
            if result["round"] <= seen_round:
                return
            algorithm.on_result(result)
            seen_round = result["round"]
            print(f"[{student_id}] R{seen_round:04d} bid={result['bid']} delivered={result['delivered']} "
                  f"lost={result['lost']} penalty={result['penalty']} left={result['after']}")

        while True:
            state = request("GET", "/api/me", params={"after_round": seen_round})
            if state["run_id"] != run_id:
                raise RuntimeError("Your team prepared another attempt. Restart your program to join it.")
            for result in state["player"]["history"]:
                # Also recover any missed feedback when joining an active run.
                feedback(result)
            if state["phase"] == "aborted":
                raise RuntimeError(state["abort_reason"] + " Restart all teammates' programs to retry.")
            if state["phase"] == "finished":
                print(f"[{student_id}] Week {week} completed. Team standing:", state.get("standing"))
                return state["grade"]
            player = state["player"]
            amount = player["bid"]  # Resume a request already accepted by the server.
            if amount is None:
                amount = 0 if player["remaining"] == 0 else algorithm.choose_bid(state)
            if type(amount) is not int or not 0 <= amount <= player["remaining"]:
                raise ValueError("choose_bid must return an integer from 0 to your remaining data.")
            receipt = request("POST", "/api/bid", json={"run_id": run_id, "round": state["round"], "bid": amount})
            while receipt["status"] == "waiting":
                # Your bid is accepted; wait until every teammate has submitted.
                time.sleep(poll_seconds)
                receipt = request("GET", "/api/result", params={"run_id": run_id, "round": state["round"]})
            feedback(receipt["result"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--student-id", required=True, help="Your own student ID.")
    parser.add_argument("--base-url", default="http://www.toysugang.korea.ac.kr")
    parser.add_argument("--week", type=int, choices=[1, 2], default=1, help="Network to use (default: 1).")
    args = parser.parse_args()
    try:
        run(args.base_url, args.student_id, "1111", week=args.week)
    except KeyboardInterrupt:
        print("Client stopped. Missing requests for 60 seconds will stop your team's attempt.")
    except (RuntimeError, ValueError, requests.RequestException) as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()